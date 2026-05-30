"""The config-driven engine includes MarginRule only when a margin rate exists.

These tests lock the registry-driven risk-rule construction in
``BacktestEngine.from_config``: ``MaxNotionalRule`` is always present, and the
per-contract margin gate (``MarginRule``) is appended only when a margin rate is
resolvable from the instrument registry. Runs without a configured rate keep
their historical rule set (no fail-closed margin rejection).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.backtest.risk_policy import BacktestMarginPolicyResolver, BacktestRiskPolicyFactory
from qts.core.ids import InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.rule_registry import RiskRuleRegistry
from qts.risk.rules.margin_limit import MarginRule
from qts.risk.rules.max_notional import MaxNotionalRule


def _registry(*margin_rates: Decimal | None) -> InstrumentRegistry:
    registry = InstrumentRegistry()
    for index, rate in enumerate(margin_rates):
        registry.register(
            f"SYM{index}",
            Instrument(
                instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.SYM{index}"),
                asset_class=AssetClass.EQUITY,
                exchange="NASDAQ",
                currency="USD",
                contract_spec=ContractSpec(
                    tick_size=Decimal("0.01"),
                    lot_size=Decimal("1"),
                    multiplier=Decimal("1"),
                    settlement=SettlementType.CASH,
                    calendar_id="XNYS",
                    initial_margin_rate=rate,
                ),
            ),
        )
    return registry


def _built_rule_types(*, max_notional: Decimal, margin_enabled: bool) -> list[type]:
    configs = BacktestRiskPolicyFactory.risk_rule_configs(
        max_notional=max_notional,
        margin_enabled=margin_enabled,
    )
    rules = RiskRuleRegistry().build_all(configs)
    return [type(rule) for rule in rules]


def test_rule_set_excludes_margin_rule_without_configured_rate() -> None:
    types = _built_rule_types(max_notional=Decimal("100000"), margin_enabled=False)
    assert types == [MaxNotionalRule]


def test_rule_set_includes_margin_rule_with_configured_rate() -> None:
    types = _built_rule_types(max_notional=Decimal("100000"), margin_enabled=True)
    assert types == [MaxNotionalRule, MarginRule]


def test_resolved_rate_is_none_without_registry() -> None:
    assert BacktestMarginPolicyResolver().resolve_initial_margin_rate(None) is None


def test_resolved_rate_is_none_when_no_contract_configures_one() -> None:
    registry = _registry(None, None)
    assert BacktestMarginPolicyResolver().resolve_initial_margin_rate(registry) is None


def test_resolved_rate_returns_the_single_configured_rate() -> None:
    registry = _registry(None, Decimal("0.05"))
    assert BacktestMarginPolicyResolver().resolve_initial_margin_rate(registry) == Decimal("0.05")


def test_resolved_rate_rejects_conflicting_rates() -> None:
    registry = _registry(Decimal("0.05"), Decimal("0.10"))
    with pytest.raises(ValueError, match="single rate"):
        BacktestMarginPolicyResolver().resolve_initial_margin_rate(registry)
