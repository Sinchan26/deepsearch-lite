/* Generated from Pydantic. Do not edit. */

export type PublicEvent =
  | StartedEvent
  | SummaryEvent
  | SearchEvent
  | EvidenceEvent
  | DraftEvent
  | CritiqueEvent
  | RevisionEvent
  | BudgetEvent
  | TerminalEvent;
export type CostUsd = number | string;
export type CritiqueAttempts = number;
export type HostedActions = number;
export type InputTokens = number;
export type ModelRequests = number;
export type OutputPerRequest = number;
export type OutputTokens = number;
export type ResearchRequests = number;
export type Revisions = number;
export type TimeoutSeconds = number;
export type RunId = string;
export type SchemaVersion = 1;
export type Seq = number;
export type Timestamp = string;
export type Type = "run.started";
export type Summary1 = string;
export type RunId1 = string;
export type SchemaVersion1 = 1;
export type Seq1 = number;
export type Timestamp1 = string;
export type Type1 = "plan.summary" | "research.action";
export type Action = "search" | "open" | "find";
export type Query = string | null;
export type RunId2 = string;
export type SchemaVersion2 = 1;
export type Seq2 = number;
export type Timestamp2 = string;
export type Type2 = "search.activity";
export type Excerpt = string;
export type Id = string;
export type Id1 = string;
export type Title = string;
export type Url = string;
export type RunId3 = string;
export type SchemaVersion3 = 1;
export type Seq3 = number;
export type Timestamp3 = string;
export type Type3 = "evidence.added";
/**
 * @maxItems 128
 */
export type EvidenceIds = string[];
export type Reviewed = boolean;
export type Text = string;
export type Validated = boolean;
export type Version = number;
export type RunId4 = string;
export type SchemaVersion4 = 1;
export type Seq4 = number;
export type Timestamp4 = string;
export type Type4 = "draft.available";
/**
 * @maxItems 32
 */
export type Feedback = string[];
export type Verdict = "pass" | "revise" | "insufficient_evidence";
export type Version1 = number;
export type RunId5 = string;
export type SchemaVersion5 = 1;
export type Seq5 = number;
export type Timestamp5 = string;
export type Type5 = "critique.feedback";
export type Version2 = number;
export type RunId6 = string;
export type SchemaVersion6 = 1;
export type Seq6 = number;
export type Timestamp6 = string;
export type Type6 = "revision.started";
export type CritiqueAttempts1 = number;
export type Frozen = boolean;
export type ModelRequests1 = number;
export type ResearchRequests1 = number;
export type Revisions1 = number;
export type CostUsd1 = number | string;
export type HostedActions1 = number;
export type InputTokens1 = number;
export type OutputTokens1 = number;
export type RunId7 = string;
export type SchemaVersion7 = 1;
export type Seq7 = number;
export type Timestamp7 = string;
export type Type7 = "budget.updated";
export type Reason =
  | "research_not_implemented"
  | "finished"
  | "insufficient_evidence"
  | "budget_exhausted"
  | "cancelled"
  | "deadline"
  | "execution_failed"
  | "memory_limit";
export type Status = "completed" | "insufficient_evidence" | "limited" | "failed" | "cancelled" | "timed_out";
export type RunId8 = string;
export type SchemaVersion8 = 1;
export type Seq8 = number;
export type Timestamp8 = string;
export type Type8 = "run.terminal";

export interface StartedEvent {
  payload: Started;
  run_id: RunId;
  schema_version?: SchemaVersion;
  seq: Seq;
  timestamp: Timestamp;
  type: Type;
}
export interface Started {
  limits: Limits;
}
export interface Limits {
  cost_usd?: CostUsd;
  critique_attempts?: CritiqueAttempts;
  hosted_actions?: HostedActions;
  input_tokens?: InputTokens;
  model_requests?: ModelRequests;
  output_per_request?: OutputPerRequest;
  output_tokens?: OutputTokens;
  research_requests?: ResearchRequests;
  revisions?: Revisions;
  timeout_seconds?: TimeoutSeconds;
}
export interface SummaryEvent {
  payload: Summary;
  run_id: RunId1;
  schema_version?: SchemaVersion1;
  seq: Seq1;
  timestamp: Timestamp1;
  type: Type1;
}
export interface Summary {
  summary: Summary1;
}
export interface SearchEvent {
  payload: SearchActivity;
  run_id: RunId2;
  schema_version?: SchemaVersion2;
  seq: Seq2;
  timestamp: Timestamp2;
  type: Type2;
}
export interface SearchActivity {
  action: Action;
  query?: Query;
}
export interface EvidenceEvent {
  payload: Evidence;
  run_id: RunId3;
  schema_version?: SchemaVersion3;
  seq: Seq3;
  timestamp: Timestamp3;
  type: Type3;
}
export interface Evidence {
  excerpt: Excerpt;
  id: Id;
  source: Source;
}
export interface Source {
  id: Id1;
  title: Title;
  url: Url;
}
export interface DraftEvent {
  payload: Draft;
  run_id: RunId4;
  schema_version?: SchemaVersion4;
  seq: Seq4;
  timestamp: Timestamp4;
  type: Type4;
}
export interface Draft {
  evidence_ids: EvidenceIds;
  reviewed?: Reviewed;
  text: Text;
  validated?: Validated;
  version: Version;
}
export interface CritiqueEvent {
  payload: Critique;
  run_id: RunId5;
  schema_version?: SchemaVersion5;
  seq: Seq5;
  timestamp: Timestamp5;
  type: Type5;
}
export interface Critique {
  feedback: Feedback;
  verdict: Verdict;
  version: Version1;
}
export interface RevisionEvent {
  payload: Revision;
  run_id: RunId6;
  schema_version?: SchemaVersion6;
  seq: Seq6;
  timestamp: Timestamp6;
  type: Type6;
}
export interface Revision {
  version: Version2;
}
export interface BudgetEvent {
  payload: Budget;
  run_id: RunId7;
  schema_version?: SchemaVersion7;
  seq: Seq7;
  timestamp: Timestamp7;
  type: Type7;
}
export interface Budget {
  critique_attempts?: CritiqueAttempts1;
  frozen?: Frozen;
  limits: Limits;
  model_requests?: ModelRequests1;
  research_requests?: ResearchRequests1;
  revisions?: Revisions1;
  usage?: Usage;
}
export interface Usage {
  cost_usd?: CostUsd1;
  hosted_actions?: HostedActions1;
  input_tokens?: InputTokens1;
  output_tokens?: OutputTokens1;
}
export interface TerminalEvent {
  payload: Terminal;
  run_id: RunId8;
  schema_version?: SchemaVersion8;
  seq: Seq8;
  timestamp: Timestamp8;
  type: Type8;
}
export interface Terminal {
  reason: Reason;
  status: Status;
}
