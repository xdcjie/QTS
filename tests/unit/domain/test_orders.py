from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import (
    BrokerOrderType,
    CancelIntent,
    ExecutionReport,
    ExecutionReportStatus,
    Order,
    OrderFill,
    OrderIntent,
    OrderSide,
    OrderState,
)


def test_order_domain_value_objects_are_importable_from_domain() -> None:
    intent = OrderIntent(
        order_id=OrderId("ord-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )
    order = Order(
        order_id=OrderId("ord-001"),
        intent=intent,
        state=OrderState.CREATED,
    )
    fill = OrderFill(
        fill_id="fill-001",
        order_id=order.order_id,
        instrument_id=order.intent.instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("101.25"),
    )
    report = ExecutionReport(
        report_id="rpt-001",
        broker_order_id="broker-001",
        status=ExecutionReportStatus.FILLED,
    )

    assert intent.order_id == OrderId("ord-001")
    assert order.state is OrderState.CREATED
    assert report.status == ExecutionReportStatus.FILLED
    assert fill.order_id == order.order_id


def test_order_type_is_canonical_and_broker_order_type_is_compatibility_alias() -> None:
    from qts.domain.orders import OrderType

    assert BrokerOrderType is OrderType


def test_order_intent_keeps_positive_quantity() -> None:
    intent = OrderIntent(
        order_id=OrderId("ord-002"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        side=OrderSide.SELL,
        quantity=Decimal("1"),
    )
    cancel = CancelIntent(order_id=intent.order_id)

    assert intent.quantity == Decimal("1")
    assert cancel.order_id == intent.order_id


def test_order_intent_requires_positive_quantity() -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        OrderIntent(
            order_id=OrderId("ord-003"),
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            side=OrderSide.BUY,
            quantity=Decimal("0"),
        )


def test_execution_report_validates_identifiers() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        ExecutionReport(
            report_id="   ",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.FILLED,
        )
