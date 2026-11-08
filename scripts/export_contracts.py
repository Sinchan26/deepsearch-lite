"""Export or check Pydantic's public event schema and synthetic protocol fixtures."""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.domain.models import Limits, PublicEvent
from pydantic import TypeAdapter

root = Path(__file__).resolve().parents[1]
adapter = TypeAdapter(PublicEvent)
schema = adapter.json_schema()
schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
schema["title"] = "PublicEvent"
limits = Limits().model_dump(mode="json")
fixtures = []
items = [
    ("run.started", {"limits": limits}),
    ("plan.summary", {"summary": "Check public sources"}),
    ("research.action", {"summary": "Collect evidence"}),
    ("search.activity", {"action": "search", "query": "synthetic example"}),
    (
        "evidence.added",
        {
            "id": "e1",
            "source": {"id": "s1", "url": "https://example.org", "title": "Example"},
            "excerpt": "Synthetic evidence",
        },
    ),
    ("draft.available", {"version": 0, "text": "Synthetic draft", "evidence_ids": ["e1"]}),
    ("critique.feedback", {"version": 0, "verdict": "revise", "feedback": ["Qualify claim"]}),
    ("revision.started", {"version": 1}),
    ("budget.updated", {"limits": limits}),
    ("run.terminal", {"status": "limited", "reason": "research_not_implemented"}),
]
for seq, (kind, payload) in enumerate(items, 1):
    event = adapter.validate_python(
        dict(
            schema_version=1,
            run_id="synthetic-run",
            seq=seq,
            timestamp=datetime(2026, 11, 8, tzinfo=UTC),
            type=kind,
            payload=payload,
        )
    )
    fixtures.append(event.model_dump(mode="json"))
for name, data in [("public-event.schema.json", schema), ("public-events.fixture.json", fixtures)]:
    target = root / "contracts" / name
    output = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        if target.read_text(encoding="utf-8") != output:
            raise SystemExit(f"Stale contract: {name}")
    else:
        target.parent.mkdir(exist_ok=True)
        target.write_text(output, encoding="utf-8")
print(
    "Public schemas and fixtures verified"
    if "--check" in sys.argv
    else "Exported public schemas and fixtures"
)
