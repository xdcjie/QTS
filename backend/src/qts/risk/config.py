"""Risk configuration schemas."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


@dataclass(frozen=True, slots=True)
class RiskRuleConfig:
    """One configured risk rule."""

    rule_id: str
    name: str
    params: dict[str, Decimal]

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.rule_id.strip():
            raise ValueError("rule_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> RiskRuleConfig:
        """Create a rule config from a YAML-decoded mapping."""
        params_payload = payload.get("params", {})
        if not isinstance(params_payload, Mapping):
            raise ValueError("risk rule params must be a mapping")
        return cls(
            rule_id=str(payload["rule_id"]),
            name=str(payload["name"]),
            params={str(name): Decimal(str(value)) for name, value in params_payload.items()},
        )


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Account/strategy/product risk configuration."""

    account_id: str
    max_notional: Decimal
    max_leverage: Decimal
    rules: tuple[RiskRuleConfig, ...] = ()
    product_rules: dict[str, tuple[RiskRuleConfig, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if self.max_notional <= Decimal("0"):
            raise ValueError("max_notional must be positive")
        if self.max_leverage <= Decimal("0"):
            raise ValueError("max_leverage must be positive")

    @classmethod
    def from_yaml(cls, path: str | Path) -> RiskConfig:
        """Load risk configuration from a YAML file."""
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(payload, Mapping):
            raise ValueError("risk config YAML must contain a mapping")
        rules_payload = payload.get("rules", ())
        if not isinstance(rules_payload, list | tuple):
            raise ValueError("risk config rules must be a list")
        return cls(
            account_id=str(payload["account_id"]),
            max_notional=Decimal(str(payload["max_notional"])),
            max_leverage=Decimal(str(payload["max_leverage"])),
            rules=tuple(
                RiskRuleConfig.from_mapping(rule_payload)
                for rule_payload in rules_payload
                if isinstance(rule_payload, Mapping)
            ),
            product_rules=cls._product_rules_from_payload(payload.get("product_rules", {})),
        )

    @staticmethod
    def _product_rules_from_payload(payload: object) -> dict[str, tuple[RiskRuleConfig, ...]]:
        if not payload:
            return {}
        if not isinstance(payload, Mapping):
            raise ValueError("product_rules must be a mapping")
        result: dict[str, tuple[RiskRuleConfig, ...]] = {}
        for product, rules_payload in payload.items():
            if not isinstance(rules_payload, list | tuple):
                raise ValueError("product rule entries must be lists")
            result[str(product)] = tuple(
                RiskRuleConfig.from_mapping(rule_payload)
                for rule_payload in rules_payload
                if isinstance(rule_payload, Mapping)
            )
        return result


__all__ = ["RiskConfig", "RiskRuleConfig"]
