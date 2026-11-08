import asyncio

import pytest
from app.config import Settings
from app.domain.models import RunRequest
from app.events.stream import encode, heartbeat
from app.orchestration.registry import CapacityExceeded, ClosedRun, NotFound, Registry, ReplayGap


class Clock:
    now = 0.0

    def __call__(self):
        return self.now


async def create(registry):
    return await registry.create(RunRequest(question="public question"))


async def test_capacity_ttl_and_restart():
    clock = Clock()
    registry = Registry(Settings(), clock)
    first = await create(registry)
    await create(registry)
    with pytest.raises(CapacityExceeded):
        await create(registry)
    await registry.finish(first.run_id, "limited", "research_not_implemented")
    await create(registry)
    clock.now = 901
    with pytest.raises(NotFound):
        await registry.snapshot(first.run_id, first.capability)
    with pytest.raises(NotFound):
        await Registry(Settings()).snapshot(first.run_id, first.capability)


async def test_terminal_retention_capacity():
    registry = Registry(Settings(retained_runs=1))
    old = await create(registry)
    await registry.finish(old.run_id, "limited", "research_not_implemented")
    new = await create(registry)
    await registry.finish(new.run_id, "limited", "research_not_implemented")
    with pytest.raises(NotFound):
        await registry.snapshot(old.run_id, old.capability)


async def test_cancel_race_and_late_results():
    registry = Registry(Settings())
    run = await create(registry)
    await asyncio.gather(
        registry.cancel(run.run_id, run.capability), registry.finish(run.run_id, "failed", "execution_failed")
    )
    events, done, _ = await registry.read(run.run_id, run.capability, 0)
    assert done and sum(e.type == "run.terminal" for e in events) == 1
    with pytest.raises(ClosedRun):
        await registry.publish(run.run_id, "plan.summary", {"summary": "late"})
    assert (await registry.cancel(run.run_id, run.capability)).seq == 2


async def test_replay_gap_snapshot_and_atomic_resume():
    registry = Registry(Settings(event_count=2))
    run = await create(registry)
    for i in range(3):
        await registry.publish(run.run_id, "plan.summary", {"summary": str(i)})
    with pytest.raises(ReplayGap):
        await registry.subscribe(run.run_id, run.capability, 0)
    snap = await registry.snapshot(run.run_id, run.capability)
    assert snap.plan.summary == "2"
    await registry.publish(run.run_id, "research.action", {"summary": "next"})
    await registry.subscribe(run.run_id, run.capability, snap.seq)
    batch, _, _ = await registry.read(run.run_id, run.capability, snap.seq)
    assert [e.seq for e in batch] == [snap.seq + 1]
    assert encode(batch[0]).startswith(f"id: {snap.seq + 1}\ndata:")
    await registry.unsubscribe(run.run_id)


async def test_subscriber_bounds_and_slow_cursor():
    registry = Registry(Settings(subscribers_per_run=1, event_count=1))
    run = await create(registry)
    await registry.subscribe(run.run_id, run.capability, 0)
    with pytest.raises(CapacityExceeded):
        await registry.subscribe(run.run_id, run.capability, 0)
    await registry.publish(run.run_id, "plan.summary", {"summary": "next"})
    with pytest.raises(ReplayGap):
        await registry.read(run.run_id, run.capability, 0)
    await registry.unsubscribe(run.run_id)
    await registry.subscribe(run.run_id, run.capability, 1)


async def test_deadline_and_heartbeat():
    clock = Clock()
    registry = Registry(Settings(), clock)
    run = await create(registry)
    clock.now = 300
    with pytest.raises(ClosedRun):
        await registry.publish(run.run_id, "plan.summary", {"summary": "too late"})
    assert (await registry.snapshot(run.run_id, run.capability)).status == "timed_out"
    assert not await heartbeat(asyncio.Event(), 0.001)
    changed = asyncio.Event()
    changed.set()
    assert await heartbeat(changed, 15)


async def test_cancel_and_deadline_block_dispatch_reservations():
    from app.domain.models import Attempt

    clock = Clock()
    registry = Registry(Settings(), clock)
    run = await create(registry)
    attempt = Attempt(
        kind="plan", input_tokens=100, output_tokens=50, cost_usd="0.01", pricing_version="test"
    )
    await registry.cancel(run.run_id, run.capability)
    with pytest.raises(ClosedRun):
        await registry.reserve(run.run_id, attempt)
    second = await create(registry)
    clock.now = 301
    with pytest.raises(ClosedRun):
        await registry.reserve(second.run_id, attempt)


async def test_budget_events_and_late_accounting_cannot_reopen_run():
    from app.domain.models import Attempt, Usage

    registry = Registry(Settings())
    run = await create(registry)
    reservation = await registry.reserve(
        run.run_id,
        Attempt(kind="plan", input_tokens=100, output_tokens=50, cost_usd="0.01", pricing_version="test"),
    )
    assert (await registry.snapshot(run.run_id, run.capability)).budget.model_requests == 1
    await registry.cancel(run.run_id, run.capability)
    seq = (await registry.snapshot(run.run_id, run.capability)).seq
    await registry.reconcile(run.run_id, reservation, Usage())
    assert (await registry.snapshot(run.run_id, run.capability)).seq == seq
