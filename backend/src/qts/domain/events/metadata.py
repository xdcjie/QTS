"""Event metadata for immutable and traceable domain events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from qts.core.ids import (
    AccountId,
    CausationId,
    CorrelationId,
    EventId,
    InstrumentId,
    OrderId,
    StrategyId,
)
from qts.core.time import require_aware_datetime


@dataclass(frozen=True, slots=True)
class EventMetadata:
    """Trace metadata carried by platform events."""

    event_id: EventId
    event_type: str
    event_time: datetime
    source_actor: str | None = None
    target_actor: str | None = None
    account_id: AccountId | None = None
    strategy_id: StrategyId | None = None
    instrument_id: InstrumentId | None = None
    order_id: OrderId | None = None
    bar_time: datetime | None = None
    seq: int | None = None
    partition_key: str | None = None
    correlation_id: CorrelationId | None = None
    causation_id: CausationId | None = None

    def __post_init__(self) -> None:
        """Validate non-empty event_type, aware timestamps, and non-negative seq."""
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")
        require_aware_datetime(self.event_time, name="event_time")
        if self.bar_time is not None:
            require_aware_datetime(self.bar_time, name="bar_time")
        if self.seq is not None and self.seq < 0:
            raise ValueError("seq must be non-negative")
        if self.partition_key is not None and not self.partition_key.strip():
            raise ValueError("partition_key must not be empty")


__all__ = ["EventMetadata"]
