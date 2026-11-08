# 002: implementation plan

## Entry gate

Read AGENTS.md, relevant skills and [shared architecture](../architecture.md). Resolve contract conflicts before edits. All preceding phase acceptance criteria must pass before integrating this phase; isolated design and mocks may proceed earlier.

## Work sequence

1. Implement W01 within its documented owner; add focused tests of success, failure and safety behavior before integration.
2. Implement W02 within its documented owner; add focused tests of success, failure and safety behavior before integration.
3. Implement W03 within its documented owner; add focused tests of success, failure and safety behavior before integration.
4. Implement W04 within its documented owner; add focused tests of success, failure and safety behavior before integration.
5. Implement W05 within its documented owner; add focused tests of success, failure and safety behavior before integration.

## Integration and exit gate

Depends on 001 contracts. Provider imports SDK/domain only; graph uses ports. Evidence validation has no network dependency. Hosted web_search stays within Responses requests; no standalone search(query), ingestion or arbitrary fetcher.

Run the acceptance cases in spec.md and relevant pytest/Vitest suites. Type-check/build the affected packages once present. Use fakes for network, clock and usage. Review error paths, terminal races, module imports and public payloads. Record command results and remaining risks in tasks.md; do not mark this phase done based on document creation. Changes to shared contracts require updating downstream specs and tests.

## Risks and handling

Provider capabilities and pricing may differ from assumptions: verify before paid calls and fail closed. Memory and replay are intentionally ephemeral: communicate expiration. Semantic citation support is fallible: use gold fixtures, structured critique and visible insufficient-evidence outcomes. See architecture.md for all mandatory safety limits.
