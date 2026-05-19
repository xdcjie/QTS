"""FIFO mailbox."""

from __future__ import annotations

from collections import deque
from threading import Condition


class MailboxTimeoutError(Exception):
    """Raised when a timed mailbox get expires."""


class Mailbox:
    """Simple in-memory FIFO mailbox with optional blocking get."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._messages: deque[object] = deque()
        self._condition = Condition()

    @property
    def size(self) -> int:
        """Perform size."""
        return len(self._messages)

    def put(self, message: object) -> None:
        """Perform put."""
        with self._condition:
            self._messages.append(message)
            self._condition.notify()

    def get(self) -> object:
        """Perform get."""
        return self._messages.popleft()

    def get_with_timeout(self, timeout: float) -> object:
        """Block until a message arrives or *timeout* seconds elapse.

        In the synchronous actor processing model the response is typically
        already in the mailbox by the time this is called, so the condition
        is satisfied immediately.  When the mailbox is empty the thread
        blocks until :meth:`put` notifies or the deadline expires.
        """
        with self._condition:
            if self._messages:
                return self._messages.popleft()
            if not self._condition.wait(timeout=timeout):
                raise MailboxTimeoutError(f"mailbox get timed out after {timeout}s")
            if self._messages:
                return self._messages.popleft()
            raise MailboxTimeoutError(f"mailbox get timed out after {timeout}s (spurious wake)")

    def empty(self) -> bool:
        """Perform empty."""
        return not self._messages


__all__ = ["Mailbox", "MailboxTimeoutError"]
