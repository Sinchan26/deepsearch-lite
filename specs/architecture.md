# Proposed architecture and shared contracts

Status: proposed implementation baseline, 2026-11-08. Phase 001 foundation implementation is authorized; subsequent phases remain planned. All five phase triplets are normative together with this document; changing a shared contract requires updating affected phases. Phase order: 001 -> 002 -> 003 -> 004 -> 005.

## Decisions

1. One FastAPI worker owns an ephemeral run registry and non-durable LangGraph state. Restart loses runs. Responses requests use `store=false`; send explicit bounded in-memory context, with no Conversations API or durable previous-response chaining. This disables application-requested response storage; provider abuse-monitoring/retention policies are separate and must be documented without promising zero provider retention. No database, disk checkpoint, vector retrieval, ingestion, PDF parsing or persistent browser state.
2. React/TypeScript/Vite with Tailwind, shadcn/ui and Motion consumes HTTP/SSE. Pydantic defines backend contracts; TypeScript mirrors the public versioned schemas. pytest and Vitest use fake provider responses. OpenTelemetry records payload-free operational metrics.
3. ReAct-style transitions are `plan -> research -> assess -> research|draft -> validate -> critique -> revise|research|finish`. Actions and observations drive transitions; private model reasoning is neither requested as public output nor exposed. Critique is added in phase 003; phase 002 can terminate after validation.
4. GPT-6 Luna performs planning, research and drafting; GPT-6.1 Sol critiques. Configuration defaults are `gpt-6-luna` and `gpt-6.1-sol`, subject to official API/account capability verification before implementation. No silent substitution. Codex development agents inherit their parent model independently.
5. Hosted web_search is a tool within Responses requests. A provider adapter owns request construction, streaming normalization and usage accounting; LangGraph never imports OpenAI SDK types. No arbitrary URL-fetching subsystem.
6. Drafts are immutable versions. Citations reference evidence IDs; every version is validated before finalization. Discovered URLs alone do not establish claim support. Critique cannot bypass validation or change policy.
7. Research calls run serially per run. All retries and revision-directed searches share one ledger. Terminal states are completed, insufficient_evidence, limited, failed, cancelled and timed_out. Exactly one terminal event wins races.

## Module ownership and contracts

The paths below define module ownership. Phase 001 creates the structure and foundational contracts; later-phase services remain unimplemented.

| Module | Input -> output | Dependency boundary |
| --- | --- | --- |
| backend/app/domain | Pydantic RunRequest, Limits, ResearchState, PublicEvent | No FastAPI, OpenAI or LangGraph imports |
| backend/app/policy | reserve(attempt specification), reconcile(usage) -> BudgetDecision | Domain only; atomic per-run ledger |
| backend/app/providers/openai_responses | ResearchRequest -> ResearchObservation; draft/critique completion ports | Domain and SDK only; no graph or HTTP transport |
| backend/app/evidence | observation -> sources/evidence; validate(Draft) -> ValidationResult | Domain only; no external I/O |
| backend/app/drafting | question + evidence + optional repair -> Draft | Completion port and domain; no search by itself |
| backend/app/critique | Draft + evidence -> Critique | Structured completion port; no policy mutations |
| backend/app/orchestration | RunRequest + ports -> state transitions and domain events | LangGraph/domain/service ports; no SDK or routes |
| backend/app/events | domain events -> allowlisted PublicEvent | No raw graph/provider serialization |
| backend/app/api | HTTP input -> validated request, snapshot, SSE and cancellation | Registry/orchestration/events; no research decisions |
| frontend/src | public HTTP/SSE -> research workspace | No backend internals, credentials or provider calls |

ResearchRequest contains question, public action summary, evidence context and immutable reserved limits. ResearchObservation contains normalized answer text, response ID, tool-call IDs, observed search/open/find actions, source metadata, untouched URL annotations, usage and completion status. Partial/malformed observations cannot become validated final evidence.

Source contains stable ID, original URL, normalized deduplication URL, title, acquired_at and provider provenance. Evidence contains ID, source ID, supporting excerpt/claim, original annotation spans and original annotated text. Keep offsets tied to the original text; revisions build explicit claim-to-evidence references rather than recycling offsets. Draft contains version, text and claim spans with evidence IDs. ValidationResult reports missing/unknown references, unsafe URLs, unsupported claims and actionable gaps. Structural validation is deterministic; semantic support assessment is separately reported and does not promise factual certainty.

Critique contains verdict (`pass|revise|insufficient_evidence`), issues with claim ID, severity, evidence IDs and concise public feedback, plus bounded repair requests. Strict schemas reject unknown fields; one malformed response is a failed attempt, not permission for an unlimited repair loop.

## Central safety policy

These proposed defaults must become validated configuration with positive finite bounds. Client input may lower limits, never raise server ceilings.

| Limit | Default and enforcement |
| --- | --- |
| Research requests | 8 attempts including retries and critique-directed research |
| All model requests | 16 attempts including planning, drafting, critiques and retries |
| Hosted actions | 16 total search/open/find actions; reserve up to 2 per research attempt |
| Revisions | 2 revised drafts; initial draft is version 0; at most 3 paid critique attempts, including retries and malformed responses |
| Tokens | 80,000 aggregate input; 16,000 aggregate output; 2,000 output per request, including provider-reported reasoning usage |
| Estimated cost | USD 1.00 per run, with operator-supplied versioned model/tool prices and worst-case reservations |
| Time | 300 seconds monotonic run deadline; request timeout min(45 seconds, remaining time) |
| Retries | At most 2 per logical operation, within global limits; transient explicit 429/5xx only, exponential jitter (1s/2s base, max 10s), honor Retry-After only within deadline |
| Ambiguous failure | No automatic retry of timeout/disconnect with unknown billed outcome; retain reservation and terminate limited/failed |
| Capacity | 2 active runs, 20 retained terminal runs; terminal TTL 15 minutes; excess creation returns 429 |
| Memory | Question 8 KiB; 64 sources, 128 evidence entries, 2 KiB per excerpt, 256 KiB normalized provider text per run; event ring 512 events / 1 MiB; draft 32 KiB; reject/truncate at typed boundaries with visible limitation |

Reserve input tokens using a verified tokenizer or conservative upper bound, maximum output, tool actions and estimated USD before dispatch. Reconcile actual usage on success; never refund ambiguous usage. Disable SDK automatic retries. Pricing must cover model input/output, reasoning and applicable hosted search/context charges. Missing price, usage or an enforceable provider tool cap blocks further paid calls. Reservations provide an application estimate, not an exact invoice guarantee.

Implementation gate: verify whether the selected Responses model/API can enforce the reserved number of hosted actions, including any internal actions. Do not assume `max_tool_calls` bounds internal search/open/find operations. If unsupported, fail configuration before paid research and propose a spec change; do not claim a hard action cap from post-hoc counting. Record verified semantics in phase 002.

Check cancellation/deadline before every node and dispatch. Cancellation stops dispatch, cancels local tasks and ignores late results; it cannot guarantee provider-side cancellation or refunds. Graph recursion limit is an additional fuse, never the budget policy. Exhaustion produces a validated partial answer with limitations if possible without another paid call, otherwise a terminal explanation. Never label an uncritiqued answer as passed.

## Public HTTP and streaming contract

Local-development deployment binds loopback by default with explicit CORS origins. Public hosting/authentication is outside this baseline. POST /api/runs accepts question and lower optional limits, returns 202 with random run_id and ephemeral ownership capability. A custom header carries the capability on snapshot, stream and cancellation requests; never put it in URLs or logs. The browser uses fetch-based SSE parsing to support headers. GET /api/runs/{id} returns only a public snapshot. GET /api/runs/{id}/events streams events. DELETE /api/runs/{id} idempotently requests cancellation. Missing/invalid capability is rejected without revealing run existence. Expired/unknown authorized state returns 404/410 as applicable.

PublicEvent fields: schema_version=1, run_id, monotonic seq, UTC timestamp, type, typed payload. SSE `id` equals seq; `data` is JSON. Types: run.started, plan.summary, research.action, search.activity, evidence.added, draft.available, critique.feedback, revision.started, budget.updated, run.terminal. Payloads contain action labels, query/activity where actually observable, evidence/source links, draft version, concise critique and usage/limits. Do not invent exact search queries when provider omits them. No prompts, raw reasoning, raw provider objects, secrets or internal exceptions.

Heartbeat comments every 15 seconds. Last-Event-ID replays retained events, with deduplication by run_id/seq. Replay gap returns 409 before streaming and requires GET snapshot (with current seq) then resume; subscribe atomically from that seq to avoid races. Disconnect does not cancel or create a run. Bounded subscribers and ring buffers prevent slow clients exhausting memory; disconnect slow subscribers with explicit resync behavior. Terminal event is retained until TTL/capacity eviction. Snapshot provides terminal state if the terminal event was missed. UI restart cannot restore a lost capability or run.

## Evidence and injection policy

Separate trusted system policy, user question and untrusted web material. Web text never grants tool permissions, changes models/budgets or requests secrets. Critic receives question, sanitized evidence and candidate only. No code execution or local-file/tool delegation from web content. Request live public web access; do not ingest uploads or private connectors.

Only absolute HTTP(S) citations without embedded credentials are rendered. Reject dangerous schemes and private/loopback link targets where identifiable; the application never follows arbitrary evidence URLs server-side. Normalize URLs for deduplication without destroying original provenance. Sanitize Markdown, escape titles/excerpts, disable raw HTML and apply safe external-link attributes. Redact keys/capabilities from logs and events. Unsupported essential claims yield insufficient_evidence; conflicting sources are disclosed. Citation validity covers provenance, reference integrity and assessed support, not a guarantee that the internet is correct.

## Validation strategy and references

Each phase defines requirement IDs, task dependencies and observable tests. Deterministic mocked tests are CI gates; optional live tests verify model/tool capabilities and quality within a separate explicit budget. Telemetry includes durations, counts, status, tokens and estimated cost, never question/web/draft bodies by default. No persistent session payloads in traces.

Official references consulted 2026-11-08: [Responses hosted web search](https://developers.openai.com/api/docs/guides/tools-web-search), [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference). Model/tool/account capability remains an implementation gate, not a claim that live integration was tested.


## Foundation implementation decisions

The phase 001 default runner terminates `limited` with the fixed reason `research_not_implemented`; it performs no research and makes no paid calls. Tests inject a controllable runner. Production graph execution starts in phase 002.

Every endpoint uses `X-Run-Capability`. Unknown, expired and unauthorized run access uniformly returns 404, avoiding an unbounded tombstone registry and existence leaks. Run creation accepts no secrets. API validation errors return a generic message without echoing request bodies.

Snapshots retain the latest public plan, action, budget, draft, critique and bounded evidence list independently of the replay ring. Event payloads are typed and contain public text only; private provider objects are never accepted. Each run permits four simultaneous stream subscribers. A stream cursor falling behind the ring disconnects; reconnect receives 409 and resynchronizes from snapshot. Heartbeats are comments, not sequenced events. Terminal events are always the final retained event.

A missing usage reconciliation freezes the paid ledger; reservations for ambiguous results remain charged. Oversized actual usage freezes the ledger rather than permitting further calls. Pricing/version and tool-cap verification are required per attempt, with no default fictional prices. Foundation accepts caller-supplied conservative reservations; phase 002 owns verified tokenization and pricing integration.
