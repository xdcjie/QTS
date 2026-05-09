"""Actor abstraction with mailbox-based message processing."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Actor(ABC):
    """Base actor that handles messages serially through an ActorRef."""

    @abstractmethod
    def handle(self, message: object) -> None:
        """Handle one message."""


__all__ = ["Actor"]
