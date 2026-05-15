from __future__ import annotations

from datetime import UTC, datetime
from typing import cast


def test_bar_to_fill_flow_can_be_traced_by_correlation_id() -> None:
    from qts.core.ids import CorrelationId, EventId
    from qts.domain.events import BaseEvent
    from qts.runtime.event_store import InMemoryEventStore

    correlation_id = CorrelationId("corr-001")
    store = InMemoryEventStore()
    for event_id, event_type in [
        ("evt-bar", "market_data.bar.closed"),
        ("evt-target", "strategy.target"),
        ("evt-order", "order.sent"),
        ("evt-fill", "execution.fill"),
        ("evt-portfolio", "portfolio.updated"),
    ]:
        store.append(
            BaseEvent(
                event_id=EventId(event_id),
                event_type=event_type,
                event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
                source="test",
                partition_key="acct-001",
                correlation_id=correlation_id,
            )
        )

    events = cast(tuple[BaseEvent, ...], store.by_correlation_id(correlation_id))

    assert [event.event_type for event in events] == [
        "market_data.bar.closed",
        "strategy.target",
        "order.sent",
        "execution.fill",
        "portfolio.updated",
    ]
