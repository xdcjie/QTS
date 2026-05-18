"""Backtest replay input assembly."""

from __future__ import annotations

import heapq
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime
from qts.data.provenance import ReplayDataAnomalyEvent, ReplayDataAnomalyType
from qts.data.sources.replay_bundle_builder import (
    ReplayMarketDataBundle,
    ReplayMarketDataBundleBuilder,
)
from qts.data.subscriptions import (
    LogicalSubscription,
    LogicalSubscriptionKey,
    MarketDataSubscriptionEvent,
    MarketDataSubscriptionEventType,
    logical_key,
)
from qts.domain.market_data import Bar

if TYPE_CHECKING:
    from qts.data.historical.catalog import HistoricalCatalog
    from qts.runtime.config import BacktestRuntimeConfig


@dataclass(slots=True)
class ReplayClock:
    """Deterministic replay clock advanced by event visibility time."""

    current_time: datetime | None = None

    def advance_to_next_event(self, visible_at: datetime) -> datetime:
        """Advance to the next market-data event visibility timestamp."""
        require_aware_datetime(visible_at, name="visible_at")
        if self.current_time is not None and visible_at < self.current_time:
            raise ValueError("replay clock cannot move backwards")
        self.current_time = visible_at
        return visible_at


@dataclass(frozen=True, slots=True)
class ReplaySequencedEvent:
    """Replay event with deterministic ordering metadata."""

    sort_key: tuple[datetime, str, str, datetime]
    source_sequence: int
    bar: Bar

    @property
    def visible_at(self) -> datetime:
        """Return the timestamp when this event can become strategy-visible."""
        return self.bar.end_time


class ReplayEventSequencer:
    """Order replay bars by visibility time and detect stream anomalies."""

    def __init__(self, *, source_id: str = "replay") -> None:
        """Create a sequencer for one replay source."""
        if not source_id.strip():
            raise ValueError("source_id must not be empty")
        self._source_id = source_id
        self._diagnostic_events: list[ReplayDataAnomalyEvent] = []

    def sequence(
        self, bars: tuple[Bar, ...] | list[Bar] | Iterator[Bar]
    ) -> tuple[ReplaySequencedEvent, ...]:
        """Return deterministic, de-duplicated replay events."""
        events: list[ReplaySequencedEvent] = []
        seen_bars: set[tuple[InstrumentId, str, datetime, datetime]] = set()
        last_end_by_stream: dict[tuple[InstrumentId, str], datetime] = {}
        for source_sequence, bar in enumerate(tuple(bars)):
            bar_key = (bar.instrument_id, bar.timeframe, bar.start_time, bar.end_time)
            stream_key = (bar.instrument_id, bar.timeframe)
            previous_end = last_end_by_stream.get(stream_key)
            if bar_key in seen_bars:
                self._diagnostic_events.append(
                    self._diagnostic_event(
                        ReplayDataAnomalyType.DUPLICATE_DROPPED,
                        bar,
                        previous_end=previous_end,
                    )
                )
                continue
            if previous_end is not None and bar.start_time < previous_end:
                self._diagnostic_events.append(
                    self._diagnostic_event(
                        ReplayDataAnomalyType.OUT_OF_ORDER_REJECTED,
                        bar,
                        previous_end=previous_end,
                    )
                )
                continue
            if previous_end is not None and bar.start_time > previous_end:
                self._diagnostic_events.append(
                    self._diagnostic_event(
                        ReplayDataAnomalyType.GAP_DETECTED,
                        bar,
                        previous_end=previous_end,
                    )
                )
            seen_bars.add(bar_key)
            last_end_by_stream[stream_key] = bar.end_time
            events.append(
                ReplaySequencedEvent(
                    sort_key=(
                        bar.end_time,
                        bar.instrument_id.value,
                        bar.timeframe,
                        bar.start_time,
                    ),
                    source_sequence=source_sequence,
                    bar=bar,
                )
            )
        return tuple(sorted(events, key=lambda event: (event.sort_key, event.source_sequence)))

    def drain_diagnostic_events(self) -> tuple[ReplayDataAnomalyEvent, ...]:
        """Return queued replay sequencing diagnostics."""
        events = tuple(self._diagnostic_events)
        self._diagnostic_events.clear()
        return events

    def _diagnostic_event(
        self,
        anomaly_type: ReplayDataAnomalyType,
        bar: Bar,
        *,
        previous_end: datetime | None,
    ) -> ReplayDataAnomalyEvent:
        return ReplayDataAnomalyEvent(
            anomaly_type=anomaly_type,
            source_id=self._source_id,
            instrument_id=bar.instrument_id,
            timeframe=bar.timeframe,
            bar_start=bar.start_time,
            bar_end=bar.end_time,
            previous_end=previous_end,
            observed_at=bar.end_time,
        )


class SubscriptionReplayMarketDataSource:
    """Broker-like replay source that emits only active logical subscriptions."""

    def __init__(
        self,
        *,
        bars: Iterator[Bar] | tuple[Bar, ...] | list[Bar],
        source_id: str = "replay",
    ) -> None:
        if not source_id.strip():
            raise ValueError("source_id must not be empty")
        self._source_id = source_id
        self._clock = ReplayClock()
        sequencer = ReplayEventSequencer(source_id=source_id)
        sequenced_events = sequencer.sequence(bars)
        self._diagnostic_events = list(sequencer.drain_diagnostic_events())
        self._events = [
            (event.sort_key, event.source_sequence, event.bar) for event in sequenced_events
        ]
        heapq.heapify(self._events)
        self._subscriptions: dict[LogicalSubscriptionKey, datetime | None] = {}
        self._callbacks: list[Callable[[Bar], None]] = []
        self._pending_control_events: list[MarketDataSubscriptionEvent] = []
        self._closed = False

    @property
    def current_time(self) -> datetime | None:
        """Return the current replay clock frontier."""
        return self._clock.current_time

    def subscribe(
        self,
        subscription: LogicalSubscription,
        *,
        subscribed_at: datetime | None = None,
    ) -> None:
        """Register a replay subscription."""

        if subscribed_at is not None:
            require_aware_datetime(subscribed_at, name="subscribed_at")
        key = logical_key(subscription)
        self._subscriptions[key] = subscribed_at
        self._pending_control_events.append(
            self._subscription_event(
                MarketDataSubscriptionEventType.SUBSCRIBED,
                subscription=subscription,
                observed_at=subscribed_at,
            )
        )

    def unsubscribe(
        self,
        subscription: LogicalSubscription,
        *,
        observed_at: datetime | None = None,
    ) -> None:
        """Remove a replay subscription."""

        key = logical_key(subscription)
        if key not in self._subscriptions:
            return
        self._subscriptions.pop(key)
        self._pending_control_events.append(
            self._subscription_event(
                MarketDataSubscriptionEventType.UNSUBSCRIBED,
                subscription=subscription,
                observed_at=observed_at,
            )
        )

    def poll_next(self, *, as_of: datetime | None = None) -> Bar | None:
        """Return the next visible bar for active subscriptions."""

        if as_of is not None:
            require_aware_datetime(as_of, name="as_of")
        if self._closed:
            return None
        while self._events:
            _, _, next_bar = self._events[0]
            if as_of is not None and next_bar.end_time > as_of:
                return None
            _, _, bar = heapq.heappop(self._events)
            self._clock.advance_to_next_event(bar.end_time)
            if not self._is_active(bar):
                continue
            for callback in tuple(self._callbacks):
                callback(bar)
            return bar
        return None

    def on_event(self, callback: Callable[[Bar], None]) -> None:
        """Register a callback invoked for every emitted replay event."""

        self._callbacks.append(callback)

    def drain_control_events(self) -> tuple[MarketDataSubscriptionEvent, ...]:
        """Return queued replay subscription lifecycle events."""

        events = tuple(self._pending_control_events)
        self._pending_control_events.clear()
        return events

    def drain_diagnostic_events(self) -> tuple[ReplayDataAnomalyEvent, ...]:
        """Return queued replay data-quality diagnostics."""

        events = tuple(self._diagnostic_events)
        self._diagnostic_events.clear()
        return events

    def subscription_snapshot(self) -> tuple[dict[str, str | None], ...]:
        """Return deterministic active replay subscriptions for recovery."""

        rows: list[dict[str, str | None]] = []
        for key, subscribed_at in sorted(
            self._subscriptions.items(),
            key=lambda item: (item[0].instrument_id.value, item[0].requested_timeframe),
        ):
            rows.append(
                {
                    "instrument_id": key.instrument_id.value,
                    "requested_timeframe": key.requested_timeframe,
                    "subscribed_at": None if subscribed_at is None else subscribed_at.isoformat(),
                }
            )
        return tuple(rows)

    def close(self) -> None:
        """Stop emitting replay events."""

        self._closed = True
        self._callbacks.clear()
        self._pending_control_events.clear()

    def _is_active(self, bar: Bar) -> bool:
        key = LogicalSubscriptionKey(
            instrument_id=bar.instrument_id,
            requested_timeframe=bar.timeframe,
        )
        subscribed_at = self._subscriptions.get(key)
        if key not in self._subscriptions:
            return False
        return subscribed_at is None or bar.end_time >= subscribed_at

    def _subscription_event(
        self,
        event_type: MarketDataSubscriptionEventType,
        *,
        subscription: LogicalSubscription,
        observed_at: datetime | None,
    ) -> MarketDataSubscriptionEvent:
        return MarketDataSubscriptionEvent(
            event_type=event_type,
            source_id=self._source_id,
            instrument_id=subscription.instrument_id,
            subscription=logical_key(subscription),
            broker_symbol=subscription.instrument_id.value,
            observed_at=self._observed_at(observed_at),
        )

    def _observed_at(self, explicit: datetime | None) -> datetime:
        if explicit is not None:
            require_aware_datetime(explicit, name="observed_at")
            return explicit
        if self.current_time is not None:
            return self.current_time
        if self._events:
            return self._events[0][2].start_time
        return datetime.now(UTC)


class ReplayMarketDataSource:
    """Compatibility wrapper for replay market-data bundle assembly."""

    def __init__(self, config: BacktestRuntimeConfig, catalog: HistoricalCatalog) -> None:
        self._builder = ReplayMarketDataBundleBuilder(config=config, catalog=catalog)

    def build(self) -> ReplayMarketDataBundle:
        """Build replay inputs from the configured historical catalog."""

        return self._builder.build()

    @staticmethod
    def _file_content_hash(path: Path) -> str:
        """Return a stable content hash for the replay source file."""

        return ReplayMarketDataBundleBuilder.file_content_hash(path)

    @staticmethod
    def _file_row_count(path: Path) -> int:
        """Return the number of data rows in a replay CSV source file."""

        return ReplayMarketDataBundleBuilder.file_row_count(path)


__all__ = [
    "ReplayMarketDataSource",
    "ReplayMarketDataBundle",
    "SubscriptionReplayMarketDataSource",
]
