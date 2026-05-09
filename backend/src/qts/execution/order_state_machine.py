"""Order lifecycle state machine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OrderState(StrEnum):
    """Internal order lifecycle states."""

    CREATED = "created"
    SENT = "sent"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderEvent(StrEnum):
    """Order lifecycle transition inputs."""

    SENT = "sent"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderTransitionError(ValueError):
    """Raised when an order transition is invalid."""


_TRANSITIONS: dict[OrderState, dict[OrderEvent, OrderState]] = {
    OrderState.CREATED: {
        OrderEvent.SENT: OrderState.SENT,
        OrderEvent.REJECTED: OrderState.REJECTED,
    },
    OrderState.SENT: {
        OrderEvent.ACCEPTED: OrderState.ACCEPTED,
        OrderEvent.PARTIALLY_FILLED: OrderState.PARTIALLY_FILLED,
        OrderEvent.FILLED: OrderState.FILLED,
        OrderEvent.REJECTED: OrderState.REJECTED,
        OrderEvent.CANCEL_REQUESTED: OrderState.CANCEL_REQUESTED,
    },
    OrderState.ACCEPTED: {
        OrderEvent.PARTIALLY_FILLED: OrderState.PARTIALLY_FILLED,
        OrderEvent.FILLED: OrderState.FILLED,
        OrderEvent.CANCEL_REQUESTED: OrderState.CANCEL_REQUESTED,
        OrderEvent.CANCELLED: OrderState.CANCELLED,
        OrderEvent.REJECTED: OrderState.REJECTED,
    },
    OrderState.PARTIALLY_FILLED: {
        OrderEvent.PARTIALLY_FILLED: OrderState.PARTIALLY_FILLED,
        OrderEvent.FILLED: OrderState.FILLED,
        OrderEvent.CANCEL_REQUESTED: OrderState.CANCEL_REQUESTED,
        OrderEvent.CANCELLED: OrderState.CANCELLED,
    },
    OrderState.CANCEL_REQUESTED: {
        OrderEvent.CANCELLED: OrderState.CANCELLED,
        OrderEvent.FILLED: OrderState.FILLED,
        OrderEvent.PARTIALLY_FILLED: OrderState.PARTIALLY_FILLED,
    },
}

_DUPLICATE_TERMINAL_EVENTS = {
    OrderState.FILLED: OrderEvent.FILLED,
    OrderState.CANCELLED: OrderEvent.CANCELLED,
    OrderState.REJECTED: OrderEvent.REJECTED,
}


@dataclass(slots=True)
class OrderStateMachine:
    """Validate and apply order lifecycle transitions."""

    state: OrderState = OrderState.CREATED

    def apply(self, event: OrderEvent) -> OrderState:
        if _DUPLICATE_TERMINAL_EVENTS.get(self.state) is event:
            return self.state
        next_state = _TRANSITIONS.get(self.state, {}).get(event)
        if next_state is None:
            raise OrderTransitionError(f"invalid order transition: {self.state} -> {event}")
        self.state = next_state
        return self.state


__all__ = ["OrderEvent", "OrderState", "OrderStateMachine", "OrderTransitionError"]
