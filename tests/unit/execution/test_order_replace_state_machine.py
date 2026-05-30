"""Replace lifecycle at the OrderManager + state-machine level.

QTS-FINAL-007 makes ReplaceOrder a complete capability. These tests lock the
domain-level transitions independent of any actor/broker wiring:

- ``OrderManager.request_replace`` moves a live order to ``REPLACE_REQUESTED``
  and records the new quantity.
- A broker ``ACCEPTED`` report then drives ``REPLACE_REQUESTED -> ACCEPTED``.
- An unapproved risk decision is rejected with ``RiskRejectedOrder``.
- The raw state machine permits ``REPLACE_REQUESTED -> ACCEPTED``.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId, OrderId
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
)
from qts.domain.orders.value_objects import ReplaceIntent
from qts.domain.risk import RiskDecision
from qts.execution.errors import RiskRejectedOrder
from qts.execution.order_manager import OrderManager
from qts.execution.order_state_machine import OrderEvent, OrderState, OrderStateMachine


def _sent_order(manager: OrderManager) -> OrderId:
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
    return order.order_id


def test_request_replace_transitions_to_replace_requested_and_updates_quantity() -> None:
    manager = OrderManager()
    order_id = _sent_order(manager)

    replaced = manager.request_replace(
        ReplaceIntent(order_id=order_id, new_quantity=Decimal("25")),
        risk_decision=RiskDecision.approve(),
    )

    assert replaced.state is OrderState.REPLACE_REQUESTED
    assert replaced.intent.quantity == Decimal("25")
    assert manager.get_order(order_id).intent.quantity == Decimal("25")


def test_broker_accept_report_confirms_replace() -> None:
    manager = OrderManager()
    order_id = _sent_order(manager)
    manager.request_replace(
        ReplaceIntent(order_id=order_id, new_quantity=Decimal("25")),
        risk_decision=RiskDecision.approve(),
    )

    manager.process_report(
        ExecutionReport(
            report_id="broker-001-replace-1",
            broker_order_id="broker-001",
            status=ExecutionReportStatus.ACCEPTED,
        )
    )

    assert manager.get_order(order_id).state is OrderState.ACCEPTED


def test_request_replace_rejects_unapproved_risk_decision() -> None:
    manager = OrderManager()
    order_id = _sent_order(manager)

    with pytest.raises(RiskRejectedOrder, match="risk decision is not approved"):
        manager.request_replace(
            ReplaceIntent(order_id=order_id, new_quantity=Decimal("25")),
            risk_decision=RiskDecision.rejected("BLOCKED", "blocked by test"),
        )


def test_state_machine_allows_replace_requested_to_accepted() -> None:
    machine = OrderStateMachine(state=OrderState.SENT)
    assert machine.apply(OrderEvent.REPLACE_REQUESTED) is OrderState.REPLACE_REQUESTED
    assert machine.apply(OrderEvent.ACCEPTED) is OrderState.ACCEPTED
