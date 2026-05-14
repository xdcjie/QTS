"""Idempotency support for operational commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class CommandIdempotencyStore:
    """Remember the first result for each command idempotency key."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._results: dict[tuple[str, str], object] = {}

    def run(self, key: str, command: Callable[[], T], *, scope: str = "runtime") -> T:
        """Perform run."""
        if not key.strip():
            raise ValueError("idempotency key must not be empty")
        if not scope.strip():
            raise ValueError("idempotency scope must not be empty")
        scoped_key = (scope, key)
        if scoped_key in self._results:
            return self._results[scoped_key]  # type: ignore[return-value]
        result = command()
        self._results[scoped_key] = result
        return result


__all__ = ["CommandIdempotencyStore"]
