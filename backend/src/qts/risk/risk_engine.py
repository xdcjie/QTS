"""Risk engine."""

from __future__ import annotations

from collections.abc import Iterable

from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.risk.rule import RiskRule


class RiskEngine:
    """Apply risk rules in order and return the first rejection."""

    def __init__(self, rules: Iterable[RiskRule]) -> None:
        self._rules = tuple(rules)

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        for rule in self._rules:
            decision = rule.check(request)
            if not decision.approved:
                return decision
        return RiskDecision.approve()


__all__ = ["RiskEngine"]
