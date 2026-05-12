"""Base immutable domain event model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from qts.core.ids import CausationId, CorrelationId, EventId
from qts.core.time import require_aware_datetime


@dataclass(frozen=True, slots=True)
class BaseEvent:
    """Minimal event envelope used for traceable internal messages."""

    event_id: EventId
    event_type: str
    event_time: datetime
    source: str
    partition_key: str
    correlation_id: CorrelationId | None = None
    causation_id: CausationId | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")
        require_aware_datetime(self.event_time, name="event_time")
        if not self.source.strip():
            raise ValueError("source must not be empty")
        if not self.partition_key.strip():
            raise ValueError("partition_key must not be empty")


__all__ = ["BaseEvent"]
