"""Maximum order notional rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class MaxNotionalRule:
    """Reject orders whose notional exceeds a fixed limit."""

    max_notional: Decimal
    rule_id = "max_notional"

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.max_notional <= Decimal("0"):
            raise ValueError("max_notional must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Perform check."""
        if request.notional > self.max_notional:
            return RiskDecision.rejected(
                "MAX_NOTIONAL_EXCEEDED",
                f"order notional {request.notional} exceeds max {self.max_notional}",
                rule_id=self.rule_id,
            )
        return RiskDecision.approve(rule_id=self.rule_id)


__all__ = ["MaxNotionalRule"]
