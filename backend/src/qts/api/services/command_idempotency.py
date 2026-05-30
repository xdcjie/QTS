"""Idempotency support for operational commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class CommandIdempotencyStore:
    """Remember the first result for each command idempotency key."""

    def __init__(self) -> None:
        """Initialize an empty store of cached results keyed by (scope, key)."""
        self._results: dict[tuple[str, str], object] = {}

    def run(self, key: str, command: Callable[[], T], *, scope: str = "runtime") -> T:
        """Run the command once per scoped key, returning the cached result on repeats."""
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
