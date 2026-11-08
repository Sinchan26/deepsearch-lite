# 001: Foundation

Status: implemented and locally verified on 2026-11-08. Shared contracts and numerical limits: [architecture](../architecture.md).

## Functional requirements

- F01: Define Pydantic domain schemas, server configuration and typed service ports matching architecture.md; reject invalid limits and oversized questions.
- F02: Provide an ephemeral bounded registry with atomic budget reservation, cancellation, terminal-state ownership and TTL eviction; use no durable checkpointer.
- F03: Define versioned HTTP/SSE public projections, capability authorization, sequence/replay semantics and payload-free OpenTelemetry instrumentation.
- F04: Establish future backend/frontend toolchains, mocked test harnesses and schema compatibility checks without enabling live provider traffic by default.

## Module contracts and dependency boundaries

Domain and policy import no framework SDKs. Registry owns lifecycle; API owns transport. A fake orchestrator is sufficient for this phase; no production research adapter. Inputs, outputs, error shapes and lifecycle follow the shared architecture; no phase may silently redefine them.

## Acceptance criteria and required tests

- A1: Schema tests reject zero/negative limits, client ceiling escalation, unknown fields and >8 KiB questions.
- A2: Fake-clock tests prove atomic reservations cannot overspend, TTL evicts terminal runs and capacity rejects the third active run.
- A3: API tests reject missing/wrong capabilities, enforce CORS and ensure secrets never enter events or trace attributes.
- A4: SSE tests prove monotonic sequence, heartbeat, replay-gap snapshot recovery, slow-consumer bounds and exactly one terminal event under cancellation races.
- A5: Restart test proves no run restoration and filesystem inspection finds no database/checkpoint/session artifacts.

- A6: Backend schema/type checks and frontend type/build checks pass; a public-event fixture validates against Pydantic and the TypeScript contract, with unknown versions rejected. Default pytest/Vitest commands execute mocked smoke tests without network or credentials.

Every requirement must have passing focused tests and every acceptance case above must pass before this phase is complete. Live model access is never required for ordinary deterministic CI. No database or persistent session artifacts are permitted.

## Requirement-to-acceptance traceability

| Requirement | Acceptance cases |
| --- | --- |
| F01 | A1, A6 |
| F02 | A2, A5 |
| F03 | A3, A4 |
| F04 | A6 |


## Foundation-specific behavior

The default runner performs no research and ends `limited` with `research_not_implemented`. Integration tests inject fake runners. LangGraph and OpenAI SDK integration remain phase 002 work; their reserved package directories contain no provider implementation. Local configuration uses explicit typed Settings rather than loading secrets or environment files.

Ownership uses `X-Run-Capability`. Unknown, expired and unauthorized access uniformly returns 404. Replay gaps return 409 before streaming; cursors falling behind during an open stream disconnect and require snapshot recovery. Four subscribers per run is the server ceiling. Terminal TTL cleanup is lazy on access and retained count is always bounded. API responses use no-store.

Public event TypeScript definitions are generated from Pydantic JSON Schema. Both languages validate the same synthetic fixtures; schema drift is checked in CI. No external telemetry exporter or live model traffic is enabled by default.
