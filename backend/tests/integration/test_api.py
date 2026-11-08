import asyncio
import json

import httpx
import pytest
from app.api.application import create_app
from app.config import Settings
from app.orchestration.registry import Registry


async def hold(run_id):
    await asyncio.Event().wait()


@pytest.fixture
async def client():
    app = create_app(runner=hold)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client, app


async def test_authorization_cors_and_secret_redaction(client):
    client, _ = client
    created = (await client.post("/api/runs", json={"question": "private-question"})).json()
    route = f"/api/runs/{created['run_id']}"
    for suffix in ["", "/events"]:
        for headers in [{}, {"X-Run-Capability": "wrong"}]:
            response = await client.get(route + suffix, headers=headers)
            assert response.status_code == 404
            assert created["capability"] not in response.text
    assert (await client.delete(route)).status_code == 404
    snapshot = await client.get(route, headers={"X-Run-Capability": created["capability"]})
    assert "private-question" not in snapshot.text and created["capability"] not in snapshot.text
    invalid = await client.post("/api/runs", json={"question": "ok", "api_key": "secret-key"})
    assert invalid.status_code == 422 and "secret-key" not in invalid.text
    for origin, allowed in [("http://localhost:5173", True), ("https://evil.example", False)]:
        response = await client.options(
            route,
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-Run-Capability",
            },
        )
        assert ("access-control-allow-origin" in response.headers) == allowed


async def test_capacity_and_client_limit_escalation(client):
    client, _ = client
    for _ in range(2):
        assert (await client.post("/api/runs", json={"question": "ok"})).status_code == 202
    assert (await client.post("/api/runs", json={"question": "ok"})).status_code == 429
    assert (
        await client.post("/api/runs", json={"question": "ok", "limits": {"model_requests": 17}})
    ).status_code == 422


async def test_stream_terminal_replay_and_cancel(client):
    client, app = client
    run = (await client.post("/api/runs", json={"question": "ok"})).json()
    headers = {"X-Run-Capability": run["capability"]}
    route = f"/api/runs/{run['run_id']}"
    assert (await client.delete(route, headers=headers)).json()["status"] == "cancelled"
    assert (await client.delete(route, headers=headers)).json()["seq"] == 2
    stream = await client.get(route + "/events", headers=headers)
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    events = [json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith("data: ")]
    assert [e["seq"] for e in events] == [1, 2]
    assert events[-1]["type"] == "run.terminal"
    replay = await client.get(route + "/events", headers={**headers, "Last-Event-ID": "1"})
    assert "id: 1" not in replay.text and "id: 2" in replay.text
    assert app.state.registry.runs[run["run_id"]].subscribers == 0


async def test_replay_gap_returns_409_before_stream():
    registry = Registry(Settings(event_count=1))
    app = create_app(registry=registry, runner=hold)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            run = (await client.post("/api/runs", json={"question": "ok"})).json()
            headers = {"X-Run-Capability": run["capability"]}
            await registry.publish(run["run_id"], "plan.summary", {"summary": "next"})
            route = f"/api/runs/{run['run_id']}"
            assert (await client.get(route + "/events", headers=headers)).status_code == 409
            snap = (await client.get(route, headers=headers)).json()
            await client.delete(route, headers=headers)
            stream = await client.get(
                route + "/events", headers={**headers, "Last-Event-ID": str(snap["seq"])}
            )
            assert stream.status_code == 200 and "run.terminal" in stream.text


async def test_default_runner_and_deadline():
    for runner, limits, expected in [(None, {}, "limited"), (hold, {"timeout_seconds": 0.01}, "timed_out")]:
        app = create_app(runner=runner)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                run = (await client.post("/api/runs", json={"question": "ok", "limits": limits})).json()
                await asyncio.sleep(0.03)
                snap = await client.get(
                    f"/api/runs/{run['run_id']}", headers={"X-Run-Capability": run["capability"]}
                )
                assert snap.json()["status"] == expected


async def test_heartbeat_disconnect_does_not_cancel_or_leak_subscription():
    from starlette.routing import Route

    registry = Registry(Settings(heartbeat_seconds=0.001))
    app = create_app(settings=registry.settings, registry=registry, runner=hold)
    from app.domain.models import RunRequest

    run = await registry.create(RunRequest(question="ok"))
    endpoint = next(
        route.endpoint for route in app.routes if isinstance(route, Route) and route.path.endswith("/events")
    )
    response = await endpoint(run.run_id, run.capability, "1")
    iterator = response.body_iterator
    assert await anext(iterator) == ": heartbeat\n\n"
    await iterator.aclose()
    assert registry.runs[run.run_id].subscribers == 0
    assert (await registry.snapshot(run.run_id, run.capability)).status == "running"


async def test_injected_runner_terminal_summary_and_private_error():
    registry = Registry(Settings())

    async def fake(run_id):
        await registry.publish(run_id, "plan.summary", {"summary": "Public execution summary"})
        raise RuntimeError("PRIVATE ERROR KEY")

    app = create_app(registry=registry, runner=fake)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            run = (await client.post("/api/runs", json={"question": "ok"})).json()
            await asyncio.sleep(0)
            response = await client.get(
                f"/api/runs/{run['run_id']}/events", headers={"X-Run-Capability": run["capability"]}
            )
            assert "PRIVATE ERROR KEY" not in response.text
            assert "Public execution summary" in response.text
            assert "execution_failed" in response.text
