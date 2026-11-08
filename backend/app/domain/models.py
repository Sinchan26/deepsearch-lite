from __future__ import annotations

import ipaddress
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


PositiveInt = Annotated[int, Field(strict=True, gt=0)]
NonNegativeInt = Annotated[int, Field(strict=True, ge=0)]
Money = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]
Status = Literal[
    "running", "completed", "insufficient_evidence", "limited", "failed", "cancelled", "timed_out"
]
TerminalStatus = Literal["completed", "insufficient_evidence", "limited", "failed", "cancelled", "timed_out"]


class Limits(Model):
    research_requests: PositiveInt = 8
    model_requests: PositiveInt = 16
    hosted_actions: PositiveInt = 16
    revisions: PositiveInt = 2
    critique_attempts: PositiveInt = 3
    input_tokens: PositiveInt = 80_000
    output_tokens: PositiveInt = 16_000
    output_per_request: PositiveInt = 2_000
    cost_usd: Annotated[Decimal, Field(gt=0, allow_inf_nan=False)] = Decimal("1.00")
    timeout_seconds: Annotated[float, Field(gt=0, le=300, allow_inf_nan=False)] = 300


class RunRequest(Model):
    question: str = Field(min_length=1)
    limits: Limits = Field(default_factory=Limits)

    @field_validator("question")
    @classmethod
    def bounded_question(cls, value: str) -> str:
        if not value.strip() or len(value.encode("utf-8")) > 8192:
            raise ValueError("question must contain text and fit in 8 KiB")
        return value


class Usage(Model):
    input_tokens: NonNegativeInt = 0
    output_tokens: NonNegativeInt = 0
    hosted_actions: NonNegativeInt = 0
    cost_usd: Money = Decimal(0)


class Attempt(Model):
    kind: Literal["plan", "research", "draft", "critique", "revision"]
    input_tokens: PositiveInt
    output_tokens: PositiveInt
    hosted_actions: NonNegativeInt = 0
    cost_usd: Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
    pricing_version: str = Field(min_length=1, max_length=128)
    tool_cap_verified: bool = False


class Source(Model):
    id: str = Field(min_length=1, max_length=128)
    url: str = Field(max_length=4096)
    title: str = Field(max_length=1024)

    @field_validator("url")
    @classmethod
    def public_url(cls, value: str) -> str:
        parsed = urlsplit(value)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            raise ValueError("unsafe source URL")
        host = parsed.hostname.lower().rstrip(".")
        if host == "localhost" or host.endswith((".localhost", ".local")):
            raise ValueError("non-public source URL")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and not address.is_global:
            raise ValueError("non-public source URL")
        return value


class Evidence(Model):
    id: str = Field(min_length=1, max_length=128)
    source: Source
    excerpt: str

    @field_validator("excerpt")
    @classmethod
    def bounded_excerpt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 2048:
            raise ValueError("excerpt exceeds 2 KiB")
        return value


class Draft(Model):
    version: NonNegativeInt
    text: str
    evidence_ids: list[str] = Field(max_length=128)
    validated: bool = False
    reviewed: bool = False

    @field_validator("text")
    @classmethod
    def bounded_text(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 32768:
            raise ValueError("draft exceeds 32 KiB")
        return value


class Summary(Model):
    summary: str = Field(min_length=1, max_length=2048)


class SearchActivity(Model):
    action: Literal["search", "open", "find"]
    query: str | None = Field(default=None, max_length=2048)


class Critique(Model):
    version: NonNegativeInt
    verdict: Literal["pass", "revise", "insufficient_evidence"]
    feedback: list[str] = Field(max_length=32)

    @field_validator("feedback")
    @classmethod
    def bounded_feedback(cls, values: list[str]) -> list[str]:
        if any(len(v.encode("utf-8")) > 2048 for v in values):
            raise ValueError("feedback exceeds public limit")
        return values


class Budget(Model):
    model_requests: NonNegativeInt = 0
    research_requests: NonNegativeInt = 0
    critique_attempts: NonNegativeInt = 0
    revisions: NonNegativeInt = 0
    usage: Usage = Field(default_factory=Usage)
    limits: Limits
    frozen: bool = False


class Started(Model):
    limits: Limits


class Revision(Model):
    version: PositiveInt


class Terminal(Model):
    status: TerminalStatus
    reason: Literal[
        "research_not_implemented",
        "finished",
        "insufficient_evidence",
        "budget_exhausted",
        "cancelled",
        "deadline",
        "execution_failed",
        "memory_limit",
    ]


class EventBase(Model):
    schema_version: Literal[1] = 1
    run_id: str
    seq: PositiveInt
    timestamp: datetime


class StartedEvent(EventBase):
    type: Literal["run.started"]
    payload: Started


class SummaryEvent(EventBase):
    type: Literal["plan.summary", "research.action"]
    payload: Summary


class SearchEvent(EventBase):
    type: Literal["search.activity"]
    payload: SearchActivity


class EvidenceEvent(EventBase):
    type: Literal["evidence.added"]
    payload: Evidence


class DraftEvent(EventBase):
    type: Literal["draft.available"]
    payload: Draft


class CritiqueEvent(EventBase):
    type: Literal["critique.feedback"]
    payload: Critique


class RevisionEvent(EventBase):
    type: Literal["revision.started"]
    payload: Revision


class BudgetEvent(EventBase):
    type: Literal["budget.updated"]
    payload: Budget


class TerminalEvent(EventBase):
    type: Literal["run.terminal"]
    payload: Terminal


PublicEvent = Annotated[
    StartedEvent
    | SummaryEvent
    | SearchEvent
    | EvidenceEvent
    | DraftEvent
    | CritiqueEvent
    | RevisionEvent
    | BudgetEvent
    | TerminalEvent,
    Field(discriminator="type"),
]


class Snapshot(Model):
    run_id: str
    seq: NonNegativeInt
    status: Status
    limits: Limits
    plan: Summary | None = None
    action: Summary | None = None
    evidence: list[Evidence] = Field(default_factory=list, max_length=128)
    draft: Draft | None = None
    critique: Critique | None = None
    budget: Budget | None = None
    terminal: Terminal | None = None


class Created(Model):
    run_id: str
    capability: str
