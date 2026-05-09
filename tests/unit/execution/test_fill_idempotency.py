from __future__ import annotations


def test_duplicate_fill_id_is_ignored() -> None:
    from qts.execution.idempotency import FillIdempotencyStore

    store = FillIdempotencyStore()

    assert store.mark_seen("fill-001")
    assert not store.mark_seen("fill-001")


def test_distinct_fill_ids_apply_once_deterministically() -> None:
    from qts.execution.idempotency import FillIdempotencyStore

    store = FillIdempotencyStore()

    assert [store.mark_seen(fill_id) for fill_id in ("a", "b", "a")] == [True, True, False]
