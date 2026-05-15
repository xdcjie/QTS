from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

from qts.core.ids import CorrelationId, EventId
from qts.domain.events import BaseEvent


def test_in_memory_event_store_appends_and_replays_deterministically() -> None:
    from qts.runtime.event_store import InMemoryEventStore

    correlation_id = CorrelationId("corr-001")
    store = InMemoryEventStore()
    first = BaseEvent(
        event_id=EventId("evt-001"),
        event_type="market_data.tick",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        source="MarketDataActor",
        partition_key="AAPL",
        correlation_id=correlation_id,
    )
    second = BaseEvent(
        event_id=EventId("evt-002"),
        event_type="execution.fill",
        event_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        source="ExecutionActor",
        partition_key="ord-001",
    )

    assert store.append(first) == 1
    assert store.append(second) == 2

    assert store.replay() == (first, second)
    assert store.replay(partition_key="AAPL") == (first,)
    assert store.by_correlation_id(correlation_id) == (first,)


def test_file_event_store_survives_restart(tmp_path: Path) -> None:
    from qts.runtime.event_store import FileEventStore

    path = tmp_path / "events.jsonl"
    event = BaseEvent(
        event_id=EventId("evt-001"),
        event_type="order.accepted",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        source="OrderManagerActor",
        partition_key="ord-001",
        correlation_id=CorrelationId("corr-001"),
    )

    assert FileEventStore(path).append(event) == 1

    restored = FileEventStore(path)
    assert restored.replay() == (event,)
    assert restored.by_correlation_id(CorrelationId("corr-001")) == (event,)


def test_file_event_store_appends_and_replays_runtime_event_envelopes(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.runtime.event_store import FileEventStore
    from qts.runtime.sinks.base import RuntimeEvent

    path = tmp_path / "runtime-events.jsonl"
    event = RuntimeEvent(
        event_id=EventId("evt-runtime-001"),
        kind="runtime.state",
        payload={"state": "running"},
        run_id=RuntimeRunId("run-runtime-001"),
        mode="paper_broker",
        sequence_no=1,
    )

    assert FileEventStore(path).append(event) == 1

    restored = FileEventStore(path)
    assert restored.replay() == (event,)
    assert restored.replay_after(0) == (event,)


def test_event_store_replays_events_after_snapshot_sequence(tmp_path: Path) -> None:
    from qts.runtime.event_store import FileEventStore, InMemoryEventStore

    first = BaseEvent(
        event_id=EventId("evt-001"),
        event_type="order.accepted",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        source="OrderManagerActor",
        partition_key="ord-001",
    )
    second = BaseEvent(
        event_id=EventId("evt-002"),
        event_type="execution.fill",
        event_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        source="ExecutionActor",
        partition_key="ord-001",
    )
    memory_store = InMemoryEventStore()
    file_store = FileEventStore(tmp_path / "events.jsonl")
    for store in (memory_store, file_store):
        store.append(first)
        store.append(second)

    assert memory_store.replay_after(1) == (second,)
    assert file_store.replay_after(1) == (second,)
    assert file_store.replay_after(0, partition_key="ord-001") == (first, second)


def test_file_event_store_detects_missing_event_sequence(tmp_path: Path) -> None:
    from qts.runtime.event_store import FileEventStore

    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            (
                '{"event": {"causation_id": null, "correlation_id": null, '
                '"event_id": "evt-001", "event_time": "2026-01-02T14:30:00+00:00", '
                '"event_type": "order.accepted", "partition_key": "ord-001", '
                '"source": "OrderManagerActor"}, "sequence": 1}',
                '{"event": {"causation_id": null, "correlation_id": null, '
                '"event_id": "evt-003", "event_time": "2026-01-02T14:32:00+00:00", '
                '"event_type": "order.filled", "partition_key": "ord-001", '
                '"source": "OrderManagerActor"}, "sequence": 3}',
            )
        ),
        encoding="utf-8",
    )

    report = FileEventStore(path).validate_sequence()

    assert not report.valid
    assert report.missing_sequences == (2,)
    assert report.duplicate_sequences == ()


def test_file_event_store_detects_duplicate_event_sequence(tmp_path: Path) -> None:
    from qts.runtime.event_store import FileEventStore

    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            (
                '{"event": {"causation_id": null, "correlation_id": null, '
                '"event_id": "evt-001", "event_time": "2026-01-02T14:30:00+00:00", '
                '"event_type": "order.accepted", "partition_key": "ord-001", '
                '"source": "OrderManagerActor"}, "sequence": 1}',
                '{"event": {"causation_id": null, "correlation_id": null, '
                '"event_id": "evt-001-duplicate", '
                '"event_time": "2026-01-02T14:30:01+00:00", '
                '"event_type": "order.accepted", "partition_key": "ord-001", '
                '"source": "OrderManagerActor"}, "sequence": 1}',
            )
        ),
        encoding="utf-8",
    )

    report = FileEventStore(path).validate_sequence()

    assert not report.valid
    assert report.missing_sequences == ()
    assert report.duplicate_sequences == (1,)


def test_event_store_keeps_json_conversion_inside_file_store() -> None:
    tree = ast.parse(Path("backend/src/qts/runtime/event_store.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_event_to_json" not in private_functions
    assert "_event_from_json" not in private_functions
