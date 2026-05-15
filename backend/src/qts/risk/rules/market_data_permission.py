"""Market-data permission risk rule."""

from __future__ import annotations

from qts.domain.risk import OrderRiskRequest, RiskDecision


class MarketDataPermissionRiskRule:
    """Require live market-data permission before broker-capable order submission."""

    rule_id = "market_data_permission"

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Reject orders when market-data permission is not live."""
        context = request.market_data
        if context is None or context.permission_state is None:
            return RiskDecision.rejected(
                "MARKET_DATA_PERMISSION_UNKNOWN",
                "market-data permission state is unknown",
                rule_id=self.rule_id,
                evidence={"market_data": {} if context is None else context.evidence_payload()},
                contributing_strategy_ids=request.contributing_strategy_ids,
            )

        permission_state = context.permission_state
        if permission_state == "live":
            return RiskDecision.approve(
                rule_id=self.rule_id,
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        if permission_state in {"delayed", "delayed_frozen"}:
            return RiskDecision.rejected(
                "MARKET_DATA_DELAYED_FOR_LIVE_ORDER",
                "delayed market data cannot support live order submission",
                rule_id=self.rule_id,
                evidence={"market_data": context.evidence_payload()},
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        if permission_state == "frozen":
            return RiskDecision.rejected(
                "MARKET_DATA_FROZEN_FOR_LIVE_ORDER",
                "frozen market data cannot support live order submission",
                rule_id=self.rule_id,
                evidence={"market_data": context.evidence_payload()},
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        if permission_state == "unavailable":
            return RiskDecision.rejected(
                "MARKET_DATA_UNAVAILABLE",
                "market data is unavailable",
                rule_id=self.rule_id,
                evidence={"market_data": context.evidence_payload()},
                contributing_strategy_ids=request.contributing_strategy_ids,
            )
        return RiskDecision.rejected(
            "MARKET_DATA_PERMISSION_UNKNOWN",
            "market-data permission state is unknown",
            rule_id=self.rule_id,
            evidence={"market_data": context.evidence_payload()},
            contributing_strategy_ids=request.contributing_strategy_ids,
        )


__all__ = ["MarketDataPermissionRiskRule"]
