"""Idempotency support for operational commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class CommandIdempotencyStore:
    """Remember the first result for each command idempotency key."""

    def __init__(self) -> None:
        self._results: dict[str, object] = {}

    def run(self, key: str, command: Callable[[], T]) -> T:
        if not key.strip():
            raise ValueError("idempotency key must not be empty")
        if key in self._results:
            return self._results[key]  # type: ignore[return-value]
        result = command()
        self._results[key] = result
        return result


__all__ = ["CommandIdempotencyStore"]
