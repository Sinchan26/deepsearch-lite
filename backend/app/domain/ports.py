from typing import Protocol

from app.domain.models import Draft, Snapshot
from app.domain.research import (
    CritiqueRequest,
    DraftRequest,
    ResearchObservation,
    ResearchRequest,
    StructuredCritique,
)


class Runner(Protocol):
    async def __call__(self, run_id: str) -> None: ...


class SnapshotReader(Protocol):
    async def snapshot(self, run_id: str, capability: str) -> Snapshot: ...


class Researcher(Protocol):
    async def research(self, request: "ResearchRequest") -> "ResearchObservation": ...


class Drafter(Protocol):
    async def draft(self, request: "DraftRequest") -> "Draft": ...


class Critic(Protocol):
    async def critique(self, request: "CritiqueRequest") -> "StructuredCritique": ...
