"""Actor references."""

from __future__ import annotations

from dataclasses import dataclass

from qts.runtime.actor import Actor
from qts.runtime.mailbox import Mailbox


@dataclass(frozen=True, slots=True)
class ActorRef:
    """Message-only reference to an actor mailbox."""

    mailbox: Mailbox
    actor: Actor | None = None

    def tell(self, message: object) -> None:
        self.mailbox.put(message)

    def process_one(self) -> bool:
        if self.actor is None or self.mailbox.empty():
            return False
        self.actor.handle(self.mailbox.get())
        return True

    def process_all(self) -> int:
        processed = 0
        while self.process_one():
            processed += 1
        return processed


__all__ = ["ActorRef"]
