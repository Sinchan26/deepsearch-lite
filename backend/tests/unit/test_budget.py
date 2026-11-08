import asyncio
from decimal import Decimal

import pytest
from app.domain.models import Attempt, Limits, Usage
from app.policy.budget import BudgetExceeded, Ledger


def attempt(**changes):
    return Attempt(
        **dict(
            dict(
                kind="research",
                input_tokens=100,
                output_tokens=50,
                hosted_actions=2,
                cost_usd=Decimal("0.1"),
                pricing_version="test",
                tool_cap_verified=True,
            ),
            **changes,
        )
    )


async def test_atomic_reservation_serializes_concurrent_attempts():
    ledger = Ledger(Limits())
    results = await asyncio.gather(*(ledger.reserve(attempt()) for _ in range(10)), return_exceptions=True)
    assert sum(isinstance(r, int) for r in results) == 1
    assert ledger.snapshot().model_requests == 1
    assert ledger.snapshot().usage.cost_usd == Decimal("0.1")


async def test_reconciliation_and_global_attempt_limits():
    ledger = Ledger(Limits(model_requests=2, research_requests=2))
    for _ in range(2):
        reservation = await ledger.reserve(attempt())
        await ledger.reconcile(
            reservation, Usage(input_tokens=80, output_tokens=20, hosted_actions=1, cost_usd=Decimal("0.05"))
        )
    assert ledger.snapshot().usage.input_tokens == 160
    assert ledger.snapshot().usage.cost_usd == Decimal("0.10")
    with pytest.raises(BudgetExceeded):
        await ledger.reserve(attempt())


@pytest.mark.parametrize("actual", [None, Usage(input_tokens=101)])
async def test_missing_or_excess_usage_freezes_ledger(actual):
    ledger = Ledger(Limits())
    reservation = await ledger.reserve(attempt())
    await ledger.reconcile(reservation, actual)
    assert ledger.frozen
    with pytest.raises(BudgetExceeded):
        await ledger.reserve(attempt())


@pytest.mark.parametrize(
    "changes",
    [
        {"cost_usd": Decimal("1.01")},
        {"input_tokens": 80001},
        {"output_tokens": 2001},
        {"hosted_actions": 3},
        {"tool_cap_verified": False},
    ],
)
async def test_attempt_budget_boundaries(changes):
    with pytest.raises(BudgetExceeded):
        await Ledger(Limits()).reserve(attempt(**changes))


@pytest.mark.parametrize(
    "kind,field,maximum", [("critique", "critique_attempts", 3), ("revision", "revisions", 2)]
)
async def test_critique_and_revision_attempt_caps(kind, field, maximum):
    ledger = Ledger(Limits())
    for _ in range(maximum):
        key = await ledger.reserve(attempt(kind=kind, hosted_actions=0))
        await ledger.reconcile(key, Usage())
    assert getattr(ledger.snapshot(), field) == maximum
    with pytest.raises(BudgetExceeded):
        await ledger.reserve(attempt(kind=kind, hosted_actions=0))
