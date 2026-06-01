"""Risk package — lazy imports to break circular dependency with qts.runtime."""

from __future__ import annotations


def __getattr__(name: str) -> object:
    """Lazy-import public names to avoid circular import with qts.runtime."""
    if name == "IntradayPnlCalculator":
        from qts.risk.intraday_pnl import IntradayPnlCalculator

        return IntradayPnlCalculator
    if name == "KillSwitchRegistry":
        from qts.risk.kill_switch import KillSwitchRegistry

        return KillSwitchRegistry
    if name == "KillSwitchScope":
        from qts.risk.kill_switch import KillSwitchScope

        return KillSwitchScope
    if name == "KillSwitchState":
        from qts.risk.kill_switch import KillSwitchState

        return KillSwitchState
    if name == "MarginCalculator":
        from qts.risk.margin import MarginCalculator

        return MarginCalculator
    if name == "MarginRequirement":
        from qts.risk.margin import MarginRequirement

        return MarginRequirement
    if name == "MarginRule":
        from qts.risk.rules.margin_limit import MarginRule

        return MarginRule
    if name == "RiskConfig":
        from qts.risk.config import RiskConfig

        return RiskConfig
    if name == "RiskEngine":
        from qts.risk.risk_engine import RiskEngine

        return RiskEngine
    if name == "RiskRule":
        from qts.risk.rule import RiskRule

        return RiskRule
    if name == "RiskRuleConfig":
        from qts.risk.config import RiskRuleConfig

        return RiskRuleConfig
    if name == "RiskRuleName":
        from qts.risk.config import RiskRuleName

        return RiskRuleName
    if name == "RiskRuleRegistry":
        from qts.risk.rule_registry import RiskRuleRegistry

        return RiskRuleRegistry
    if name == "RiskStateSnapshot":
        from qts.risk.risk_state import RiskStateSnapshot

        return RiskStateSnapshot
    raise AttributeError(f"module 'qts.risk' has no attribute {name}")


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
