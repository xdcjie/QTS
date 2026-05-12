"""Maximum order quantity rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class MaxOrderQuantityRule:
    """Reject orders whose absolute quantity exceeds a fixed limit."""

    max_quantity: Decimal

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if self.max_quantity <= Decimal("0"):
            raise ValueError("max_quantity must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Perform check."""
        if request.quantity > self.max_quantity:
            return RiskDecision.rejected(
                "MAX_ORDER_QTY_EXCEEDED",
                f"order quantity {request.quantity} exceeds max {self.max_quantity}",
            )
        return RiskDecision.approve()


__all__ = ["MaxOrderQuantityRule"]
