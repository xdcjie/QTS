"""FIFO mailbox."""

from __future__ import annotations

from collections import deque
from threading import Condition


class MailboxTimeoutError(Exception):
    """Raised when a timed mailbox get expires."""


class Mailbox:
    """Simple in-memory FIFO mailbox with optional blocking get."""

    def __init__(self) -> None:
        """Create an empty message deque guarded by a condition variable."""
        self._messages: deque[object] = deque()
        self._condition = Condition()

    @property
    def size(self) -> int:
        """Return the number of queued messages."""
        return len(self._messages)

    def put(self, message: object) -> None:
        """Append a message and notify any waiting consumer."""
        with self._condition:
            self._messages.append(message)
            self._condition.notify()

    def get(self) -> object:
        """Pop and return the oldest message without blocking."""
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

    def get_blocking(self) -> object:
        """Block indefinitely until a message arrives.

        Used by the ask pattern when no timeout is configured.  In the
        synchronous actor model the response is typically already in the
        mailbox by the time this is called, so the condition is satisfied
        immediately.  When the mailbox is empty the thread blocks until
        :meth:`put` notifies.
        """
        with self._condition:
            if self._messages:
                return self._messages.popleft()
            self._condition.wait()
            if self._messages:
                return self._messages.popleft()
            raise RuntimeError("blocking mailbox wait failed (spurious wake with no message)")

    def empty(self) -> bool:
        """Return whether the mailbox currently holds no messages."""
        return not self._messages


__all__ = ["Mailbox", "MailboxTimeoutError"]
