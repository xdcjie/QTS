from __future__ import annotations

from decimal import Decimal


def test_execution_report_handler_returns_validated_fills() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent, OrderSide
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderManager
    from qts.runtime.execution_report_handler import ExecutionReportHandler

    instrument_id = InstrumentId("FUT.CME.GC.202606")
    order_manager = OrderManager()
    order_manager.create_order(
        OrderIntent(
            order_id=OrderId("ord-001"),
            account_id=AccountId("acct-a"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("2"),
        ),
        risk_decision=RiskDecision.approve(),
    )
    order_manager.mark_sent(OrderId("ord-001"), broker_order_id="broker-001")
    handler = ExecutionReportHandler(
        order_manager=order_manager,
        account_id=AccountId("acct-a"),
    )

    fills = handler.handle(
        ExecutionReport(
            report_id="rpt-001",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("2"),
            fill_price=Decimal("2300"),
            fill_id="fill-001",
        )
    )

    assert len(fills) == 1
    assert fills[0].quantity == Decimal("2")
    assert fills[0].price == Decimal("2300")


def test_execution_report_handler_quarantines_unresolved_reports() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent, OrderSide
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderManager
    from qts.runtime.execution_report_handler import ExecutionReportHandler

    instrument_id = InstrumentId("FUT.CME.GC.202606")
    order_manager = OrderManager()
    order_manager.create_order(
        OrderIntent(
            order_id=OrderId("ord-001"),
            account_id=AccountId("acct-a"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("2"),
        ),
        risk_decision=RiskDecision.approve(),
    )
    order_manager.mark_sent(OrderId("ord-001"), broker_order_id="broker-001")
    handler = ExecutionReportHandler(
        order_manager=order_manager,
        account_id=AccountId("acct-a"),
    )

    fills = handler.handle(
        ExecutionReport(
            report_id="rpt-unknown",
            broker_order_id="broker-999",
            status=ExecutionReportStatus.ACCEPTED,
        )
    )

    assert fills == ()
    assert len(handler.quarantined_reports) == 1
    assert handler.quarantined_reports[0].broker_order_id == "broker-999"


def test_execution_report_handler_quarantines_cross_account_fills() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent, OrderSide
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderManager
    from qts.runtime.execution_report_handler import ExecutionReportHandler

    instrument_id = InstrumentId("FUT.CME.GC.202606")
    order_manager = OrderManager()
    order_manager.create_order(
        OrderIntent(
            order_id=OrderId("ord-001"),
            account_id=AccountId("acct-a"),
            instrument_id=instrument_id,
            side=OrderSide.BUY,
            quantity=Decimal("2"),
        ),
        risk_decision=RiskDecision.approve(),
    )
    order_manager.mark_sent(OrderId("ord-001"), broker_order_id="broker-001")
    handler = ExecutionReportHandler(
        order_manager=order_manager,
        account_id=AccountId("acct-b"),
    )

    fills = handler.handle(
        ExecutionReport(
            report_id="rpt-cross-account",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("2"),
            fill_price=Decimal("2300"),
            fill_id="fill-001",
        )
    )

    assert fills == ()
    assert handler.quarantined_reports == (
        ExecutionReport(
            report_id="rpt-cross-account",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.FILLED,
            filled_quantity=Decimal("2"),
            fill_price=Decimal("2300"),
            fill_id="fill-001",
        ),
    )


def test_execution_report_handler_does_not_import_apply_fill_or_account_actor() -> None:
    """ExecutionReportHandler must not reference ApplyFill or AccountActor."""
    import inspect

    from qts.runtime.execution_report_handler import ExecutionReportHandler

    source = inspect.getsource(ExecutionReportHandler)
    assert "ApplyFill" not in source
    assert "AccountActor" not in source
    assert "account_ref" not in source
