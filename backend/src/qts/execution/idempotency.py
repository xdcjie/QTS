"""Execution idempotency helpers."""

from __future__ import annotations


class FillIdempotencyStore:
    """Tracks fill IDs that have already been applied."""

    def __init__(self, seen: set[str] | None = None) -> None:
        """Perform __init__."""
        self._seen: set[str] = set(seen or set())

    def mark_seen(self, fill_id: str) -> bool:
        """Perform mark_seen."""
        if not fill_id.strip():
            raise ValueError("fill_id must not be empty")
        if fill_id in self._seen:
            return False
        self._seen.add(fill_id)
        return True

    def discard(self, fill_id: str) -> None:
        """Perform discard."""
        self._seen.discard(fill_id)

    def snapshot(self) -> tuple[str, ...]:
        """Perform snapshot."""
        return tuple(sorted(self._seen))

    @classmethod
    def restore(cls, seen: tuple[str, ...]) -> FillIdempotencyStore:
        """Perform restore."""
        return cls(set(seen))


__all__ = ["FillIdempotencyStore"]
