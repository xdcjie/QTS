import ast
from decimal import Decimal
from pathlib import Path

import pytest
from qts.risk.config import RiskConfig, RiskRuleConfig, RiskRuleName
from qts.risk.rule_registry import RiskRuleRegistry


def test_risk_config_supports_account_and_product_rules() -> None:
    rule = RiskRuleConfig(
        rule_id="rule-001",
        name=RiskRuleName.MAX_NOTIONAL,
        params={"max_notional": Decimal("100000")},
    )
    config = RiskConfig(
        account_id="acct-001",
        max_notional=Decimal("100000"),
        max_leverage=Decimal("2"),
        rules=(rule,),
        product_rules={"future": (rule,)},
    )

    assert config.rules == (rule,)
    assert config.product_rules["future"] == (rule,)


def test_risk_rule_registry_builds_rules_and_rejects_unknown_names() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.risk import OrderRiskRequest

    registry = RiskRuleRegistry()
    rule = registry.build(
        RiskRuleConfig(
            rule_id="rule-001",
            name=RiskRuleName.MAX_NOTIONAL,
            params={"max_notional": Decimal("100")},
        )
    )

    assert not rule.check(
        OrderRiskRequest(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            quantity=Decimal("2"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
        )
    ).approved
    # Unknown rule names are now caught at config construction (ValueError)
    # instead of registry dispatch (KeyError) -- a type-safety improvement.
    with pytest.raises(ValueError, match="unknown"):
        RiskRuleConfig(rule_id="rule-002", name="unknown", params={})  # type: ignore[arg-type]
    # Verify the config.name field holds the typed enum after string coercion.
    config = RiskRuleConfig(
        rule_id="rule-003", name=RiskRuleName.MAX_NOTIONAL, params={"max_notional": Decimal("50")}
    )
    assert config.name is RiskRuleName.MAX_NOTIONAL


def test_risk_rule_registry_builds_market_data_rules() -> None:
    from qts.risk.rules.market_data_freshness import MarketDataFreshnessRiskRule
    from qts.risk.rules.market_data_permission import MarketDataPermissionRiskRule

    registry = RiskRuleRegistry()

    assert isinstance(
        registry.build(
            RiskRuleConfig(
                rule_id="rule-md-permission", name=RiskRuleName.MARKET_DATA_PERMISSION, params={}
            )
        ),
        MarketDataPermissionRiskRule,
    )
    assert isinstance(
        registry.build(
            RiskRuleConfig(
                rule_id="rule-md-freshness", name=RiskRuleName.MARKET_DATA_FRESHNESS, params={}
            )
        ),
        MarketDataFreshnessRiskRule,
    )


def test_risk_rule_registry_builds_rules_in_declared_order() -> None:
    rules = RiskRuleRegistry().build_all(
        (
            RiskRuleConfig(
                rule_id="rule-position",
                name=RiskRuleName.POSITION_LIMIT,
                params={"max_position": Decimal("100")},
            ),
            RiskRuleConfig(
                rule_id="rule-notional",
                name=RiskRuleName.MAX_NOTIONAL,
                params={"max_notional": Decimal("1000")},
            ),
        )
    )

    assert [type(rule).__name__ for rule in rules] == ["PositionLimitRule", "MaxNotionalRule"]


def test_risk_rule_registry_keeps_param_lookup_inside_the_registry() -> None:
    tree = ast.parse(Path("backend/src/qts/risk/rule_registry.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_param" not in private_functions
