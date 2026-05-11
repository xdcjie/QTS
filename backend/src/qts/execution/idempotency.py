"""Execution idempotency helpers."""

from __future__ import annotations


class FillIdempotencyStore:
    """Tracks fill IDs that have already been applied."""

    def __init__(self, seen: set[str] | None = None) -> None:
        self._seen: set[str] = set(seen or set())

    def mark_seen(self, fill_id: str) -> bool:
        if not fill_id.strip():
            raise ValueError("fill_id must not be empty")
        if fill_id in self._seen:
            return False
        self._seen.add(fill_id)
        return True

    def discard(self, fill_id: str) -> None:
        self._seen.discard(fill_id)

    def snapshot(self) -> tuple[str, ...]:
        return tuple(sorted(self._seen))

    @classmethod
    def restore(cls, seen: tuple[str, ...]) -> FillIdempotencyStore:
        return cls(set(seen))


__all__ = ["FillIdempotencyStore"]
