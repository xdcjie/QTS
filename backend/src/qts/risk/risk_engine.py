"""Risk engine."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Protocol

from qts.domain.orders import OrderType
from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.risk.rule import RiskRule
from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule
from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule
from qts.risk.rules.order_spec_validity import OrderSpecValidityRule


class BrokerageRiskPolicy(Protocol):
    """Brokerage assumptions needed by risk without importing execution models."""

    @property
    def requires_live_market_data(self) -> bool:
        """Return whether broker-capable orders require live market data."""
        ...

    @property
    def supported_order_types(self) -> frozenset[OrderType]:
        """Return the set of order types the active brokerage accepts."""
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
        """Return a risk engine configured from brokerage-model risk requirements.

        Injects the brokerage's ``supported_order_types`` into any
        ``OrderSpecValidityRule`` so unsupported order types are rejected at
        risk time rather than crashing inside the adapter.
        """
        rules = tuple(self._with_brokerage_rules(brokerage_model))
        engine: RiskEngine = RiskEngine(
            rules,
            require_live_market_data=self._require_live_market_data,
        )
        if brokerage_model.requires_live_market_data:
            return engine.requiring_live_market_data()
        return engine

    def _with_brokerage_rules(
        self,
        brokerage_model: BrokerageRiskPolicy,
    ) -> Iterable[RiskRule]:
        """Yield rules with order-spec validity bound to the brokerage policy."""
        for rule in self._rules:
            if isinstance(rule, OrderSpecValidityRule):
                yield replace(rule, brokerage_policy=brokerage_model)
            else:
                yield rule

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
