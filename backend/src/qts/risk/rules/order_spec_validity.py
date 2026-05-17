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
from typing import Protocol

from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.execution.broker import BrokerOrderType


class BrokerageOrderTypePolicy(Protocol):
    """Brokerage-acceptance subset consulted by the validity rule."""

    @property
    def supported_order_types(self) -> frozenset[BrokerOrderType]:
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
        policy = self.brokerage_policy
        if policy is not None and spec.order_type not in policy.supported_order_types:
            return RiskDecision.rejected(
                "UNSUPPORTED_ORDER_TYPE",
                f"order type {spec.order_type.value} is not supported by the active brokerage",
                rule_id=self.rule_id,
                evidence=spec.to_payload(),
            )
        return RiskDecision.approve(rule_id=self.rule_id)


__all__ = ["BrokerageOrderTypePolicy", "OrderSpecValidityRule"]
