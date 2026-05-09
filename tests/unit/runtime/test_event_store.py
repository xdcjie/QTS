from __future__ import annotations

from datetime import UTC, datetime


def test_in_memory_event_store_appends_and_replays_deterministically() -> None:
    from qts.core.ids import EventId
    from qts.domain.events import BaseEvent
    from qts.runtime.event_store import InMemoryEventStore

    store = InMemoryEventStore()
    first = BaseEvent(
        event_id=EventId("evt-001"),
        event_type="market_data.tick",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        source="MarketDataActor",
        partition_key="AAPL",
    )
    second = BaseEvent(
        event_id=EventId("evt-002"),
        event_type="execution.fill",
        event_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        source="ExecutionActor",
        partition_key="ord-001",
    )

    store.append(first)
    store.append(second)

    assert store.replay() == (first, second)
    assert store.replay(partition_key="AAPL") == (first,)
