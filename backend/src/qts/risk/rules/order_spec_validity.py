"""Risk rule validating order specification shape."""

from __future__ import annotations

from qts.domain.risk import OrderRiskRequest, RiskDecision


class OrderSpecValidityRule:
    """Reject invalid order spec combinations before order submission."""

    rule_id = "order_spec_validity"

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Validate the request order spec."""
        try:
            request.order_spec._validate_shape()
        except ValueError as exc:
            return RiskDecision.rejected(
                "INVALID_ORDER_SPEC",
                str(exc),
                rule_id=self.rule_id,
                evidence=request.order_spec.to_payload(),
            )
        return RiskDecision.approve(rule_id=self.rule_id)


__all__ = ["OrderSpecValidityRule"]
