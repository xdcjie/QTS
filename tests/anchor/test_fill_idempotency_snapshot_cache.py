"""Anchor: FillIdempotencyStore.snapshot() is O(1) when membership is unchanged.

Domain fact: ``AccountActor.snapshot()`` calls
``_fill_ids.snapshot()`` on every per-bar account snapshot emission.
Without a cache, each call re-sorts the full seen-fill set —
``O(n log n)`` per call. For a 90-day GC backtest profiling showed
this single ``sorted()`` consumed ~23% of total wall time, growing
quadratically with run length.

The cache must remain transparently correct: the returned tuple
must equal the freshly-sorted set on every call, and must update
after ``mark_seen`` and ``discard`` mutate membership.

Owner: ``qts.execution.idempotency.FillIdempotencyStore``.

Forbidden shortcut: returning an unsorted tuple; mutating the cached
tuple after handing it out; failing to invalidate after ``discard``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from qts.execution.idempotency import FillIdempotencyStore


def test_snapshot_returns_sorted_tuple_of_seen_ids() -> None:
    store = FillIdempotencyStore()
    for fill_id in ("c", "a", "b"):
        store.mark_seen(fill_id)
    assert store.snapshot() == ("a", "b", "c")


def test_repeated_snapshot_calls_sort_only_once_when_membership_unchanged() -> None:
    """Calling snapshot() N times without mutation must trigger ``sorted`` once."""
    store = FillIdempotencyStore()
    for fill_id in ("a", "b", "c", "d", "e"):
        store.mark_seen(fill_id)

    with patch("qts.execution.idempotency.sorted", wraps=sorted) as spy:
        first = store.snapshot()
        for _ in range(100):
            assert store.snapshot() == first
        assert spy.call_count == 1


def test_snapshot_cache_invalidates_on_mark_seen() -> None:
    store = FillIdempotencyStore()
    store.mark_seen("a")
    initial = store.snapshot()
    assert initial == ("a",)

    store.mark_seen("b")
    updated = store.snapshot()
    assert updated == ("a", "b")
    assert len(updated) != len(initial)


def test_snapshot_cache_invalidates_on_discard() -> None:
    store = FillIdempotencyStore()
    store.mark_seen("a")
    store.mark_seen("b")
    assert store.snapshot() == ("a", "b")

    store.discard("a")
    assert store.snapshot() == ("b",)


def test_snapshot_cache_not_invalidated_on_duplicate_mark_seen() -> None:
    """Duplicate ``mark_seen`` returns False without mutating membership.

    The cache must not be invalidated in that case — otherwise duplicate
    fill IDs would force a full re-sort on every retry.
    """
    store = FillIdempotencyStore()
    store.mark_seen("a")
    store.mark_seen("b")

    with patch("qts.execution.idempotency.sorted", wraps=sorted) as spy:
        first = store.snapshot()
        assert not store.mark_seen("a")
        second = store.snapshot()
        assert first is second  # identity (cache reused, not just equal)
        assert spy.call_count == 1


def test_returned_tuple_is_safe_to_mutate_externally() -> None:
    """Cache must hand out an immutable tuple — callers cannot poison it."""
    store = FillIdempotencyStore()
    store.mark_seen("a")
    snap = store.snapshot()
    assert isinstance(snap, tuple)
    with pytest.raises(TypeError):
        snap[0] = "x"  # type: ignore[index]
