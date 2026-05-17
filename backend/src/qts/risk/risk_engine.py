"""Risk engine."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.risk.rule import RiskRule
from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule
from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule


class BrokerageRiskPolicy(Protocol):
    """Brokerage assumptions needed by risk without importing execution models."""

    @property
    def requires_live_market_data(self) -> bool:
        """Return whether broker-capable orders require live market data."""
        ...


class RiskEngine:
    """Apply risk rules in order and return the first rejection."""

    def __init__(
        self,
        rules: Iterable[RiskRule],
        *,
        require_live_market_data: bool = False,
    ) -> None:
        """Perform __init__."""
        self._rules = tuple(rules)
        self._require_live_market_data = require_live_market_data

    def requiring_live_market_data(self) -> RiskEngine:
        """Return a risk engine that force-checks live market-data safety first."""
        if self._require_live_market_data:
            return self
        return RiskEngine(self._rules, require_live_market_data=True)

    def with_brokerage_model(self, brokerage_model: BrokerageRiskPolicy) -> RiskEngine:
        """Return a risk engine configured from brokerage-model risk requirements."""
        if brokerage_model.requires_live_market_data:
            return self.requiring_live_market_data()
        return self

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        """Perform check."""
        if self._require_live_market_data:
            live_market_data_rules: tuple[RiskRule, ...] = (
                MarketDataPermissionRiskRule(),
                MarketDataFreshnessRiskRule(),
            )
            for rule in live_market_data_rules:
                decision = rule.check(request)
                if not decision.approved:
                    return decision
        for rule in self._rules:
            decision = rule.check(request)
            if not decision.approved:
                return decision
        return RiskDecision.approve()


__all__ = ["BrokerageRiskPolicy", "RiskEngine"]
