from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.domain.risk import OrderRiskRequest


def _request(
    *,
    quantity: str = "100",
    price: str = "100",
    account_equity: str | None = None,
    current_exposure: str = "0",
    intraday_pnl: str | None = None,
    concentration: str | None = None,
    volatility: str | None = None,
) -> OrderRiskRequest:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    current_notional_by_instrument = {}
    if concentration is not None:
        current_notional_by_instrument[instrument_id] = Decimal(concentration)
    return OrderRiskRequest(
        instrument_id=instrument_id,
        quantity=Decimal(quantity),
        price=Decimal(price),
        multiplier=Decimal("1"),
        account_equity=Decimal(account_equity) if account_equity is not None else None,
        current_exposure=Decimal(current_exposure),
        intraday_pnl=Decimal(intraday_pnl) if intraday_pnl is not None else None,
        current_notional_by_instrument=current_notional_by_instrument,
        volatility=Decimal(volatility) if volatility is not None else None,
    )


def test_leverage_limit_rejects_projected_account_exposure_anchor() -> None:
    from qts.risk.rules.leverage_limit import LeverageLimitRule

    rule = LeverageLimitRule(max_leverage=Decimal("2"))

    rejected = rule.check(
        _request(
            quantity="600",
            price="100",
            account_equity="100000",
            current_exposure="150000",
        )
    )
    approved = rule.check(
        _request(
            quantity="400",
            price="100",
            account_equity="100000",
            current_exposure="150000",
        )
    )

    assert rejected.reason_code == "LEVERAGE_LIMIT_EXCEEDED"
    assert rejected.evidence["projected_leverage"] == Decimal("2.1")
    assert approved.approved is True


def test_intraday_loss_limit_rejects_when_realized_loss_exceeds_cap() -> None:
    from qts.risk.rules.intraday_loss_limit import IntradayLossLimitRule

    rule = IntradayLossLimitRule(max_loss=Decimal("5000"))

    rejected = rule.check(_request(intraday_pnl="-5001"))

    assert rejected.reason_code == "INTRADAY_LOSS_LIMIT_EXCEEDED"
    assert rejected.evidence["intraday_pnl"] == Decimal("-5001")


def test_concentration_limit_rejects_projected_single_instrument_weight() -> None:
    from qts.risk.rules.concentration_limit import ConcentrationLimitRule

    rule = ConcentrationLimitRule(max_fraction=Decimal("0.50"))

    rejected = rule.check(
        _request(
            quantity="250",
            price="100",
            account_equity="100000",
            concentration="30000",
        )
    )

    assert rejected.reason_code == "CONCENTRATION_LIMIT_EXCEEDED"
    assert rejected.evidence["projected_fraction"] == Decimal("0.55")


def test_volatility_adjusted_sizing_rejects_notional_above_volatility_cap() -> None:
    from qts.risk.rules.volatility_adjusted_sizing import VolatilityAdjustedSizingRule

    rule = VolatilityAdjustedSizingRule(max_notional_per_volatility=Decimal("1000"))

    rejected = rule.check(_request(quantity="120", price="100", volatility="0.10"))
    approved = rule.check(_request(quantity="100", price="100", volatility="0.10"))

    assert rejected.reason_code == "VOLATILITY_ADJUSTED_SIZE_EXCEEDED"
    assert rejected.evidence["max_notional"] == Decimal("1.000E+4")
    assert approved.approved is True


def test_standard_five_risk_rules_build_from_registry_in_declared_order() -> None:
    from qts.risk import RiskRuleConfig, RiskRuleRegistry

    rules = RiskRuleRegistry().build_all(
        (
            RiskRuleConfig("risk-position", "position_limit", {"max_position": Decimal("1000")}),
            RiskRuleConfig("risk-leverage", "leverage_limit", {"max_leverage": Decimal("2")}),
            RiskRuleConfig("risk-loss", "intraday_loss_limit", {"max_loss": Decimal("5000")}),
            RiskRuleConfig("risk-conc", "concentration_limit", {"max_fraction": Decimal("0.50")}),
            RiskRuleConfig(
                "risk-vol",
                "volatility_adjusted_sizing",
                {"max_notional_per_volatility": Decimal("1000")},
            ),
        )
    )

    assert [type(rule).__name__ for rule in rules] == [
        "PositionLimitRule",
        "LeverageLimitRule",
        "IntradayLossLimitRule",
        "ConcentrationLimitRule",
        "VolatilityAdjustedSizingRule",
    ]


def test_risk_engine_runs_registry_built_rules_in_declared_order() -> None:
    from qts.risk import RiskEngine, RiskRuleConfig, RiskRuleRegistry

    rules = RiskRuleRegistry().build_all(
        (
            RiskRuleConfig("risk-loss", "intraday_loss_limit", {"max_loss": Decimal("5000")}),
            RiskRuleConfig("risk-position", "position_limit", {"max_position": Decimal("10")}),
        )
    )

    decision = RiskEngine(rules).check(_request(quantity="20", price="100", intraday_pnl="-6000"))

    assert decision.reason_code == "INTRADAY_LOSS_LIMIT_EXCEEDED"


def test_risk_config_loads_yaml_rules_in_declared_order(tmp_path: Path) -> None:
    from qts.risk import RiskConfig

    path = tmp_path / "risk.yaml"
    path.write_text(
        """
account_id: acct-001
max_notional: "100000"
max_leverage: "2"
rules:
  - rule_id: risk-position
    name: position_limit
    params:
      max_position: "1000"
  - rule_id: risk-leverage
    name: leverage_limit
    params:
      max_leverage: "2"
""",
        encoding="utf-8",
    )

    config = RiskConfig.from_yaml(path)

    assert [rule.name for rule in config.rules] == ["position_limit", "leverage_limit"]
    assert config.rules[0].params["max_position"] == Decimal("1000")
