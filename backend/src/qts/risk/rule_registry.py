"""Construct risk rules from configuration."""

from __future__ import annotations

from decimal import Decimal

from qts.risk.config import RiskRuleConfig
from qts.risk.rule import RiskRule
from qts.risk.rules.concentration_limit import ConcentrationLimitRule
from qts.risk.rules.intraday_loss_limit import IntradayLossLimitRule
from qts.risk.rules.leverage_limit import LeverageLimitRule
from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule
from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.risk.rules.max_order_qty import MaxOrderQuantityRule
from qts.risk.rules.order_spec_validity import OrderSpecValidityRule
from qts.risk.rules.position_limit import PositionLimitRule
from qts.risk.rules.volatility_adjusted_sizing import VolatilityAdjustedSizingRule


class RiskRuleRegistry:
    """Map configured rule names to executable risk rules."""

    def build(self, config: RiskRuleConfig) -> RiskRule:
        """Perform build."""
        if config.name == "position_limit":
            return PositionLimitRule(max_position=self._param(config, "max_position"))
        if config.name == "leverage_limit":
            return LeverageLimitRule(max_leverage=self._param(config, "max_leverage"))
        if config.name == "intraday_loss_limit":
            return IntradayLossLimitRule(max_loss=self._param(config, "max_loss"))
        if config.name == "concentration_limit":
            return ConcentrationLimitRule(max_fraction=self._param(config, "max_fraction"))
        if config.name == "volatility_adjusted_sizing":
            return VolatilityAdjustedSizingRule(
                max_notional_per_volatility=self._param(
                    config,
                    "max_notional_per_volatility",
                )
            )
        if config.name == "max_notional":
            return MaxNotionalRule(max_notional=self._param(config, "max_notional"))
        if config.name == "max_order_quantity":
            return MaxOrderQuantityRule(max_quantity=self._param(config, "max_quantity"))
        if config.name == "market_data_permission":
            return MarketDataPermissionRiskRule()
        if config.name == "market_data_freshness":
            return MarketDataFreshnessRiskRule()
        if config.name == "order_spec_validity":
            return OrderSpecValidityRule()
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
