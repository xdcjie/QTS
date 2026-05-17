"""Account leverage limit risk rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class LeverageLimitRule:
    """Reject orders whose projected gross exposure exceeds account leverage."""

    max_leverage: Decimal
    rule_id = "leverage_limit"

    def __post_init__(self) -> None:
        """Validate configured leverage cap."""
        if self.max_leverage <= Decimal("0"):
            raise ValueError("max_leverage must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders that would exceed the configured leverage limit."""
        if request.account_equity is None:
            return RiskDecision.rejected(
                "ACCOUNT_EQUITY_REQUIRED",
                "account_equity is required for leverage risk",
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        projected_exposure = request.current_exposure + request.notional
        projected_leverage = projected_exposure / request.account_equity
        evidence = {
            "account_equity": request.account_equity,
            "current_exposure": request.current_exposure,
            "order_notional": request.notional,
            "projected_exposure": projected_exposure,
            "projected_leverage": projected_leverage,
            "max_leverage": self.max_leverage,
        }
        if projected_leverage > self.max_leverage:
            return RiskDecision.rejected(
                "LEVERAGE_LIMIT_EXCEEDED",
                f"projected leverage {projected_leverage} exceeds max {self.max_leverage}",
                rule_id=self.rule_id,
                evidence=evidence,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            evidence=evidence,
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["LeverageLimitRule"]
