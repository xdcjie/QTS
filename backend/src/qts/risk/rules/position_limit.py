"""Position limit risk rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class PositionLimitRule:
    """Reject orders that would exceed an absolute position limit."""

    max_position: Decimal
    rule_id = "position_limit"

    def __post_init__(self) -> None:
        """Validate the configured absolute position limit."""
        if self.max_position <= Decimal("0"):
            raise ValueError("max_position must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders whose projected absolute position exceeds the limit.

        When the request carries a signed quantity delta (buy positive, sell
        negative) the projection is computed against the *net* post-trade
        position ``abs(current_position + signed_quantity_delta)``, so a
        risk-reducing order (e.g. short 10 then buy 5 -> projected 5) is never
        blocked by an absolute position limit. Without a signed delta the rule
        falls back to the conservative worst-case ``abs(current) + quantity``.
        """
        if request.signed_quantity_delta is not None:
            projected_position = abs(request.current_position + request.signed_quantity_delta)
        else:
            projected_position = abs(request.current_position) + request.quantity
        if projected_position > self.max_position:
            return RiskDecision.rejected(
                "POSITION_LIMIT_EXCEEDED",
                f"projected position {projected_position} exceeds max {self.max_position}",
                rule_id=self.rule_id,
                evidence={
                    "current_position": request.current_position,
                    "order_quantity": request.quantity,
                    "projected_position": projected_position,
                    "max_position": self.max_position,
                },
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            contributing_strategy_ids=request.contributing_strategy_ids,
            evidence={
                "current_position": request.current_position,
                "order_quantity": request.quantity,
                "projected_position": projected_position,
                "max_position": self.max_position,
            },
        )


__all__ = ["PositionLimitRule"]
