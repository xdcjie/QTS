from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest


def test_base_event_is_immutable_traceable_and_partitioned() -> None:
    from qts.core.ids import CausationId, CorrelationId, EventId
    from qts.domain.events import BaseEvent

    event = BaseEvent(
        event_id=EventId("evt-002"),
        event_type="bar.closed",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        source="market-data",
        partition_key="strategy-001",
        correlation_id=CorrelationId("corr-001"),
        causation_id=CausationId("evt-001"),
    )

    assert event.source == "market-data"
    assert event.partition_key == "strategy-001"
    assert event.causation_id == CausationId("evt-001")
    with pytest.raises(FrozenInstanceError):
        event.source = "other"  # type: ignore[misc]


def test_base_event_rejects_empty_routing_fields() -> None:
    from qts.core.ids import EventId
    from qts.domain.events import BaseEvent

    event_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)

    with pytest.raises(ValueError, match="event_type must not be empty"):
        BaseEvent(
            event_id=EventId("evt-001"),
            event_type="",
            event_time=event_time,
            source="market-data",
            partition_key="strategy-001",
        )
    with pytest.raises(ValueError, match="source must not be empty"):
        BaseEvent(
            event_id=EventId("evt-001"),
            event_type="bar.closed",
            event_time=event_time,
            source="",
            partition_key="strategy-001",
        )
    with pytest.raises(ValueError, match="partition_key must not be empty"):
        BaseEvent(
            event_id=EventId("evt-001"),
            event_type="bar.closed",
            event_time=event_time,
            source="market-data",
            partition_key="",
        )
