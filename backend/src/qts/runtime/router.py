"""Event router for actor message delivery by partition key."""

from __future__ import annotations

from qts.runtime.actor_ref import ActorRef


class RouteNotFoundError(KeyError):
    """Raised when no actor route exists for a partition key."""


class EventRouter:
    """Route messages to actor refs by a configured message attribute."""

    def __init__(self, *, partition_attr: str) -> None:
        if not partition_attr.strip():
            raise ValueError("partition_attr must not be empty")
        self._partition_attr = partition_attr
        self._routes: dict[object, ActorRef] = {}

    def register(self, key: object, actor_ref: ActorRef) -> None:
        self._routes[key] = actor_ref

    def route(self, message: object) -> None:
        key = getattr(message, self._partition_attr)
        try:
            actor_ref = self._routes[key]
        except KeyError as exc:
            raise RouteNotFoundError(f"no route for key: {key}") from exc
        actor_ref.tell(message)


__all__ = ["EventRouter", "RouteNotFoundError"]
