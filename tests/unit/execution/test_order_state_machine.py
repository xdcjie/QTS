from __future__ import annotations

import pytest


def test_order_state_machine_accepts_valid_lifecycle() -> None:
    from qts.execution.order_state_machine import OrderEvent, OrderState, OrderStateMachine

    machine = OrderStateMachine()

    assert machine.state is OrderState.CREATED
    assert machine.apply(OrderEvent.SENT) is OrderState.SENT
    assert machine.apply(OrderEvent.ACCEPTED) is OrderState.ACCEPTED
    assert machine.apply(OrderEvent.PARTIALLY_FILLED) is OrderState.PARTIALLY_FILLED
    assert machine.apply(OrderEvent.FILLED) is OrderState.FILLED


def test_order_state_machine_rejects_invalid_transition() -> None:
    from qts.execution.order_state_machine import (
        OrderEvent,
        OrderStateMachine,
        OrderTransitionError,
    )

    machine = OrderStateMachine()

    with pytest.raises(OrderTransitionError, match="invalid order transition"):
        machine.apply(OrderEvent.FILLED)


def test_duplicate_terminal_broker_report_does_not_corrupt_state() -> None:
    from qts.execution.order_state_machine import OrderEvent, OrderState, OrderStateMachine

    machine = OrderStateMachine()
    machine.apply(OrderEvent.SENT)
    machine.apply(OrderEvent.ACCEPTED)
    machine.apply(OrderEvent.FILLED)

    assert machine.apply(OrderEvent.FILLED) is OrderState.FILLED
