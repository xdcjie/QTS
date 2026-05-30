"""QTS-FINAL-008: OrderManager public boundary raises domain errors, not built-ins."""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.errors import QTSError
from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
)
from qts.domain.risk import RiskDecision
from qts.execution.errors import (
    MissingFillPrice,
    OrderLifecycleError,
    RiskRejectedOrder,
    UnknownBrokerOrder,
)
from qts.execution.order_manager import OrderManager


def _intent(order_id: str = "ord-001") -> OrderIntent:
    return OrderIntent(
        order_id=OrderId(order_id),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )


def test_execution_errors_are_qts_errors() -> None:
    for error in (RiskRejectedOrder, OrderLifecycleError, UnknownBrokerOrder, MissingFillPrice):
        assert issubclass(error, QTSError)


def test_create_order_rejects_unapproved_risk_with_domain_error() -> None:
    manager = OrderManager()
    with pytest.raises(RiskRejectedOrder):
        manager.create_order(_intent(), risk_decision=RiskDecision.rejected("BLOCKED", "no"))


def test_mark_sent_requires_broker_order_id() -> None:
    manager = OrderManager()
    manager.create_order(_intent(), risk_decision=RiskDecision.approve())
    with pytest.raises(OrderLifecycleError):
        manager.mark_sent(OrderId("ord-001"), broker_order_id="  ")


def test_process_report_for_unknown_broker_order_raises_domain_error() -> None:
    manager = OrderManager()
    with pytest.raises(UnknownBrokerOrder):
        manager.process_report(
            ExecutionReport(
                report_id="rpt-x",
                broker_order_id="broker-unknown",
                status=ExecutionReportStatus.ACCEPTED,
            )
        )


def test_fill_report_without_price_raises_missing_fill_price() -> None:
    manager = OrderManager()
    manager.create_order(_intent(), risk_decision=RiskDecision.approve())
    manager.mark_sent(OrderId("ord-001"), broker_order_id="broker-001")
    with pytest.raises(MissingFillPrice):
        manager.process_report(
            ExecutionReport(
                report_id="rpt-1",
                broker_order_id="broker-001",
                status=ExecutionReportStatus.FILLED,
                filled_quantity=Decimal("10"),
                fill_price=None,
                fill_id="fill-1",
            )
        )


def test_discard_non_terminal_order_raises_lifecycle_error() -> None:
    manager = OrderManager()
    manager.create_order(_intent(), risk_decision=RiskDecision.approve())
    with pytest.raises(OrderLifecycleError):
        manager.discard_terminal_order(OrderId("ord-001"))
