"""Maximum order quantity rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class MaxOrderQuantityRule:
    """Reject orders whose absolute quantity exceeds a fixed limit."""

    max_quantity: Decimal
    rule_id = "max_order_quantity"

    def __post_init__(self) -> None:
        """Require a positive maximum order quantity."""
        if self.max_quantity <= Decimal("0"):
            raise ValueError("max_quantity must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject the order if its quantity exceeds the configured maximum."""
        if request.quantity > self.max_quantity:
            return RiskDecision.rejected(
                "MAX_ORDER_QTY_EXCEEDED",
                f"order quantity {request.quantity} exceeds max {self.max_quantity}",
                rule_id=self.rule_id,
            )
        return RiskDecision.approve(rule_id=self.rule_id)


__all__ = ["MaxOrderQuantityRule"]
