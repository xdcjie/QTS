"""FIFO mailbox."""

from __future__ import annotations

from collections import deque


class Mailbox:
    """Simple in-memory FIFO mailbox."""

    def __init__(self) -> None:
        self._messages: deque[object] = deque()

    @property
    def size(self) -> int:
        return len(self._messages)

    def put(self, message: object) -> None:
        self._messages.append(message)

    def get(self) -> object:
        return self._messages.popleft()

    def empty(self) -> bool:
        return not self._messages


__all__ = ["Mailbox"]
