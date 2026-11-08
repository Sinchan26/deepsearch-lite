# 005: Evaluation

Status: proposed; application implementation not started. Shared contracts and numerical limits: [architecture](../architecture.md).

## Functional requirements

- E01: Create deterministic offline contract, graph and end-to-end evaluation scenarios using synthetic provider protocol fixtures, not a retrieval corpus.
- E02: Measure citation reference integrity, assessed support, essential-claim coverage, injection resistance, critique repair behavior and bounded execution.
- E03: Validate OpenTelemetry counters/durations/status, token and estimated-cost accounting without session payloads or private reasoning.
- E04: Provide explicitly opted-in, independently budgeted live public-web evaluation for configured model/tool capability and current evidence quality; report uncertainty and failures.

## Module contracts and dependency boundaries

Depends on 001-004. Evaluation invokes public API and service ports; it cannot change production policy. Default CI is network-free. Fixtures are test artifacts only; no production offline fallback or persistent research sessions. Inputs, outputs, error shapes and lifecycle follow the shared architecture; no phase may silently redefine them.

## Acceptance criteria and required tests

- A1: Deterministic suite covers supported, unsupported, conflicting, malicious, malformed, exhausted, cancelled and disconnected scenarios with fixed seeds/fake clocks.
- A2: Release gate: zero unknown citation references, zero unsafe rendered links/private reasoning leaks, 100% bounded-run invariant cases pass.
- A3: Curated synthetic gold set requires all designated essential claims supported or explicitly withheld and all designated injection attempts rejected; do not conflate this with general factual accuracy.
- A4: End-to-end tests correlate HTTP/SSE, final draft version, citation ledger and terminal status across backend/frontend.
- A5: Telemetry tests verify no question, evidence, draft, prompt, key or capability values in exported attributes; ledger totals match fixture usage.
- A6: Live evaluation is skipped by default; explicit opt-in requires verified prices/capabilities, max 3 runs and USD 3 aggregate reservation ceiling, plus per-run limits. Report timestamps, models, sample count, estimates and failed cases.

Every requirement must have passing focused tests and every acceptance case above must pass before this phase is complete. Live model access is never required for ordinary deterministic CI. No database or persistent session artifacts are permitted.

## Requirement-to-acceptance traceability

| Requirement | Acceptance cases |
| --- | --- |
| E01 | A1, A4 |
| E02 | A2, A3 |
| E03 | A5 |
| E04 | A6 |
