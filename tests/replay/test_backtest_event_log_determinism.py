"""Gate test for byte-identical deterministic FileEventStore output.

Locks the Task 9.2 acceptance criterion: writing the same events with an
injected fixed clock twice yields byte-identical event log files. The store
stamps ``ts_ingest`` from the injected clock, so a deterministic run (fixed
clock plus deterministic ``ts_event``) produces an identical on-disk log.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.core.ids import EventId, RuntimeRunId
from qts.runtime.event_store import FileEventStore
from qts.runtime.sinks.base import RuntimeEvent


class _FixedClock:
    """Clock that returns a fixed instant so ingest stamps are deterministic."""

    def __init__(self, instant: datetime) -> None:
        self._instant = instant

    def now(self) -> datetime:
        return self._instant


def _events() -> tuple[RuntimeEvent, ...]:
    run_id = RuntimeRunId("run-determinism-001")
    occurred = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    return (
        RuntimeEvent(
            event_id=EventId("evt-001"),
            kind="runtime.state_snapshot",
            payload={"state": "running"},
            run_id=run_id,
            mode="live",
            sequence_no=1,
            ts_event=occurred,
        ),
        RuntimeEvent(
            event_id=EventId("evt-002"),
            kind="runtime.state_snapshot",
            payload={"state": "stopping"},
            run_id=run_id,
            mode="live",
            sequence_no=2,
            ts_event=occurred,
        ),
    )


def _write_log(path: Path, instant: datetime) -> None:
    store = FileEventStore(path, clock=_FixedClock(instant))
    for event in _events():
        store.append(event)
    store.close()


def test_same_events_and_fixed_clock_produce_byte_identical_log(tmp_path: Path) -> None:
    instant = datetime(2026, 1, 2, 14, 30, 0, 500000, tzinfo=UTC)
    left = tmp_path / "left.jsonl"
    right = tmp_path / "right.jsonl"

    _write_log(left, instant)
    _write_log(right, instant)

    assert left.read_bytes() == right.read_bytes()
