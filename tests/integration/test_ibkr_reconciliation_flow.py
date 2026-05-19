from __future__ import annotations

from decimal import Decimal


def test_order_manager_snapshot_reconciles_pending_order_after_reconnect() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.orders import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderSide,
    )
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderManager
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
    manager.mark_sent(order.order_id, broker_order_id="ibkr-001")
    restored = OrderManager.restore(manager.snapshot())

    report = ExecutionReport(
        report_id="rpt-001",
        broker_order_id="ibkr-001",
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("10"),
        fill_price=Decimal("101.25"),
        fill_id="fill-001",
    )
    first = restored.process_report(report)
    duplicate = restored.process_report(report)

    assert restored.get_order(order.order_id).state is OrderState.FILLED
    assert first.fills[0].order_id == order.order_id
    assert duplicate.fills == ()
