"""Instrument concentration limit risk rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class ConcentrationLimitRule:
    """Reject orders whose projected instrument notional exceeds account weight."""

    max_fraction: Decimal
    rule_id = "concentration_limit"

    def __post_init__(self) -> None:
        """Validate configured concentration fraction."""
        if self.max_fraction <= Decimal("0") or self.max_fraction > Decimal("1"):
            raise ValueError("max_fraction must be in (0, 1]")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders that would over-concentrate one instrument."""
        if request.account_equity is None:
            return RiskDecision.rejected(
                "ACCOUNT_EQUITY_REQUIRED",
                "account_equity is required for concentration risk",
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        current_by_instrument = request.current_notional_by_instrument or {}
        current_notional = current_by_instrument.get(request.instrument_id, Decimal("0"))
        projected_notional = current_notional + request.notional
        projected_fraction = projected_notional / request.account_equity
        evidence = {
            "account_equity": request.account_equity,
            "current_instrument_notional": current_notional,
            "order_notional": request.notional,
            "projected_instrument_notional": projected_notional,
            "projected_fraction": projected_fraction,
            "max_fraction": self.max_fraction,
        }
        if projected_fraction > self.max_fraction:
            return RiskDecision.rejected(
                "CONCENTRATION_LIMIT_EXCEEDED",
                f"projected concentration {projected_fraction} exceeds max {self.max_fraction}",
                rule_id=self.rule_id,
                evidence=evidence,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            evidence=evidence,
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["ConcentrationLimitRule"]
