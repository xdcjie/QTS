"""Construct risk rules from configuration."""

from __future__ import annotations

from decimal import Decimal

from qts.risk.config import RiskRuleConfig
from qts.risk.rule import RiskRule
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.risk.rules.max_order_qty import MaxOrderQuantityRule


class RiskRuleRegistry:
    """Map configured rule names to executable risk rules."""

    def build(self, config: RiskRuleConfig) -> RiskRule:
        if config.name == "max_notional":
            return MaxNotionalRule(max_notional=_param(config, "max_notional"))
        if config.name == "max_order_quantity":
            return MaxOrderQuantityRule(max_quantity=_param(config, "max_quantity"))
        raise KeyError(f"unknown risk rule: {config.name}")


def _param(config: RiskRuleConfig, name: str) -> Decimal:
    try:
        return config.params[name]
    except KeyError as exc:
        raise KeyError(f"missing risk rule param: {name}") from exc


__all__ = ["RiskRuleRegistry"]
