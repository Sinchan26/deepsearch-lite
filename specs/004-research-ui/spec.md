# 004: Research workspace

Status: proposed; application implementation not started. Shared contracts and numerical limits: [architecture](../architecture.md).

## Functional requirements

- U01: Create an accessible React workspace for question submission, plan/progress, actual research/search activity, evidence links and immutable draft versions.
- U02: Show structured critique, revision count, limits and terminal outcomes, including insufficient evidence, unreviewed partial answer and expired run.
- U03: Implement typed fetch-SSE transport with in-memory capability, sequence deduplication, snapshot resync, cancellation and honest disconnect state.
- U04: Use Tailwind, shadcn/ui and Motion with keyboard navigation, reduced motion, safe Markdown/link rendering and server-only API credentials.

## Module contracts and dependency boundaries

Depends on public contracts from 001-003. UI consumes only HTTP/SSE and never graph or provider objects. Transport parser is separate from React views. No localStorage, IndexedDB, service-worker session cache or persistence. Inputs, outputs, error shapes and lifecycle follow the shared architecture; no phase may silently redefine them.

## Acceptance criteria and required tests

- A1: Vitest component fixtures render every public event type and terminal status, preserving source links and draft/critique association.
- A2: Transport tests split SSE frames across chunks, handle CRLF/comments/multiline data, reject malformed or unsupported schemas and deduplicate replay.
- A3: Reconnect tests recover from a replay gap via snapshot without creating a second run or losing intervening events.
- A4: Interaction tests submit once, cancel idempotently and show reconnecting/expired states without falsely reporting completion.
- A5: Keyboard/reduced-motion and automated accessibility checks cover form, live region and evidence/critique navigation.
- A6: XSS fixtures for Markdown, titles and URL schemes stay inert; production build contains no API key and browser storage remains unused.

Every requirement must have passing focused tests and every acceptance case above must pass before this phase is complete. Live model access is never required for ordinary deterministic CI. No database or persistent session artifacts are permitted.

## Requirement-to-acceptance traceability

| Requirement | Acceptance cases |
| --- | --- |
| U01 | A1, A5 |
| U02 | A1, A4 |
| U03 | A2, A3, A4 |
| U04 | A5, A6 |
