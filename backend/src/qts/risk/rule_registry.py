"""Construct risk rules from configuration."""

from __future__ import annotations

from decimal import Decimal

from qts.risk.config import RiskRuleConfig
from qts.risk.rule import RiskRule
from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule
from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.risk.rules.max_order_qty import MaxOrderQuantityRule
from qts.risk.rules.position_limit import PositionLimitRule


class RiskRuleRegistry:
    """Map configured rule names to executable risk rules."""

    def build(self, config: RiskRuleConfig) -> RiskRule:
        """Perform build."""
        if config.name == "position_limit":
            return PositionLimitRule(max_position=self._param(config, "max_position"))
        if config.name == "max_notional":
            return MaxNotionalRule(max_notional=self._param(config, "max_notional"))
        if config.name == "max_order_quantity":
            return MaxOrderQuantityRule(max_quantity=self._param(config, "max_quantity"))
        if config.name == "market_data_permission":
            return MarketDataPermissionRiskRule()
        if config.name == "market_data_freshness":
            return MarketDataFreshnessRiskRule()
        raise KeyError(f"unknown risk rule: {config.name}")

    def build_all(self, configs: tuple[RiskRuleConfig, ...]) -> tuple[RiskRule, ...]:
        """Build all configured rules in declared order."""
        return tuple(self.build(config) for config in configs)

    @staticmethod
    def _param(config: RiskRuleConfig, name: str) -> Decimal:
        """Perform _param."""
        try:
            return config.params[name]
        except KeyError as exc:
            raise KeyError(f"missing risk rule param: {name}") from exc


__all__ = ["RiskRuleRegistry"]
