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


def test_order_state_machine_handles_cancel_replace_and_late_fill_paths() -> None:
    from qts.execution.order_state_machine import OrderEvent, OrderState, OrderStateMachine

    replace_machine = OrderStateMachine()
    replace_machine.apply(OrderEvent.SENT)
    replace_machine.apply(OrderEvent.ACCEPTED)

    assert replace_machine.apply(OrderEvent.REPLACE_REQUESTED) is OrderState.REPLACE_REQUESTED
    assert replace_machine.apply(OrderEvent.ACCEPTED) is OrderState.ACCEPTED

    cancel_machine = OrderStateMachine()
    cancel_machine.apply(OrderEvent.SENT)
    cancel_machine.apply(OrderEvent.ACCEPTED)
    cancel_machine.apply(OrderEvent.CANCEL_REQUESTED)
    cancel_machine.apply(OrderEvent.CANCELLED)

    assert cancel_machine.apply(OrderEvent.PARTIALLY_FILLED) is OrderState.PARTIALLY_FILLED
