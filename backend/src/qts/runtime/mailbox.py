"""FIFO mailbox."""

from __future__ import annotations

from collections import deque


class Mailbox:
    """Simple in-memory FIFO mailbox."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._messages: deque[object] = deque()

    @property
    def size(self) -> int:
        """Perform size."""
        return len(self._messages)

    def put(self, message: object) -> None:
        """Perform put."""
        self._messages.append(message)

    def get(self) -> object:
        """Perform get."""
        return self._messages.popleft()

    def empty(self) -> bool:
        """Perform empty."""
        return not self._messages


__all__ = ["Mailbox"]
