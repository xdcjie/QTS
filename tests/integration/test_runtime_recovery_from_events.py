from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import cast

from qts.core.ids import CorrelationId, EventId, InstrumentId, OrderId
from qts.domain.events import BaseEvent
from qts.execution.order_manager import OrderIntent, OrderManager, OrderSide
from qts.portfolio.cash_book import CashBook
from qts.portfolio.position_book import PositionBook
from qts.runtime.event_store import InMemoryEventStore


def test_replayed_events_reconstruct_expected_order_sequence() -> None:
    correlation_id = CorrelationId("corr-bar-fill-001")
    store = InMemoryEventStore()
    events = (
        BaseEvent(
            event_id=EventId("evt-001"),
            event_type="order.sent",
            event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            source="OrderManagerActor",
            partition_key="ord-001",
            correlation_id=correlation_id,
        ),
        BaseEvent(
            event_id=EventId("evt-002"),
            event_type="execution.fill",
            event_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            source="ExecutionActor",
            partition_key="ord-001",
            correlation_id=correlation_id,
        ),
    )
    store.append_many(events)

    replayed = cast(tuple[BaseEvent, ...], store.replay(partition_key="ord-001"))

    assert [event.event_type for event in replayed] == ["order.sent", "execution.fill"]
    assert store.by_correlation_id(correlation_id) == events


def test_replayed_events_reconstruct_order_and_position_state() -> None:
    """Replayed events reconstruct expected order and position state."""
    instrument_id = InstrumentId("AAPL")
    order_id = OrderId("ord-001")
    correlation_id = CorrelationId("corr-recovery-001")

    # Step 1: Record events from a live flow
    store = InMemoryEventStore()
    store.append(
        BaseEvent(
            event_id=EventId("evt-001"),
            event_type="order.created",
            event_time=datetime(2026, 1, 2, 14, 30, 0, tzinfo=UTC),
            source="OrderManagerActor",
            partition_key=order_id.value,
            correlation_id=correlation_id,
        ),
    )
    store.append(
        BaseEvent(
            event_id=EventId("evt-002"),
            event_type="order.sent",
            event_time=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            source="OrderManagerActor",
            partition_key=order_id.value,
            correlation_id=correlation_id,
        ),
    )
    store.append(
        BaseEvent(
            event_id=EventId("evt-003"),
            event_type="execution.fill",
            event_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            source="ExecutionActor",
            partition_key=order_id.value,
            correlation_id=correlation_id,
        ),
    )

    # Step 2: Replay events and reconstruct order state
    from qts.domain.risk import RiskDecision
    from qts.execution.order_state_machine import OrderEvent, OrderState

    event_type_to_order_event = {
        "order.created": None,
        "order.sent": OrderEvent.SENT,
        "execution.fill": OrderEvent.FILLED,
    }

    replayed = cast(tuple[BaseEvent, ...], store.replay(partition_key=order_id.value))
    manager = OrderManager()
    intent = OrderIntent(
        order_id=order_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("10"),
    )
    manager.create_order(intent, risk_decision=RiskDecision.approve())

    for event in replayed:
        order_event = event_type_to_order_event.get(event.event_type)
        if order_event is not None:
            if order_event is OrderEvent.SENT:
                manager.mark_sent(order_id, broker_order_id="broker-001")
            elif order_event is OrderEvent.FILLED:
                from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus

                report = ExecutionReport(
                    report_id="rpt-001",
                    broker_order_id="broker-001",
                    status=ExecutionReportStatus.FILLED,
                    filled_quantity=Decimal("10"),
                    fill_price=Decimal("150.00"),
                    fill_id="fill-001",
                )
                result = manager.process_report(report)

                # Step 3: Reconstruct position state from fills
                positions = PositionBook()
                cash = CashBook({"USD": Decimal("100000")})
                for fill in result.fills:
                    signed_qty = fill.quantity if fill.side is OrderSide.BUY else -fill.quantity
                    positions.apply_delta(fill.instrument_id, signed_qty)
                    cash.apply_delta("USD", -signed_qty * fill.price * Decimal("1"))

                assert positions.quantity(instrument_id) == Decimal("10")
                assert cash.balance("USD") == Decimal("98500")

    order = manager.get_order(order_id)
    assert order.state is OrderState.FILLED
