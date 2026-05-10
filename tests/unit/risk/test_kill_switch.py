from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

from qts.core.ids import AccountId, BrokerId, InstrumentId, StrategyId
from qts.domain.risk import OrderRiskRequest
from qts.risk.kill_switch import KillSwitchRegistry, KillSwitchScope


def test_kill_switch_rejects_only_matching_scope_with_explicit_reason_code() -> None:
    registry = KillSwitchRegistry()
    registry.activate(KillSwitchScope.account(AccountId("acct-a")), reason="operator halt")

    rejected = registry.check_order(
        OrderRiskRequest(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            quantity=Decimal("1"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
        ),
        account_id=AccountId("acct-a"),
        strategy_id=StrategyId("strat-a"),
        broker_id=BrokerId("broker-a"),
    )
    approved = registry.check_order(
        OrderRiskRequest(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
            quantity=Decimal("1"),
            price=Decimal("100"),
            multiplier=Decimal("1"),
        ),
        account_id=AccountId("acct-b"),
        strategy_id=StrategyId("strat-a"),
        broker_id=BrokerId("broker-a"),
    )

    assert rejected.reason_code == "KILL_SWITCH_ACCOUNT"
    assert approved.approved


def test_kill_switch_registry_keeps_scope_matching_inside_the_registry() -> None:
    tree = ast.parse(Path("backend/src/qts/risk/kill_switch.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_matching_scopes" not in private_functions
