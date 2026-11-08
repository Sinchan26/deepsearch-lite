from __future__ import annotations

import asyncio
import secrets
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast

from pydantic import TypeAdapter

from app.config import Settings
from app.domain.models import (
    Attempt,
    Created,
    PublicEvent,
    RunRequest,
    Snapshot,
    Terminal,
    TerminalStatus,
    Usage,
)
from app.policy.budget import Ledger, enforce_ceilings
from app.telemetry import Telemetry

EVENT: TypeAdapter[PublicEvent] = TypeAdapter(cast(Any, PublicEvent))


class NotFound(Exception):
    pass


class CapacityExceeded(Exception):
    pass


class ReplayGap(Exception):
    pass


class ClosedRun(Exception):
    pass


@dataclass
class Run:
    capability: str
    snapshot: Snapshot
    started: float
    ledger: Ledger
    terminal_at: float | None = None
    events: deque[PublicEvent] = field(default_factory=deque)
    event_bytes: int = 0
    subscribers: int = 0
    changed: asyncio.Event = field(default_factory=asyncio.Event)


class Registry:
    """One-process, memory-only state. All event/state transitions share one lock."""

    def __init__(
        self,
        settings: Settings,
        clock: Callable[[], float] = time.monotonic,
        telemetry: Telemetry | None = None,
    ) -> None:
        self.settings = settings
        self.clock = clock
        self.telemetry = telemetry or Telemetry()
        self.runs: dict[str, Run] = {}
        self.lock = asyncio.Lock()

    def _prune(self) -> None:
        terminals = sorted(
            ((key, run) for key, run in self.runs.items() if run.terminal_at is not None),
            key=lambda item: item[1].terminal_at or 0,
        )
        excess = max(0, len(terminals) - self.settings.retained_runs)
        for index, (key, run) in enumerate(terminals):
            if index < excess or self.clock() - (run.terminal_at or 0) >= self.settings.terminal_ttl:
                run.changed.set()
                del self.runs[key]

    def _authorized(self, run_id: str, capability: str) -> Run:
        self._prune()
        run = self.runs.get(run_id)
        expected = run.capability if run else secrets.token_urlsafe(32)
        if not secrets.compare_digest(expected.encode(), capability.encode()) or run is None:
            raise NotFound
        return run

    def _append(self, run: Run, kind: str, payload: dict[str, Any]) -> PublicEvent:
        event = EVENT.validate_python(
            dict(
                schema_version=1,
                run_id=run.snapshot.run_id,
                seq=run.snapshot.seq + 1,
                timestamp=datetime.now(UTC),
                type=kind,
                payload=payload,
            )
        )
        size = len(event.model_dump_json().encode())
        if size > self.settings.event_bytes:
            raise CapacityExceeded("event exceeds ring capacity")
        updates: dict[str, Any] = {"seq": event.seq}
        if event.type == "plan.summary":
            updates["plan"] = event.payload
        elif event.type == "research.action":
            updates["action"] = event.payload
        elif event.type == "evidence.added":
            evidence = list(run.snapshot.evidence)
            if any(e.id == event.payload.id for e in evidence):
                raise ValueError("duplicate evidence id")
            if len(evidence) >= 128 or len({e.source.id for e in evidence} | {event.payload.source.id}) > 64:
                raise CapacityExceeded("evidence capacity")
            updates["evidence"] = [*evidence, event.payload]
        elif event.type == "draft.available":
            if run.snapshot.draft and event.payload.version <= run.snapshot.draft.version:
                raise ValueError("draft version must increase")
            updates["draft"] = event.payload
        elif event.type == "critique.feedback":
            if not run.snapshot.draft or event.payload.version != run.snapshot.draft.version:
                raise ValueError("critique must target current draft")
            updates["critique"] = event.payload
        elif event.type == "budget.updated":
            updates["budget"] = event.payload
        elif event.type == "run.terminal":
            updates.update(status=event.payload.status, terminal=event.payload)
        run.snapshot = run.snapshot.model_copy(update=updates)
        run.events.append(event)
        run.event_bytes += size
        while len(run.events) > self.settings.event_count or run.event_bytes > self.settings.event_bytes:
            removed = run.events.popleft()
            run.event_bytes -= len(removed.model_dump_json().encode())
        run.changed.set()
        run.changed = asyncio.Event()
        return event

    def _finish(self, run: Run, terminal: Terminal) -> bool:
        if run.terminal_at is not None:
            return False
        self._append(run, "run.terminal", terminal.model_dump())
        run.terminal_at = self.clock()
        self.telemetry.terminal(terminal.status, self.clock() - run.started)
        return True

    def _check_active(self, run: Run) -> None:
        if run.terminal_at is not None:
            raise ClosedRun
        if self.clock() - run.started >= run.snapshot.limits.timeout_seconds:
            self._finish(run, Terminal(status="timed_out", reason="deadline"))
            raise ClosedRun

    async def create(self, request: RunRequest) -> Created:
        enforce_ceilings(request.limits, self.settings.ceilings)
        async with self.lock:
            self._prune()
            if sum(r.terminal_at is None for r in self.runs.values()) >= self.settings.active_runs:
                raise CapacityExceeded
            run_id, capability = secrets.token_urlsafe(24), secrets.token_urlsafe(32)
            run = Run(
                capability,
                Snapshot(run_id=run_id, seq=0, status="running", limits=request.limits),
                self.clock(),
                Ledger(request.limits),
            )
            self.runs[run_id] = run
            self._append(run, "run.started", {"limits": request.limits.model_dump()})
            return Created(run_id=run_id, capability=capability)

    async def reserve(self, run_id: str, attempt: Attempt) -> int:
        async with self.lock:
            run = self.runs.get(run_id)
            if run is None:
                raise ClosedRun
            self._check_active(run)
            reservation = await run.ledger.reserve(attempt)
            self._append(run, "budget.updated", run.ledger.snapshot().model_dump())
            return reservation

    async def reconcile(self, run_id: str, reservation: int, usage: Usage | None) -> None:
        async with self.lock:
            run = self.runs.get(run_id)
            if run is None:
                raise ClosedRun
            await run.ledger.reconcile(reservation, usage)
            # Accounting may settle after cancellation, but public terminal state stays immutable.
            if run.terminal_at is None:
                self._append(run, "budget.updated", run.ledger.snapshot().model_dump())

    async def publish(self, run_id: str, kind: str, payload: dict[str, Any]) -> None:
        if kind in {"run.started", "run.terminal"}:
            raise ValueError("lifecycle events belong to registry")
        async with self.lock:
            run = self.runs.get(run_id)
            if run is None:
                raise ClosedRun
            self._check_active(run)
            self._append(run, kind, payload)

    async def finish(self, run_id: str, status: TerminalStatus, reason: str) -> bool:
        terminal = Terminal.model_validate({"status": status, "reason": reason})
        async with self.lock:
            run = self.runs.get(run_id)
            if run is None:
                return False
            if run.terminal_at is None and self.clock() - run.started >= run.snapshot.limits.timeout_seconds:
                terminal = Terminal(status="timed_out", reason="deadline")
            finished = self._finish(run, terminal)
            self._prune()
            return finished

    async def cancel(self, run_id: str, capability: str) -> Snapshot:
        async with self.lock:
            run = self._authorized(run_id, capability)
            if run.terminal_at is None and self.clock() - run.started >= run.snapshot.limits.timeout_seconds:
                self._finish(run, Terminal(status="timed_out", reason="deadline"))
            else:
                self._finish(run, Terminal(status="cancelled", reason="cancelled"))
            return run.snapshot.model_copy(deep=True)

    async def snapshot(self, run_id: str, capability: str) -> Snapshot:
        async with self.lock:
            run = self._authorized(run_id, capability)
            if run.terminal_at is None and self.clock() - run.started >= run.snapshot.limits.timeout_seconds:
                self._finish(run, Terminal(status="timed_out", reason="deadline"))
            return run.snapshot.model_copy(deep=True)

    def _batch(self, run: Run, cursor: int) -> list[PublicEvent]:
        if cursor > run.snapshot.seq or (run.events and cursor < run.events[0].seq - 1):
            raise ReplayGap
        return [e.model_copy(deep=True) for e in run.events if e.seq > cursor]

    async def subscribe(self, run_id: str, capability: str, cursor: int) -> None:
        async with self.lock:
            run = self._authorized(run_id, capability)
            self._batch(run, cursor)
            if run.subscribers >= self.settings.subscribers_per_run:
                raise CapacityExceeded
            run.subscribers += 1

    async def read(
        self, run_id: str, capability: str, cursor: int
    ) -> tuple[list[PublicEvent], bool, asyncio.Event]:
        async with self.lock:
            run = self._authorized(run_id, capability)
            return self._batch(run, cursor), run.terminal_at is not None, run.changed

    async def unsubscribe(self, run_id: str) -> None:
        async with self.lock:
            run = self.runs.get(run_id)
            if run:
                run.subscribers = max(0, run.subscribers - 1)

    async def clear(self) -> None:
        async with self.lock:
            for run in self.runs.values():
                run.changed.set()
            self.runs.clear()
