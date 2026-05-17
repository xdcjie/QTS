"""Volatility-adjusted order sizing risk rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class VolatilityAdjustedSizingRule:
    """Reject orders above a notional cap scaled by current volatility."""

    max_notional_per_volatility: Decimal
    rule_id = "volatility_adjusted_sizing"

    def __post_init__(self) -> None:
        """Validate configured volatility-adjusted cap."""
        if self.max_notional_per_volatility <= Decimal("0"):
            raise ValueError("max_notional_per_volatility must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders whose notional exceeds the volatility-adjusted cap."""
        if request.volatility is None:
            return RiskDecision.rejected(
                "VOLATILITY_REQUIRED",
                "volatility is required for volatility-adjusted sizing risk",
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        max_notional = (
            self.max_notional_per_volatility
            if request.volatility == Decimal("0")
            else self.max_notional_per_volatility / request.volatility
        )
        evidence = {
            "order_notional": request.notional,
            "volatility": request.volatility,
            "max_notional": max_notional,
            "max_notional_per_volatility": self.max_notional_per_volatility,
        }
        if request.notional > max_notional:
            return RiskDecision.rejected(
                "VOLATILITY_ADJUSTED_SIZE_EXCEEDED",
                f"order notional {request.notional} exceeds volatility-adjusted max {max_notional}",
                rule_id=self.rule_id,
                evidence=evidence,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            evidence=evidence,
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["VolatilityAdjustedSizingRule"]
