"""Market-data freshness risk rule."""

from __future__ import annotations

from dataclasses import dataclass

from qts.domain.risk import OrderRiskRequest, RiskDecision


@dataclass(frozen=True, slots=True)
class MarketDataFreshnessRiskRule:
    """Reject orders when the latest market-data source is stale.

    In live-required mode (``require_market_data_context=True``) the rule fails
    CLOSED: a missing market-data context is itself a rejection, matching the
    permission rule's fail-closed stance. When the flag is False (backtest /
    research), a missing context is allowed and only an explicitly stale context
    is rejected.
    """

    require_market_data_context: bool = False
    rule_id = "market_data_freshness"

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject stale (and, in live-required mode, missing) market-data contexts."""
        context = request.market_data
        if context is None:
            if self.require_market_data_context:
                return RiskDecision.rejected(
                    "MARKET_DATA_CONTEXT_REQUIRED",
                    "market-data context is required for live order submission",
                    rule_id=self.rule_id,
                    evidence={"market_data": {}},
                    contributing_strategy_ids=request.contributing_strategy_ids,
                )
            return RiskDecision.approve(
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        if context.stale:
            return RiskDecision.rejected(
                "MARKET_DATA_STALE",
                "market data is stale",
                rule_id=self.rule_id,
                evidence={"market_data": context.evidence_payload()},
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            evidence={"market_data": context.evidence_payload()},
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["MarketDataFreshnessRiskRule"]
