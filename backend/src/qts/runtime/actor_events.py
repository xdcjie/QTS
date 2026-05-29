"""Structured actor failure events for supervision and observability."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ActorFailureEvent:
    """Immutable record of an actor failure emitted by the runtime.

    These events are emitted when an actor's handle() raises an exception
    during mailbox processing.  The supervisor and observability sinks
    consume them to decide restart policy, log, and alert.
    """

    actor_name: str
    exception_type: str
    exception_message: str
    timestamp: datetime | None = None
    recoverable: bool = True

    @classmethod
    def from_exception(
        cls,
        actor_name: str,
        exception: BaseException,
        *,
        recoverable: bool = True,
    ) -> ActorFailureEvent:
        """Create an ActorFailureEvent from a caught exception."""
        return cls(
            actor_name=actor_name,
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            timestamp=datetime.now(tz=UTC),
            recoverable=recoverable,
        )


__all__ = ["ActorFailureEvent"]
