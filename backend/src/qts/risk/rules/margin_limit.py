"""Margin limit risk rule."""

from __future__ import annotations

from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


class MarginRule:
    """Reject orders whose initial margin would not fit within available margin.

    The order's incremental initial margin (``projected_initial_margin``) must
    fit within the account's free margin headroom (``available_margin`` =
    account_equity - current_margin_requirement). This is equivalent to
    requiring post-trade total initial margin <= account equity. Risk-reducing
    orders carry non-positive incremental margin and always pass. When the rule
    is enabled but margin context is missing, it fails closed (rejects).
    """

    rule_id = "margin_limit"

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders whose projected initial margin exceeds available margin."""
        if request.projected_initial_margin is None or request.available_margin is None:
            return RiskDecision.rejected(
                "MARGIN_CONTEXT_REQUIRED",
                "projected and available margin are required for margin risk",
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        evidence = {
            "current_margin": request.current_margin_requirement or Decimal("0"),
            "projected_margin": request.projected_initial_margin,
            "available_margin": request.available_margin,
        }
        if request.projected_initial_margin > request.available_margin:
            return RiskDecision.rejected(
                "MARGIN_LIMIT_EXCEEDED",
                (
                    f"projected initial margin {request.projected_initial_margin} "
                    f"exceeds available margin {request.available_margin}"
                ),
                rule_id=self.rule_id,
                evidence=evidence,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            evidence=evidence,
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["MarginRule"]
