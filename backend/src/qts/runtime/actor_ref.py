"""Actor references."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar

from qts.runtime.actor import Actor
from qts.runtime.actor_errors import ActorAskTimeoutError
from qts.runtime.actor_events import ActorFailureEvent
from qts.runtime.actor_path import ActorPath
from qts.runtime.mailbox import Mailbox, MailboxTimeoutError

T_co = TypeVar("T_co", covariant=True)

# Type alias for the failure-sink callback used by ActorRef.
FailureSink = Callable[[ActorFailureEvent], None]


class ActorQuery(Protocol[T_co]):
    """Actor ask-message contract with response validation."""

    def validate_response(self, response: object) -> T_co:
        """Validate and return the typed actor response."""
        ...


@dataclass(frozen=True, slots=True)
class ActorRef:
    """Message-only reference to an actor mailbox.

    Optionally carries an :class:`ActorPath` for naming/supervision and a
    ``failure_sink`` callback that receives :class:`ActorFailureEvent` when
    ``handle()`` raises during mailbox processing.  Both fields default to
    ``None`` and are fully backward-compatible with existing code.
    """

    mailbox: Mailbox
    actor: Actor | None = None
    path: ActorPath | None = None
    failure_sink: FailureSink | None = None

    def tell(self, message: object) -> None:
        """Enqueue a fire-and-forget message into the actor's mailbox."""
        self.mailbox.put(message)

    def ask(self, message: ActorQuery[T_co], ask_timeout: float | None = None) -> T_co:
        """Send *message* and block until the actor produces a response.

        The ask pattern wraps the caller's message together with a fresh
        response mailbox into a ``(query, response_mailbox)`` tuple that
        the target actor's ``handle()`` method recognises.  After placing
        the tuple in the actor mailbox the call drains the actor's
        mailbox (synchronous model) and then blocks on the response
        mailbox.

        When *ask_timeout* is ``None`` (default), the call blocks
        indefinitely until the response arrives.  This is safe in the
        synchronous model because ``process_all()`` ensures the actor
        processes the query before we wait.

        When *ask_timeout* is a float, the call raises
        :class:`ActorAskTimeoutError` if the response does not arrive
        within the given seconds.  This prevents unbounded blocking in
        live-critical broker callbacks.
        """
        response_mailbox = Mailbox()
        self.mailbox.put((message, response_mailbox))
        if self.actor is not None:
            self.process_all()
        if ask_timeout is None:
            response = response_mailbox.get_blocking()
        else:
            try:
                response = response_mailbox.get_with_timeout(ask_timeout)
            except MailboxTimeoutError as exc:
                raise ActorAskTimeoutError(
                    f"ask() timed out after {ask_timeout}s for actor {self.path or '(unnamed)'}"
                ) from exc
        return message.validate_response(response)

    def process_one(self) -> bool:
        """Process one message from the mailbox.

        If the actor's ``handle()`` raises, the exception is caught and
        an :class:`ActorFailureEvent` is emitted to the configured
        ``failure_sink`` (if any).  The mailbox continues to accept
        messages for graceful degradation.  Returns ``True`` if a message
        was dequeued (even if handle raised), ``False`` if the mailbox
        was empty.
        """
        if self.actor is None or self.mailbox.empty():
            return False
        message = self.mailbox.get()
        try:
            self.actor.handle(message)
        except Exception as exc:
            if self.failure_sink is not None:
                actor_name = str(self.path) if self.path is not None else "(unnamed)"
                event = ActorFailureEvent.from_exception(
                    actor_name=actor_name,
                    exception=exc,
                )
                self.failure_sink(event)
            else:
                raise
        return True

    def process_all(self) -> int:
        """Process all pending messages from the mailbox.

        Exceptions raised by ``handle()`` are caught per-message and
        emitted as :class:`ActorFailureEvent` to the configured
        ``failure_sink``.  Processing continues after a failure so that
        subsequent messages are not stranded in the mailbox.
        """
        processed = 0
        while self.process_one():
            processed += 1
        return processed


__all__ = ["ActorQuery", "ActorRef", "FailureSink"]
