"""Minimal actor supervisor for failure handling and observability."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from logging import getLogger

from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_path import ActorPath
from qts.runtime.actor_ref import ActorRef

logger = getLogger(__name__)


class SupervisorDecision(Enum):
    """Decision taken by the supervisor on actor failure."""

    LOG = auto()
    STOP = auto()
    RESTART = auto()


class ActorSupervisor:
    """Minimal supervisor that registers actors and handles failure events.

    The supervisor receives :class:`ActorFailureEvent` via its
    :meth:`handle_failure` method (typically wired as a ``failure_sink``
    on :class:`ActorRef`).  For now the supervisor logs the failure and
    records the actor as failed.  Restart policy is reserved for a future
    milestone.
    """

    def __init__(
        self,
        *,
        on_failure: Callable[[ActorFailureEvent], None] | None = None,
    ) -> None:
        self._registered: dict[ActorPath, ActorRef] = {}
        self._failed_paths: set[ActorPath] = set()
        self._failure_events: list[ActorFailureEvent] = []
        self._on_failure = on_failure

    def supervise(self, actor_ref: ActorRef, *, path: ActorPath) -> None:
        """Register an actor for supervision.

        The supervisor stores a mapping from path to ActorRef so that
        future restart policies can re-wire the actor.  The ActorRef
        should also have this supervisor (or a callback wrapping it) set
        as its ``failure_sink``.
        """
        self._registered[path] = actor_ref

    def handle_failure(self, event: ActorFailureEvent) -> None:
        """Decide what to do on actor failure.

        Current behaviour: log the failure, mark the actor as failed,
        and call any user-provided ``on_failure`` callback.  Restart
        policy will be added in a future milestone.
        """
        logger.error(
            "actor failure: %s %s: %s (recoverable=%s)",
            event.actor_name,
            event.exception_type,
            event.exception_message,
            event.recoverable,
        )
        self._failure_events.append(event)
        # Try to find the path matching this actor name for failed-paths tracking.
        matching_path = self._find_path_by_name(event.actor_name)
        if matching_path is not None:
            self._failed_paths.add(matching_path)
        if self._on_failure is not None:
            self._on_failure(event)

    @property
    def failure_events(self) -> tuple[ActorFailureEvent, ...]:
        """Return all recorded failure events."""
        return tuple(self._failure_events)

    @property
    def failed_paths(self) -> frozenset[ActorPath]:
        """Return paths of actors that have experienced failures."""
        return frozenset(self._failed_paths)

    def is_failed(self, path: ActorPath) -> bool:
        """Check whether a supervised actor has experienced a failure."""
        return path in self._failed_paths

    def _find_path_by_name(self, actor_name: str) -> ActorPath | None:
        """Find a registered path matching the actor name string."""
        for path in self._registered:
            if str(path) == actor_name:
                return path
        return None


__all__ = ["ActorSupervisor", "SupervisorDecision"]
