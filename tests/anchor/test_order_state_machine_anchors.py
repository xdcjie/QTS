from __future__ import annotations

import pytest


def test_filled_order_cannot_be_cancelled_later() -> None:
    from qts.execution.order_state_machine import (
        OrderEvent,
        OrderStateMachine,
        OrderTransitionError,
    )

    machine = OrderStateMachine()
    machine.apply(OrderEvent.SENT)
    machine.apply(OrderEvent.ACCEPTED)
    machine.apply(OrderEvent.FILLED)

    with pytest.raises(OrderTransitionError):
        machine.apply(OrderEvent.CANCELLED)


def test_cancelled_order_can_record_late_fill_without_invalid_state() -> None:
    from qts.execution.order_state_machine import OrderEvent, OrderState, OrderStateMachine

    machine = OrderStateMachine()
    machine.apply(OrderEvent.SENT)
    machine.apply(OrderEvent.ACCEPTED)
    machine.apply(OrderEvent.CANCEL_REQUESTED)
    machine.apply(OrderEvent.CANCELLED)

    assert machine.apply(OrderEvent.FILLED) is OrderState.FILLED
