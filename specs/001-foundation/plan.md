# 001: implementation plan

## Entry gate

Read AGENTS.md, relevant skills and [shared architecture](../architecture.md). Resolve contract conflicts before edits. No previous application phase is required. Establish contracts before service implementations.

## Work sequence

1. Implement F01 within its documented owner; add focused tests of success, failure and safety behavior before integration.
2. Implement F02 within its documented owner; add focused tests of success, failure and safety behavior before integration.
3. Implement F03 within its documented owner; add focused tests of success, failure and safety behavior before integration.
4. Implement F04 within its documented owner; add focused tests of success, failure and safety behavior before integration.

## Integration and exit gate

Domain and policy import no framework SDKs. Registry owns lifecycle; API owns transport. A fake orchestrator is sufficient for this phase; no production research adapter.

Run the acceptance cases in spec.md and relevant pytest/Vitest suites. Type-check/build the affected packages once present. Use fakes for network, clock and usage. Review error paths, terminal races, module imports and public payloads. Record command results and remaining risks in tasks.md; do not mark this phase done based on document creation. Changes to shared contracts require updating downstream specs and tests.

## Risks and handling

Provider capabilities and pricing may differ from assumptions: verify before paid calls and fail closed. Memory and replay are intentionally ephemeral: communicate expiration. Semantic citation support is fallible: use gold fixtures, structured critique and visible insufficient-evidence outcomes. See architecture.md for all mandatory safety limits.


## Implemented layout

`backend/app/domain` contains public models, future research contracts and ports; `policy` owns the ledger; `orchestration` owns the ephemeral registry; `api` owns HTTP/SSE/runtime lifecycle; `events` owns framing/heartbeat; `telemetry.py` instruments payload-free terminal metrics and spans. Future provider/evidence/drafting/critique packages are reserved only.

`frontend` contains the React/Vite/Tailwind shell, Motion dependency, shadcn configuration and reserved workspace folders. `contracts` holds generated JSON schema and synthetic fixtures; frontend runtime validation and generated TypeScript use that schema. `scripts/export_contracts.py` checks drift. Root pyproject, dependency snapshot, npm lockfile and CI workflow establish reproducible checks. See README.md for complete structure and commands.
