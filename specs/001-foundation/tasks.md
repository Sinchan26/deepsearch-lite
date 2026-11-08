# 001: tasks

Phase 001 implemented and locally verified on 2026-11-08. Later phases remain unimplemented.

- [x] T01: Implement F01 and focused success/failure tests. Depends on the entry gate.
- [x] T02: Implement F02 and focused success/failure tests. Depends on T01.
- [x] T03: Implement F03 and focused success/failure tests. Depends on T02.
- [x] T04: Implement F04 and focused success/failure tests. Depends on T03.
- [x] V01: Demonstrate A1 from spec.md; record test name and result. Depends on all T tasks.
- [x] V02: Demonstrate A2 from spec.md; record test name and result. Depends on all T tasks.
- [x] V03: Demonstrate A3 from spec.md; record test name and result. Depends on all T tasks.
- [x] V04: Demonstrate A4 from spec.md; record test name and result. Depends on all T tasks.
- [x] V05: Demonstrate A5 from spec.md; record test name and result. Depends on all T tasks.
- [x] V06: Demonstrate A6 toolchain and cross-language schema compatibility checks. Depends on all T tasks.
- [x] R01: Review traceability from every requirement to tests; verify dependency boundaries and centralized safety policy. Depends on all V tasks.
- [x] R02: Record relevant pytest/Vitest/type/build results and unresolved limitations; mark phase complete only after acceptance. Depends on R01.

## Verification evidence

Local verification completed on Windows with Python 3.13.2 and Node 24.11.1:

| Acceptance | Evidence |
| --- | --- |
| A1 / F01 | test_domain: question byte bounds, strict numeric limits, unknown fields, hard server ceilings, client escalation and unsafe links |
| A2 / F02 | test_budget: concurrent reservations, reconciliation, missing/excess usage freeze, token/cost/call/tool/revision/critique caps; test_registry: active/retained capacity and fake-clock TTL |
| A3 / F03 | test_api: ownership, generic validation errors, CORS and public projections; test_telemetry: in-memory span/metric attribute allowlists |
| A4 / F03 | test_registry/test_api: ordered replay, 409 gap and snapshot resume, slow cursor/subscriber ceilings, heartbeat, disconnect cleanup, cancellation races, late results and deadline dispatch blocking |
| A5 / F02 | test_capacity_ttl_and_restart and test_no_persistence_artifacts: independent registries cannot restore runs; no application database artifacts |
| A6 / F01, F04 | Shared generated event schema and ten variant fixtures validate in Pydantic and Vitest; TypeScript generation drift checks, strict mypy, frontend typecheck/build and mocked tests pass |

Commands and results:

- `.venv/Scripts/python.exe -m pytest -q`: **48 passed**.
- `.venv/Scripts/python.exe -m mypy`: **success, 21 source files**.
- `.venv/Scripts/python.exe -m ruff check backend scripts`: **passed**.
- `.venv/Scripts/python.exe -m ruff format --check backend scripts`: **29 files formatted**.
- `.venv/Scripts/python.exe scripts/export_contracts.py --check`: **passed**.
- Frontend `npm.cmd run contracts:check`: **passed**.
- Frontend `npm.cmd run typecheck`: **passed**.
- Frontend `npm.cmd test`: **2 passed**, exercising all ten event fixtures plus invalid version/type/payload/private-field cases.
- Frontend `npm.cmd run build`: **passed**, Vite 7.3.7 production bundle.

Dependency downloads required approved network access. Frontend test/build execution required approved access outside the Windows sandbox after Vite resolver access-denied errors. No test made a live provider call. CI workflow is written but has not run remotely.

R01 self-review verified domain/policy import isolation, typed public serialization, bounded registry/ring/subscribers, capability protection, deadline/cancellation dispatch guards and one winning terminal outcome. The pre-existing U05 edit in phase 004 was preserved. No commits or pushes were made.

Known limits: foundation default runner terminates limited; provider integration and LangGraph execution are phase 002. Provider pricing/capability/tokenization gates remain unresolved until that phase. TTL eviction is lazy; single-worker state is intentionally ephemeral. Telemetry has no configured remote exporter. Reserved later-phase modules contain package markers only.
