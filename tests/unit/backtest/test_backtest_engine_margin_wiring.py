"""The config-driven engine includes MarginRule only when a margin rate exists.

These tests lock the registry-driven risk-rule construction in
``BacktestEngine.from_config``: ``MaxNotionalRule`` is always present, and the
per-contract margin gate (``MarginRule``) is appended when a futures margin rate
is resolvable from the instrument registry. Futures without a configured rate
fail closed instead of silently disabling margin risk.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from qts.backtest.risk_policy import BacktestMarginPolicyResolver, BacktestRiskPolicyFactory
from qts.core.ids import InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, FutureSpec, Instrument, SettlementType
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


def _future_registry(*, margin_rate: Decimal | None) -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register(
        "GC",
        Instrument(
            instrument_id=InstrumentId("FUTURE.CME.GC.GCM6"),
            asset_class=AssetClass.FUTURE,
            exchange="CME",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.1"),
                lot_size=Decimal("1"),
                multiplier=Decimal("100"),
                settlement=SettlementType.CASH,
                calendar_id="CMES",
                initial_margin_rate=margin_rate,
            ),
            derivative=FutureSpec(
                expiry=date(2026, 6, 26),
                underlying=InstrumentId("FUTURE_ROOT.CME.GC"),
                root_symbol="GC",
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


def test_futures_without_configured_margin_rate_fail_closed() -> None:
    with pytest.raises(ValueError, match="missing initial_margin_rate"):
        BacktestMarginPolicyResolver().resolve_initial_margin_rate(
            _future_registry(margin_rate=None)
        )


def test_resolved_rate_returns_the_single_configured_rate() -> None:
    registry = _future_registry(margin_rate=Decimal("0.05"))
    assert BacktestMarginPolicyResolver().resolve_initial_margin_rate(registry) == Decimal("0.05")


def test_resolved_rate_rejects_conflicting_rates() -> None:
    registry = _registry(Decimal("0.05"), Decimal("0.10"))
    with pytest.raises(ValueError, match="single rate"):
        BacktestMarginPolicyResolver().resolve_initial_margin_rate(registry)
