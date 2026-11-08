# 005: implementation plan

## Entry gate

Read AGENTS.md, relevant skills and [shared architecture](../architecture.md). Resolve contract conflicts before edits. All preceding phase acceptance criteria must pass before integrating this phase; isolated design and mocks may proceed earlier.

## Work sequence

1. Implement E01 within its documented owner; add focused tests of success, failure and safety behavior before integration.
2. Implement E02 within its documented owner; add focused tests of success, failure and safety behavior before integration.
3. Implement E03 within its documented owner; add focused tests of success, failure and safety behavior before integration.
4. Implement E04 within its documented owner; add focused tests of success, failure and safety behavior before integration.

## Integration and exit gate

Depends on 001-004. Evaluation invokes public API and service ports; it cannot change production policy. Default CI is network-free. Fixtures are test artifacts only; no production offline fallback or persistent research sessions.

Run the acceptance cases in spec.md and relevant pytest/Vitest suites. Type-check/build the affected packages once present. Use fakes for network, clock and usage. Review error paths, terminal races, module imports and public payloads. Record command results and remaining risks in tasks.md; do not mark this phase done based on document creation. Changes to shared contracts require updating downstream specs and tests.

## Risks and handling

Provider capabilities and pricing may differ from assumptions: verify before paid calls and fail closed. Memory and replay are intentionally ephemeral: communicate expiration. Semantic citation support is fallible: use gold fixtures, structured critique and visible insufficient-evidence outcomes. See architecture.md for all mandatory safety limits.
