"""Risk configuration schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RiskRuleConfig:
    """One configured risk rule."""

    rule_id: str
    name: str
    params: dict[str, Decimal]

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Account/strategy/product risk configuration."""

    account_id: str
    max_notional: Decimal
    max_leverage: Decimal
    rules: tuple[RiskRuleConfig, ...] = ()
    product_rules: dict[str, tuple[RiskRuleConfig, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if self.max_notional <= Decimal("0"):
            raise ValueError("max_notional must be positive")
        if self.max_leverage <= Decimal("0"):
            raise ValueError("max_leverage must be positive")


__all__ = ["RiskConfig", "RiskRuleConfig"]
