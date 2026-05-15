"""Market-data freshness risk rule."""

from __future__ import annotations

from qts.domain.risk import OrderRiskRequest, RiskDecision


class MarketDataFreshnessRiskRule:
    """Reject orders when the latest market-data source is stale."""

    rule_id = "market_data_freshness"

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject stale market-data contexts."""
        context = request.market_data
        if context is not None and context.stale:
            return RiskDecision.rejected(
                "MARKET_DATA_STALE",
                "market data is stale",
                rule_id=self.rule_id,
                evidence={"market_data": context.evidence_payload()},
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.approve(
            rule_id=self.rule_id,
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["MarketDataFreshnessRiskRule"]
