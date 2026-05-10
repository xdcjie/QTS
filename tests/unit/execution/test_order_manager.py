from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest


def test_order_manager_creates_order_from_approved_intent_and_tracks_state() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderIntent, OrderManager, OrderSide
    from qts.execution.order_state_machine import OrderState

    manager = OrderManager()
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    order = manager.create_order(intent, risk_decision=RiskDecision.approve())

    assert order.order_id == OrderId("ord-001")
    assert order.state is OrderState.CREATED
    assert manager.get_order(order.order_id) == order


def test_order_manager_rejects_unapproved_intent() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderIntent, OrderManager, OrderSide

    manager = OrderManager()
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )

    with pytest.raises(ValueError, match="risk decision is not approved"):
        manager.create_order(
            intent,
            risk_decision=RiskDecision.rejected("BLOCKED", "blocked by test"),
        )


def test_order_manager_processes_normalized_fill_report_once() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderManager,
        OrderSide,
    )
    from qts.execution.order_state_machine import OrderState

    manager = OrderManager()
    order = manager.create_order(
        OrderIntent(
            order_id=OrderId("ord-001"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("10"),
        ),
        risk_decision=RiskDecision.approve(),
    )
    manager.mark_sent(order.order_id, broker_order_id="broker-001")

    report = ExecutionReport(
        report_id="rpt-001",
        broker_order_id="broker-001",
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("10"),
        fill_price=Decimal("101.25"),
        fill_id="fill-001",
    )
    first = manager.process_report(report)
    second = manager.process_report(report)

    assert manager.get_order(order.order_id).state is OrderState.FILLED
    assert len(first.fills) == 1
    assert first.fills[0].instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert first.fills[0].quantity == Decimal("10")
    assert second.fills == ()


def test_order_manager_cancel_and_replace_intents_remain_manager_owned() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import (
        CancelIntent,
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderManager,
        OrderSide,
        ReplaceIntent,
    )
    from qts.execution.order_state_machine import OrderState

    manager = OrderManager()
    order = manager.create_order(
        OrderIntent(
            order_id=OrderId("ord-001"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("10"),
        ),
        risk_decision=RiskDecision.approve(),
    )
    manager.mark_sent(order.order_id, broker_order_id="broker-001")

    replaced = manager.request_replace(
        ReplaceIntent(order_id=order.order_id, new_quantity=Decimal("5")),
        risk_decision=RiskDecision.approve(),
    )
    assert replaced.state is OrderState.REPLACE_REQUESTED
    assert replaced.intent.quantity == Decimal("5")

    manager.process_report(
        ExecutionReport(
            report_id="rpt-accepted",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.ACCEPTED,
        )
    )
    cancelled = manager.request_cancel(CancelIntent(order_id=order.order_id))
    assert cancelled.state is OrderState.CANCEL_REQUESTED


def test_order_manager_keeps_report_event_mapping_inside_the_manager() -> None:
    tree = ast.parse(Path("backend/src/qts/execution/order_manager.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_event_for_report" not in private_functions
