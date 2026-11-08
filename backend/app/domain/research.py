"""Service-port contracts only. Provider integration belongs to phase 002."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.domain.models import Attempt, Draft, Evidence, Limits, Model, NonNegativeInt, Source, Usage


class Annotation(Model):
    url: str
    title: str
    start_index: NonNegativeInt
    end_index: NonNegativeInt


class SourceRecord(Model):
    source: Source
    normalized_url: str
    acquired_at: datetime
    response_id: str
    tool_call_ids: list[str] = Field(max_length=16)


class EvidenceRecord(Model):
    evidence: Evidence
    original_text: str = Field(max_length=262144)
    annotations: list[Annotation] = Field(max_length=128)
    provenance: SourceRecord


class ResearchRequest(Model):
    question: str = Field(max_length=8192)
    action_summary: str = Field(max_length=2048)
    evidence: list[EvidenceRecord] = Field(max_length=128)
    limits: Limits
    reservation: Attempt


class ObservedAction(Model):
    action: Literal["search", "open", "find"]
    query: str | None = Field(default=None, max_length=2048)
    tool_call_id: str


class ResearchObservation(Model):
    text: str = Field(max_length=262144)
    response_id: str
    actions: list[ObservedAction] = Field(max_length=16)
    sources: list[SourceRecord] = Field(max_length=64)
    annotations: list[Annotation] = Field(max_length=128)
    usage: Usage | None
    status: Literal["complete", "incomplete", "failed"]


class DraftRequest(Model):
    question: str = Field(max_length=8192)
    evidence: list[EvidenceRecord] = Field(max_length=128)
    previous: Draft | None = None
    repair: list[str] = Field(default_factory=list, max_length=32)


class CritiqueRequest(Model):
    question: str = Field(max_length=8192)
    evidence: list[EvidenceRecord] = Field(max_length=128)
    candidate: Draft


class CritiqueIssue(Model):
    claim_id: str
    severity: Literal["low", "medium", "high"]
    evidence_ids: list[str] = Field(max_length=128)
    feedback: str = Field(max_length=2048)


class StructuredCritique(Model):
    verdict: Literal["pass", "revise", "insufficient_evidence"]
    issues: list[CritiqueIssue] = Field(max_length=32)
    repair_requests: list[str] = Field(max_length=32)
