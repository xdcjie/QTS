"""Intraday loss limit risk rule."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class IntradayLossLimitRule:
    """Reject new orders once account intraday loss exceeds a configured cap."""

    max_loss: Decimal
    rule_id = "intraday_loss_limit"

    def __post_init__(self) -> None:
        """Validate configured intraday loss cap."""
        if self.max_loss <= Decimal("0"):
            raise ValueError("max_loss must be positive")

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders after the configured intraday loss is breached."""
        if request.intraday_pnl is None:
            return RiskDecision.rejected(
                "INTRADAY_PNL_REQUIRED",
                "intraday_pnl is required for intraday loss risk",
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        evidence = {
            "intraday_pnl": request.intraday_pnl,
            "max_loss": self.max_loss,
        }
        if request.intraday_pnl < -self.max_loss:
            return RiskDecision.rejected(
                "INTRADAY_LOSS_LIMIT_EXCEEDED",
                f"intraday PnL {request.intraday_pnl} exceeds max loss {self.max_loss}",
                rule_id=self.rule_id,
                evidence=evidence,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            evidence=evidence,
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["IntradayLossLimitRule"]
