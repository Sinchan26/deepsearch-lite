from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import Settings
from app.domain.models import Created, RunRequest, Snapshot
from app.domain.ports import Runner
from app.events.stream import encode, heartbeat
from app.orchestration.registry import CapacityExceeded, ClosedRun, NotFound, Registry, ReplayGap
from app.policy.budget import BudgetExceeded


class Runtime:
    def __init__(self, registry: Registry, runner: Runner | None) -> None:
        self.registry = registry
        self.runner = runner
        self.tasks: dict[str, asyncio.Task[None]] = {}

    async def execute(self, run_id: str, timeout: float) -> None:
        try:
            async with asyncio.timeout(timeout):
                if self.runner is None:
                    await self.registry.finish(run_id, "limited", "research_not_implemented")
                else:
                    await self.runner(run_id)
                    # A runner returning without a terminal outcome never implies success.
                    await self.registry.finish(run_id, "failed", "execution_failed")
        except TimeoutError:
            await self.registry.finish(run_id, "timed_out", "deadline")
        except asyncio.CancelledError:
            await self.registry.finish(run_id, "cancelled", "cancelled")
            raise
        except ClosedRun:
            pass
        except Exception:
            await self.registry.finish(run_id, "failed", "execution_failed")

    def start(self, created: Created, timeout: float) -> None:
        task = asyncio.create_task(self.execute(created.run_id, timeout))
        self.tasks[created.run_id] = task
        task.add_done_callback(lambda _: self.tasks.pop(created.run_id, None))

    async def close(self) -> None:
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.registry.clear()


def create_app(
    settings: Settings | None = None, registry: Registry | None = None, runner: Runner | None = None
) -> FastAPI:
    config = settings or Settings()
    store = registry or Registry(config)
    runtime = Runtime(store, runner)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await runtime.close()

    app = FastAPI(title="DeepResearch Lite", lifespan=lifespan)
    app.state.registry = store
    app.state.runtime = runtime
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-Run-Capability", "Last-Event-ID"],
    )

    @app.middleware("http")
    async def prevent_caching(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(*_: object) -> JSONResponse:
        return JSONResponse({"detail": "Invalid request"}, status_code=422)

    @app.exception_handler(NotFound)
    async def not_found(*_: object) -> JSONResponse:
        return JSONResponse({"detail": "Run unavailable"}, status_code=404)

    @app.exception_handler(CapacityExceeded)
    async def capacity(*_: object) -> JSONResponse:
        return JSONResponse({"detail": "Capacity exceeded"}, status_code=429)

    @app.exception_handler(BudgetExceeded)
    async def budget(*_: object) -> JSONResponse:
        return JSONResponse({"detail": "Invalid run limits"}, status_code=422)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "phase": "foundation"}

    @app.post("/api/runs", status_code=202, response_model=Created)
    async def create(request: RunRequest) -> Created:
        created = await store.create(request)
        runtime.start(created, request.limits.timeout_seconds)
        return created

    @app.get("/api/runs/{run_id}", response_model=Snapshot)
    async def snapshot(run_id: str, x_run_capability: str = Header(default="")) -> Snapshot:
        return await store.snapshot(run_id, x_run_capability)

    @app.delete("/api/runs/{run_id}", response_model=Snapshot)
    async def cancel(run_id: str, x_run_capability: str = Header(default="")) -> Snapshot:
        result = await store.cancel(run_id, x_run_capability)
        task = runtime.tasks.get(run_id)
        if task:
            task.cancel()
        return result

    @app.get("/api/runs/{run_id}/events")
    async def events(
        run_id: str, x_run_capability: str = Header(default=""), last_event_id: str = Header(default="0")
    ) -> StreamingResponse:
        if not last_event_id.isascii() or not last_event_id.isdecimal() or len(last_event_id) > 16:
            raise HTTPException(400, "Invalid Last-Event-ID")
        cursor = int(last_event_id)
        try:
            await store.subscribe(run_id, x_run_capability, cursor)
        except ReplayGap:
            raise HTTPException(409, "Replay unavailable; fetch snapshot") from None

        async def stream() -> AsyncIterator[str]:
            nonlocal cursor
            try:
                while True:
                    try:
                        batch, terminal, changed = await store.read(run_id, x_run_capability, cursor)
                    except (ReplayGap, NotFound):
                        return  # A new request will receive 409 or 404, then resync.
                    for event in batch:
                        cursor = event.seq
                        yield encode(event)
                    if terminal:
                        return
                    if not await heartbeat(changed, config.heartbeat_seconds):
                        yield ": heartbeat\n\n"
            finally:
                await store.unsubscribe(run_id)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    return app
