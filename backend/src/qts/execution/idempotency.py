"""Execution idempotency helpers."""

from __future__ import annotations


class FillIdempotencyStore:
    """Tracks fill IDs that have already been applied.

    ``snapshot()`` is called once per ``AccountActor.snapshot()`` call,
    which in turn fires on every per-bar account snapshot emission in
    backtest event sinks. Naïvely re-sorting the membership set on each
    call is ``O(n log n)`` per call, producing quadratic wall time on
    long backtests. The store caches the sorted tuple and invalidates
    only on actual membership change (``mark_seen`` returning True or
    a successful ``discard``).
    """

    def __init__(self, seen: set[str] | None = None) -> None:
        """Perform __init__."""
        self._seen: set[str] = set(seen or set())
        self._snapshot_cache: tuple[str, ...] | None = None

    def mark_seen(self, fill_id: str) -> bool:
        """Perform mark_seen."""
        if not fill_id.strip():
            raise ValueError("fill_id must not be empty")
        if fill_id in self._seen:
            return False
        self._seen.add(fill_id)
        self._snapshot_cache = None
        return True

    def discard(self, fill_id: str) -> None:
        """Perform discard."""
        if fill_id in self._seen:
            self._seen.discard(fill_id)
            self._snapshot_cache = None

    def snapshot(self) -> tuple[str, ...]:
        """Perform snapshot."""
        if self._snapshot_cache is None:
            self._snapshot_cache = tuple(sorted(self._seen))
        return self._snapshot_cache

    @classmethod
    def restore(cls, seen: tuple[str, ...]) -> FillIdempotencyStore:
        """Perform restore."""
        return cls(set(seen))


__all__ = ["FillIdempotencyStore"]
