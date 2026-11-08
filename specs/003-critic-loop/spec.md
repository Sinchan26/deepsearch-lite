# 003: Critic loop

Status: proposed; application implementation not started. Shared contracts and numerical limits: [architecture](../architecture.md).

## Functional requirements

- C01: Use Sol through a structured critique port with strict verdict, claim-linked issues, evidence IDs and public repair feedback.
- C02: Route pass to finalization only after citation validation; route repair to Luna revision or bounded research under the original ledger.
- C03: Permit at most two revised drafts and three paid critique attempts, including initial review, retries and malformed responses; report unresolved issues and exhaustion without claiming a pass.
- C04: Emit critique/revision progress with immutable draft versions and no private reasoning; malformed critique is a bounded failed attempt.

## Module contracts and dependency boundaries

Depends on 001 and 002. Critic sees sanitized question/evidence/candidate; no search tool or policy mutation. Orchestration owns routing and counters; drafting owns text; evidence module owns citation integrity. Inputs, outputs, error shapes and lifecycle follow the shared architecture; no phase may silently redefine them.

## Acceptance criteria and required tests

- A1: Strict-schema tests reject unknown verdicts, extra reasoning fields, missing claim IDs and references to absent evidence.
- A2: Graph fixtures exercise pass, revise, research-needed, insufficient evidence, malformed output and critic failure.
- A3: Repeated revise requests terminate after version 2 / critique attempt 3; retries and malformed responses consume the three-attempt critique cap and all-call budget and cannot bypass revision ceilings.
- A4: A revised draft with removed supporting evidence cannot finalize, even if critic says pass.
- A5: Cost exhaustion before critic yields limited/unreviewed status with visible feedback; cancellation prevents later revision dispatch.

Every requirement must have passing focused tests and every acceptance case above must pass before this phase is complete. Live model access is never required for ordinary deterministic CI. No database or persistent session artifacts are permitted.

## Requirement-to-acceptance traceability

| Requirement | Acceptance cases |
| --- | --- |
| C01 | A1, A2 |
| C02 | A2, A4 |
| C03 | A3, A5 |
| C04 | A1, A2, A5 |
