"""Risk rule protocol."""

from __future__ import annotations

from typing import Protocol

from qts.domain.risk import OrderRiskRequest, RiskDecision


class RiskRule(Protocol):
    """A pre-trade risk rule."""

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Return an explicit risk decision."""


__all__ = ["RiskRule"]
