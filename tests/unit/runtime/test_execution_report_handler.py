from __future__ import annotations

from decimal import Decimal


def test_execution_report_handler_routes_validated_fills_to_account_actor() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderManager,
        OrderSide,
    )
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.account_actor import ApplyFill
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.mailbox import Mailbox

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
    account_mailbox = Mailbox()
    handler = ExecutionReportHandler(
        order_manager=order_manager,
        account_ref=ActorRef(mailbox=account_mailbox),
        multiplier_by_instrument={instrument_id: Decimal("100")},
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
    fill_message = account_mailbox.get()
    assert isinstance(fill_message, ApplyFill)
    assert fill_message.fill == fills[0]
    assert fill_message.currency == "USD"
    assert fill_message.multiplier == Decimal("100")


def test_execution_report_handler_quarantines_unresolved_reports() -> None:
    from qts.core.ids import AccountId, InstrumentId, OrderId
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderManager,
        OrderSide,
    )
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.mailbox import Mailbox

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
        account_ref=ActorRef(mailbox=Mailbox()),
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
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import (
        ExecutionReport,
        ExecutionReportStatus,
        OrderIntent,
        OrderManager,
        OrderSide,
    )
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.execution_report_handler import ExecutionReportHandler
    from qts.runtime.mailbox import Mailbox

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
    account_mailbox = Mailbox()
    handler = ExecutionReportHandler(
        order_manager=order_manager,
        account_ref=ActorRef(mailbox=account_mailbox),
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
    assert account_mailbox.empty()
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
