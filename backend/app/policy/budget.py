import asyncio

from app.domain.models import Attempt, Budget, Limits, Usage


class BudgetExceeded(Exception):
    pass


class Ledger:
    """Reservations count paid attempts; unknown outcomes are never refunded."""

    def __init__(self, limits: Limits) -> None:
        self.limits = limits
        self.lock = asyncio.Lock()
        self.model_requests = 0
        self.research_requests = 0
        self.critique_attempts = 0
        self.revisions = 0
        self.usage = Usage()
        self.pending: dict[int, Attempt] = {}
        self.frozen = False

    def snapshot(self) -> Budget:
        return Budget(
            model_requests=self.model_requests,
            research_requests=self.research_requests,
            critique_attempts=self.critique_attempts,
            revisions=self.revisions,
            usage=self.usage,
            limits=self.limits,
            frozen=self.frozen,
        )

    async def reserve(self, attempt: Attempt) -> int:
        async with self.lock:
            if self.frozen or self.pending:
                raise BudgetExceeded("unreconciled or frozen ledger")
            if attempt.kind == "research" and (not attempt.tool_cap_verified or attempt.hosted_actions > 2):
                raise BudgetExceeded("hosted tool cap is unverified or excessive")
            if attempt.kind != "research" and attempt.hosted_actions:
                raise BudgetExceeded("only research may use hosted tools")
            usage = Usage(
                input_tokens=self.usage.input_tokens + attempt.input_tokens,
                output_tokens=self.usage.output_tokens + attempt.output_tokens,
                hosted_actions=self.usage.hosted_actions + attempt.hosted_actions,
                cost_usd=self.usage.cost_usd + attempt.cost_usd,
            )
            if (
                self.model_requests >= self.limits.model_requests
                or self.research_requests + (attempt.kind == "research") > self.limits.research_requests
                or self.critique_attempts + (attempt.kind == "critique") > self.limits.critique_attempts
                or self.revisions + (attempt.kind == "revision") > self.limits.revisions
                or attempt.output_tokens > self.limits.output_per_request
                or any(getattr(usage, k) > getattr(self.limits, k) for k in Usage.model_fields)
            ):
                raise BudgetExceeded("attempt exceeds limits")
            self.model_requests += 1
            self.research_requests += attempt.kind == "research"
            self.critique_attempts += attempt.kind == "critique"
            self.revisions += attempt.kind == "revision"
            self.usage = usage
            self.pending[self.model_requests] = attempt
            return self.model_requests

    async def reconcile(self, reservation: int, actual: Usage | None) -> None:
        async with self.lock:
            attempt = self.pending.pop(reservation)
            if actual is None:
                self.frozen = True
                return
            exceeded = any(getattr(actual, k) > getattr(attempt, k) for k in Usage.model_fields)
            self.usage = Usage(
                **{
                    k: getattr(self.usage, k) - getattr(attempt, k) + getattr(actual, k)
                    for k in Usage.model_fields
                }
            )
            self.frozen = exceeded


def enforce_ceilings(limits: Limits, ceilings: Limits) -> None:
    if any(getattr(limits, key) > getattr(ceilings, key) for key in Limits.model_fields):
        raise BudgetExceeded("client limits exceed server ceilings")
