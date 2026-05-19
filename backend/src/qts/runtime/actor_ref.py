"""Actor references."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeVar

from qts.runtime.actor import Actor
from qts.runtime.mailbox import Mailbox

T_co = TypeVar("T_co", covariant=True)


class ActorQuery(Protocol[T_co]):
    """Actor ask-message contract with response validation."""

    def validate_response(self, response: object) -> T_co:
        """Validate and return the typed actor response."""
        ...


@dataclass(frozen=True, slots=True)
class ActorRef:
    """Message-only reference to an actor mailbox."""

    mailbox: Mailbox
    actor: Actor | None = None

    def tell(self, message: object) -> None:
        """Perform tell."""
        self.mailbox.put(message)

    def ask(self, message: ActorQuery[T_co], timeout: float = 5.0) -> T_co:
        """Send *message* and block until the actor produces a response.

        The ask pattern wraps the caller's message together with a fresh
        response mailbox into a ``(query, response_mailbox)`` tuple that
        the target actor's ``handle()`` method recognises.  After placing
        the tuple in the actor mailbox the call drains the actor's
        mailbox (synchronous model) and then blocks on the response
        mailbox for up to *timeout* seconds.
        """
        response_mailbox = Mailbox()
        self.mailbox.put((message, response_mailbox))
        if self.actor is not None:
            self.process_all()
        response = response_mailbox.get_with_timeout(timeout)
        return message.validate_response(response)

    def process_one(self) -> bool:
        """Perform process_one."""
        if self.actor is None or self.mailbox.empty():
            return False
        self.actor.handle(self.mailbox.get())
        return True

    def process_all(self) -> int:
        """Perform process_all."""
        processed = 0
        while self.process_one():
            processed += 1
        return processed


__all__ = ["ActorQuery", "ActorRef"]
