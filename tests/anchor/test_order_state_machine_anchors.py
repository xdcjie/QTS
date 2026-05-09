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
