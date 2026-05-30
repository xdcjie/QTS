"""Risk package — lazy imports to break circular dependency with qts.runtime."""

from __future__ import annotations

_RISK_SUBMODULES = {
    "KillSwitchRegistry": "qts.risk.kill_switch",
    "KillSwitchScope": "qts.risk.kill_switch",
    "KillSwitchState": "qts.risk.kill_switch",
    "RiskConfig": "qts.risk.config",
    "RiskEngine": "qts.risk.risk_engine",
    "RiskRule": "qts.risk.rule",
    "RiskRuleConfig": "qts.risk.config",
    "RiskRuleName": "qts.risk.config",
    "RiskRuleRegistry": "qts.risk.rule_registry",
    "RiskStateSnapshot": "qts.risk.risk_state",
    "MarginCalculator": "qts.risk.margin",
    "MarginRequirement": "qts.risk.margin",
    "MarginRule": "qts.risk.rules.margin_limit",
    "IntradayPnlCalculator": "qts.risk.intraday_pnl",
}


def __getattr__(name: str) -> object:
    """Lazy-import public names to avoid circular import with qts.runtime."""
    module_path = _RISK_SUBMODULES.get(name)
    if module_path is None:
        raise AttributeError(f"module 'qts.risk' has no attribute {name}")
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, name)


__all__ = [
    "IntradayPnlCalculator",
    "KillSwitchRegistry",
    "KillSwitchScope",
    "KillSwitchState",
    "MarginCalculator",
    "MarginRequirement",
    "MarginRule",
    "RiskConfig",
    "RiskEngine",
    "RiskRule",
    "RiskRuleConfig",
    "RiskRuleName",
    "RiskRuleRegistry",
    "RiskStateSnapshot",
]
