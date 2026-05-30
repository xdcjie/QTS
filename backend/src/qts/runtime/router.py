"""Event router for actor message delivery by partition key."""

from __future__ import annotations

from collections.abc import Callable, Hashable

from qts.runtime.actor_ref import ActorRef


class RouteNotFoundError(KeyError):
    """Raised when no actor route exists for a partition key."""


class EventRouter:
    """Route messages to actor refs by a message-derived key."""

    def __init__(self, *, key_for: Callable[[object], Hashable]) -> None:
        """Initialize the router with a function that derives a partition key from a message."""
        if not callable(key_for):
            raise TypeError("key_for must be callable")
        self._key_for = key_for
        self._routes: dict[object, ActorRef] = {}

    def register(self, key: object, actor_ref: ActorRef) -> None:
        """Map a partition key to the actor ref that should receive its messages."""
        self._routes[key] = actor_ref

    def route(self, message: object) -> None:
        """Deliver a message to the actor registered for its derived key."""
        key = self._key_for(message)
        try:
            actor_ref = self._routes[key]
        except KeyError as exc:
            raise RouteNotFoundError(f"no route for key: {key}") from exc
        actor_ref.tell(message)


__all__ = ["EventRouter", "RouteNotFoundError"]
