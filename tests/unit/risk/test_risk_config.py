from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest


def test_risk_config_supports_account_and_product_rules() -> None:
    from qts.risk import RiskConfig, RiskRuleConfig

    rule = RiskRuleConfig(
        rule_id="rule-001",
        name="max_notional",
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
    from qts.risk import RiskRuleConfig, RiskRuleRegistry

    registry = RiskRuleRegistry()
    rule = registry.build(
        RiskRuleConfig(
            rule_id="rule-001",
            name="max_notional",
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
    with pytest.raises(KeyError, match="unknown risk rule"):
        registry.build(RiskRuleConfig(rule_id="rule-002", name="unknown", params={}))


def test_risk_rule_registry_keeps_param_lookup_inside_the_registry() -> None:
    tree = ast.parse(Path("backend/src/qts/risk/rule_registry.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_param" not in private_functions
