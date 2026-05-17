"""Market data subscription planning."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime
from qts.data.capabilities import MarketDataFeedCapabilities


class SourceStreamType(StrEnum):
    """Physical market data stream type."""

    BAR = "bar"
    TICK = "tick"
    QUOTE = "quote"


class MarketDataSubscriptionEventType(StrEnum):
    """Source subscription lifecycle event types visible to runtime."""

    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    RESUBSCRIBED = "resubscribed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class LogicalSubscription:
    """Strategy-requested market data stream."""

    subscriber_id: str
    instrument_id: InstrumentId
    requested_timeframe: str
    stream_type: SourceStreamType = SourceStreamType.BAR

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.subscriber_id.strip():
            raise ValueError("subscriber_id must not be empty")
        if not self.requested_timeframe.strip():
            raise ValueError("requested_timeframe must not be empty")


@dataclass(frozen=True, slots=True)
class LogicalSubscriptionKey:
    """Deduplication key for strategy-facing subscribers."""

    instrument_id: InstrumentId
    requested_timeframe: str
    stream_type: SourceStreamType = SourceStreamType.BAR


@dataclass(frozen=True, slots=True)
class MarketDataSubscriptionEvent:
    """Source-owned subscription lifecycle signal."""

    event_type: MarketDataSubscriptionEventType
    source_id: str
    instrument_id: InstrumentId
    subscription: LogicalSubscriptionKey
    broker_symbol: str
    observed_at: datetime
    reason: str | None = None

    def __post_init__(self) -> None:
        """Validate source lifecycle event fields."""
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        require_aware_datetime(self.observed_at, name="observed_at")
        if self.event_type is MarketDataSubscriptionEventType.FAILED:
            if self.reason is None or not self.reason.strip():
                raise ValueError("reason is required for failed subscription events")
        elif self.reason is not None and not self.reason.strip():
            raise ValueError("reason must not be empty when provided")


@dataclass(frozen=True, slots=True)
class UniverseSubscriptionDelta:
    """Internal instrument subscription changes required by a universe update."""

    subscribe: tuple[InstrumentId, ...]
    unsubscribe: tuple[InstrumentId, ...]


class UniverseSubscriptionPlanner:
    """Materialize universe membership changes into market data deltas."""

    def plan(
        self,
        *,
        current: Iterable[InstrumentId],
        target: Iterable[InstrumentId],
    ) -> UniverseSubscriptionDelta:
        """Return deterministic subscribe/unsubscribe deltas for internal IDs."""
        current_ids = set(current)
        target_ids = set(target)
        return UniverseSubscriptionDelta(
            subscribe=_sorted_ids(target_ids - current_ids),
            unsubscribe=_sorted_ids(current_ids - target_ids),
        )


@dataclass(frozen=True, slots=True)
class PhysicalSubscriptionKey:
    """Deduplication key for provider-facing subscriptions."""

    source_id: str
    instrument_id: InstrumentId
    stream_type: SourceStreamType
    source_timeframe: str

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_timeframe.strip():
            raise ValueError("source_timeframe must not be empty")


def logical_key(subscription: LogicalSubscription) -> LogicalSubscriptionKey:
    """Return the logical fan-out key for a subscription."""

    return LogicalSubscriptionKey(
        instrument_id=subscription.instrument_id,
        requested_timeframe=subscription.requested_timeframe,
        stream_type=subscription.stream_type,
    )


def plan_physical_subscription(
    subscription: LogicalSubscription,
    *,
    capabilities: MarketDataFeedCapabilities,
) -> PhysicalSubscriptionKey:
    """Map one logical subscription to its provider source subscription."""

    if subscription.stream_type is not SourceStreamType.BAR:
        raise ValueError("only bar subscriptions are supported")
    return PhysicalSubscriptionKey(
        source_id=capabilities.source_id,
        instrument_id=subscription.instrument_id,
        stream_type=subscription.stream_type,
        source_timeframe=capabilities.source_timeframe_for(subscription.requested_timeframe),
    )


def _sorted_ids(instrument_ids: Iterable[InstrumentId]) -> tuple[InstrumentId, ...]:
    return tuple(sorted(set(instrument_ids), key=lambda item: item.value))


__all__ = [
    "LogicalSubscription",
    "LogicalSubscriptionKey",
    "MarketDataSubscriptionEvent",
    "MarketDataSubscriptionEventType",
    "PhysicalSubscriptionKey",
    "SourceStreamType",
    "UniverseSubscriptionDelta",
    "UniverseSubscriptionPlanner",
    "logical_key",
    "plan_physical_subscription",
]
