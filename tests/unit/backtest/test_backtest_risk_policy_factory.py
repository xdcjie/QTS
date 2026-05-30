"""QTS-FINAL-002: BacktestRiskPolicyFactory owns risk/margin rule construction."""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.backtest.risk_policy import BacktestMarginPolicyResolver, BacktestRiskPolicyFactory
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.config import RiskRuleName


def test_risk_rule_configs_without_margin_is_max_notional_only() -> None:
    configs = BacktestRiskPolicyFactory.risk_rule_configs(
        max_notional=Decimal("1000"), margin_enabled=False
    )
    assert [c.name for c in configs] == [RiskRuleName.MAX_NOTIONAL]
    assert configs[0].params == {"max_notional": Decimal("1000")}


def test_risk_rule_configs_with_margin_appends_margin_limit() -> None:
    configs = BacktestRiskPolicyFactory.risk_rule_configs(
        max_notional=Decimal("1000"), margin_enabled=True
    )
    assert [c.name for c in configs] == [RiskRuleName.MAX_NOTIONAL, RiskRuleName.MARGIN_LIMIT]


def test_build_without_registry_has_no_margin_calculator() -> None:
    risk_engine, margin_calculator = BacktestRiskPolicyFactory().build(
        max_notional=Decimal("1000"), instrument_registry=None
    )
    assert risk_engine is not None
    assert margin_calculator is None


def test_resolver_returns_none_when_no_rate_configured() -> None:
    resolver = BacktestMarginPolicyResolver()
    assert resolver.resolve_initial_margin_rate(InstrumentRegistry()) is None
    assert resolver.margin_calculator(None) is None


def test_resolver_builds_calculator_for_a_rate() -> None:
    resolver = BacktestMarginPolicyResolver()
    calc = resolver.margin_calculator(Decimal("0.1"))
    assert calc is not None


def test_engine_no_longer_owns_risk_rule_helpers() -> None:
    from qts.backtest.engine import BacktestEngine

    assert not hasattr(BacktestEngine, "_risk_rule_configs")
    assert not hasattr(BacktestEngine, "_resolved_initial_margin_rate")


def test_resolver_rejects_conflicting_rates(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Spec:
        def __init__(self, rate: Decimal) -> None:
            self.initial_margin_rate = rate

    class _Registry:
        def contract_specs(self) -> list[_Spec]:
            return [_Spec(Decimal("0.1")), _Spec(Decimal("0.2"))]

    resolver = BacktestMarginPolicyResolver()
    with pytest.raises(ValueError, match="single rate"):
        resolver.resolve_initial_margin_rate(_Registry())  # type: ignore[arg-type]
