# 002: Web research

Status: proposed; application implementation not started. Shared contracts and numerical limits: [architecture](../architecture.md).

## Functional requirements

- W01: Verify exact configured model IDs, Responses parameters, live-public-search settings and hard hosted-action cap semantics; fail closed on unsupported configuration.
- W02: Implement the isolated Responses adapter returning normalized observations with untouched annotations, source metadata, observed tool activities, usage and provider IDs.
- W03: Implement bounded plan/research/assess/draft/validate graph flow using Luna, explicit action summaries and shared reservations for every paid attempt.
- W04: Track evidence provenance and immutable drafts; validate citation references and assessed claim support, qualify conflicts and terminate insufficient_evidence when essential support is absent.
- W05: Enforce untrusted-content boundaries, centralized retries/timeouts/cancellation and redacted observable events without raw model reasoning.

## Module contracts and dependency boundaries

Depends on 001 contracts. Provider imports SDK/domain only; graph uses ports. Evidence validation has no network dependency. Hosted web_search stays within Responses requests; no standalone search(query), ingestion or arbitrary fetcher. Inputs, outputs, error shapes and lifecycle follow the shared architecture; no phase may silently redefine them.

## Acceptance criteria and required tests

- A1: Protocol fixtures containing multiple text/tool items retain response IDs, original URL annotation spans and complete source metadata.
- A2: Capability test distinguishes tool invocations from internal search/open/find actions; unsupported hard cap blocks dispatch.
- A3: Fake-ledger graph tests enforce research/all-call/action/token/cost limits across retries and partial failures; missing pricing/usage blocks subsequent dispatch.
- A4: Citation tests reject fabricated URLs, unknown evidence, stale offsets after edits, unsafe links and syntactically valid but unsupported claims.
- A5: Injection fixtures cannot change system policy, request local secrets or expose reasoning; incomplete streams cannot finalize an answer.
- A6: Fake-clock tests cover timeout, Retry-After beyond deadline, ambiguous billed failure and late result after cancellation.

Every requirement must have passing focused tests and every acceptance case above must pass before this phase is complete. Live model access is never required for ordinary deterministic CI. No database or persistent session artifacts are permitted.

## Requirement-to-acceptance traceability

| Requirement | Acceptance cases |
| --- | --- |
| W01 | A2, A3 |
| W02 | A1, A5 |
| W03 | A3, A6 |
| W04 | A4 |
| W05 | A3, A5, A6 |
