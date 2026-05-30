"""Risk rule validating order specification shape and brokerage acceptance.

Owner of the OrderSpec acceptance contract at the risk boundary. Combines
two checks:

1. **Shape**: ``OrderSpec._validate_shape`` ensures price fields match the
   order type (e.g. LIMIT requires limit_price, BRACKET requires legs).
2. **Brokerage acceptance**: when a ``BrokerageOrderTypePolicy`` is wired
   in, the rule rejects any order_type not in the policy's
   ``supported_order_types``. This keeps backtest/live parity (no adapter
   crash on unsupported types — the rejection is a risk decision).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from qts.domain.orders import OrderSide, OrderType
from qts.domain.risk import OrderRiskRequest, RiskDecision


class BrokerageOrderTypePolicy(Protocol):
    """Brokerage-acceptance subset consulted by the validity rule."""

    @property
    def supported_order_types(self) -> frozenset[OrderType]:
        """Return the set of order types the active brokerage accepts."""
        ...


@dataclass(frozen=True, slots=True)
class OrderSpecValidityRule:
    """Reject invalid order spec combinations before order submission."""

    rule_id: str = "order_spec_validity"
    brokerage_policy: BrokerageOrderTypePolicy | None = None

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Validate the request order spec against shape and acceptance."""
        spec = request.order_spec
        try:
            spec._validate_shape()
        except ValueError as exc:
            return RiskDecision.rejected(
                "INVALID_ORDER_SPEC",
                str(exc),
                rule_id=self.rule_id,
                evidence=spec.to_payload(),
            )
        bracket_reason = self._validate_bracket(request)
        if bracket_reason is not None:
            return RiskDecision.rejected(
                "INVALID_BRACKET_LEGS",
                bracket_reason,
                rule_id=self.rule_id,
                evidence=spec.to_payload(),
            )
        policy = self.brokerage_policy
        if policy is not None and spec.order_type not in policy.supported_order_types:
            return RiskDecision.rejected(
                "UNSUPPORTED_ORDER_TYPE",
                f"order type {spec.order_type.value} is not supported by the active brokerage",
                rule_id=self.rule_id,
                evidence=spec.to_payload(),
            )
        return RiskDecision.approve(rule_id=self.rule_id)

    @staticmethod
    def _validate_bracket(request: OrderRiskRequest) -> str | None:
        """Validate bracket exit legs against the parent intent direction/size.

        Bracket child legs are OCO exits: they must share one side (you exit a
        position in a single direction), each cover the full parent quantity, and
        face the opposite direction of the parent. The parent direction is read
        from ``signed_quantity_delta`` when available (positive opens long, so
        exits sell; negative opens short, so exits buy).
        """
        bracket = request.order_spec.bracket
        if bracket is None:
            return None
        sides = {leg.side for leg in bracket.legs}
        if len(sides) > 1:
            return "bracket exit legs must share a single side (OCO exits one direction)"
        exit_side = next(iter(sides))
        for leg in bracket.legs:
            if leg.quantity != request.quantity:
                return (
                    f"bracket leg quantity {leg.quantity} must equal parent quantity "
                    f"{request.quantity}"
                )
        delta = request.signed_quantity_delta
        if delta is not None:
            expected = OrderSide.SELL if delta > Decimal("0") else OrderSide.BUY
            if exit_side is not expected:
                direction = "long" if delta > Decimal("0") else "short"
                return (
                    f"bracket exit side {exit_side.value} must be {expected.value} "
                    f"for a {direction} parent intent"
                )
        return None


__all__ = ["BrokerageOrderTypePolicy", "OrderSpecValidityRule"]
