"""Cohesive supervision policies for actor restart, mailbox, and ask handling.

These small value objects describe *how* the supervisor reacts to an actor
failure once a :class:`~qts.runtime.actor_supervisor.SupervisorDecision` has
been taken:

* :class:`RestartPolicy` decides whether a failure is recoverable within a
  bounded restart window and therefore worth restarting, or whether repeated
  failures have exhausted the budget and must escalate.
* :class:`MailboxDrainPolicy` decides what happens to messages still queued in
  a failed actor's mailbox when it is restarted: discard them (the failing
  message and anything queued behind it are dropped) or preserve them for
  reprocessing.
* :class:`AskContextPolicy` decides how in-flight ``ask()`` requests behave when
  the target actor fails: fail fast so the live-path caller receives a
  domain-specific error, or leave the caller to time out on its own.

They are deterministic and free of I/O so the supervisor and runtime session
remain fully testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto

from qts.runtime.mailbox import Mailbox


class MailboxDrainMode(Enum):
    """How a failed actor's mailbox is handled on restart."""

    DISCARD = auto()
    PRESERVE = auto()


class AskContextMode(Enum):
    """How in-flight ``ask()`` requests behave when the target actor fails."""

    FAIL_FAST = auto()
    WAIT_FOR_TIMEOUT = auto()


@dataclass(frozen=True, slots=True)
class RestartPolicy:
    """Bounded-restart policy for actor failures.

    A failure is *restartable* when it is recoverable and the number of
    failures already observed for the actor within ``window`` is below
    ``max_restarts``.  Once that budget is exhausted, or the failure is
    non-recoverable, the actor must not be restarted and the supervisor
    escalates to degrade.

    The policy is stateless: failure history is supplied by the caller as an
    ordered sequence of timestamps so the decision stays deterministic and
    testable.
    """

    max_restarts: int = 3
    window: timedelta = timedelta(minutes=1)

    def __post_init__(self) -> None:
        """Validate restart-budget invariants."""
        if self.max_restarts < 0:
            raise ValueError("max_restarts must be non-negative")
        if self.window <= timedelta(0):
            raise ValueError("window must be positive")

    def restarts_within_window(
        self,
        failure_times: tuple[datetime, ...],
        *,
        now: datetime,
    ) -> int:
        """Count prior failures that fall inside the restart window ending at *now*."""
        threshold = now - self.window
        return sum(1 for failure_time in failure_times if failure_time > threshold)

    def should_restart(
        self,
        failure_times: tuple[datetime, ...],
        *,
        now: datetime,
        recoverable: bool,
    ) -> bool:
        """Return whether the current failure should trigger a restart.

        *failure_times* are the timestamps of failures already recorded for the
        actor (excluding the current one); *now* is the current failure's
        timestamp.  A non-recoverable failure is never restartable.  A
        recoverable failure is restartable only while prior restarts within the
        window remain under ``max_restarts``.
        """
        if not recoverable:
            return False
        return self.restarts_within_window(failure_times, now=now) < self.max_restarts


@dataclass(frozen=True, slots=True)
class MailboxDrainPolicy:
    """Policy for handling a failed actor's mailbox on restart."""

    mode: MailboxDrainMode = MailboxDrainMode.DISCARD

    def apply(self, mailbox: Mailbox) -> tuple[object, ...]:
        """Apply the drain policy to *mailbox*, returning the affected messages.

        For :attr:`MailboxDrainMode.DISCARD` the mailbox is emptied and the
        discarded messages are returned for observability.  For
        :attr:`MailboxDrainMode.PRESERVE` the mailbox is left untouched and an
        empty tuple is returned.
        """
        if self.mode is MailboxDrainMode.PRESERVE:
            return ()
        drained: list[object] = []
        while not mailbox.empty():
            drained.append(mailbox.get())
        return tuple(drained)

    @property
    def discards(self) -> bool:
        """Return whether this policy discards queued messages on restart."""
        return self.mode is MailboxDrainMode.DISCARD


@dataclass(frozen=True, slots=True)
class AskContextPolicy:
    """Policy for in-flight ``ask()`` requests when the target actor fails."""

    mode: AskContextMode = AskContextMode.FAIL_FAST

    @property
    def fails_fast(self) -> bool:
        """Return whether in-flight asks should be failed immediately on failure."""
        return self.mode is AskContextMode.FAIL_FAST


__all__ = [
    "AskContextMode",
    "AskContextPolicy",
    "MailboxDrainMode",
    "MailboxDrainPolicy",
    "RestartPolicy",
]
