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


def test_event_store_keeps_json_conversion_inside_file_store() -> None:
    tree = ast.parse(Path("backend/src/qts/runtime/event_store.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_event_to_json" not in private_functions
    assert "_event_from_json" not in private_functions
