import json
from pathlib import Path

import pytest
from app.domain.models import Limits, PublicEvent, RunRequest
from app.policy.budget import BudgetExceeded, enforce_ceilings
from pydantic import TypeAdapter, ValidationError


@pytest.mark.parametrize("question", ["", " ", chr(233) * 4097])
def test_question_bounds(question):
    with pytest.raises(ValidationError):
        RunRequest(question=question)


@pytest.mark.parametrize(
    "changes",
    [
        {"model_requests": 0},
        {"input_tokens": -1},
        {"input_tokens": True},
        {"output_tokens": 1.5},
        {"cost_usd": "NaN"},
        {"timeout_seconds": float("inf")},
        {"unexpected": 1},
    ],
)
def test_invalid_limits(changes):
    with pytest.raises(ValidationError):
        Limits(**changes)


def test_unknown_fields_and_client_escalation():
    with pytest.raises(ValidationError):
        RunRequest(question="ok", api_key="private")
    with pytest.raises(BudgetExceeded):
        enforce_ceilings(Limits(model_requests=17), Limits())
    enforce_ceilings(Limits(model_requests=1), Limits())


def test_contract_fixtures_and_no_private_fields():
    adapter = TypeAdapter(PublicEvent)
    fixtures = json.loads(Path("contracts/public-events.fixture.json").read_text())
    for fixture in fixtures:
        adapter.validate_python(fixture)
    for changes in [
        {"schema_version": 2},
        {"reasoning": "private"},
        {"payload": {"prompt": "private"}},
        {"seq": 0},
    ]:
        with pytest.raises(ValidationError):
            adapter.validate_python({**fixtures[0], **changes})


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "http://localhost/a",
        "http://127.0.0.1/a",
        "https://user:pass@example.org",
        "http://192.168.1.1",
    ],
)
def test_unsafe_source_links(url):
    from app.domain.models import Source

    with pytest.raises(ValidationError):
        Source(id="s", url=url, title="source")


def test_server_ceilings_and_explicit_cors():
    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(ceilings=Limits(model_requests=100))
    with pytest.raises(ValidationError):
        Settings(cors_origins=("*",))
