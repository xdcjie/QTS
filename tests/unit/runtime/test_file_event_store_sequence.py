"""Gate tests for FileEventStore sequence seeding and single-writer safety.

Locks the Task 9.2 acceptance criteria:
- the monotonic sequence counter is seeded once from the existing file on open;
- ``append`` is O(1) and does not re-read the whole file (it must not call
  ``replay()``);
- a second concurrent writer that appends to the same path is rejected.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.core.ids import EventId
from qts.domain.events import BaseEvent
from qts.runtime.event_store import FileEventStore, SingleWriterViolation


def _event(event_id: str, minute: int) -> BaseEvent:
    return BaseEvent(
        event_id=EventId(event_id),
        event_type="order.accepted",
        event_time=datetime(2026, 1, 2, 14, minute, tzinfo=UTC),
        source="OrderManagerActor",
        partition_key="ord-001",
    )


def test_sequence_is_seeded_from_existing_file_on_open(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    first = FileEventStore(path)
    assert first.append(_event("evt-001", 30)) == 1
    assert first.append(_event("evt-002", 31)) == 2
    first.close()

    reopened = FileEventStore(path)
    # Seeded from the persisted max sequence (2), so the next append is 3.
    assert reopened.append(_event("evt-003", 32)) == 3
    assert reopened.append(_event("evt-004", 33)) == 4

    sequences = [int(line.split('"sequence":')[1].split("}")[0]) for line in _lines(path)]
    assert sequences == [1, 2, 3, 4]


def test_append_does_not_re_read_the_whole_file(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    store = FileEventStore(path)
    store.append(_event("evt-001", 30))
    store.append(_event("evt-002", 31))

    # Spy: append must not fall back to a full-file replay() per the O(1) contract.
    calls = {"replay": 0}
    original_replay = store.replay

    def _counting_replay(*args: object, **kwargs: object) -> tuple[object, ...]:
        calls["replay"] += 1
        return original_replay(*args, **kwargs)  # type: ignore[arg-type]

    store.replay = _counting_replay  # type: ignore[method-assign,assignment]

    assert store.append(_event("evt-003", 32)) == 3
    assert calls["replay"] == 0


def test_second_writer_append_is_rejected_while_first_is_open(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    first = FileEventStore(path)
    assert first.append(_event("evt-001", 30)) == 1  # first acquires the writer lock

    second = FileEventStore(path)
    with pytest.raises(SingleWriterViolation):
        second.append(_event("evt-002", 31))

    # After the first writer releases, a new writer may append again.
    first.close()
    third = FileEventStore(path)
    assert third.append(_event("evt-003", 31)) == 2
    third.close()


def test_read_only_store_does_not_take_the_writer_lock(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    writer = FileEventStore(path)
    writer.append(_event("evt-001", 30))

    # A reader replays without acquiring the lock, so it never contends.
    reader = FileEventStore(path)
    assert len(reader.replay()) == 1

    # The original writer can still append (it still holds the lock).
    assert writer.append(_event("evt-002", 31)) == 2
    writer.close()


def _lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
