"""Live or paper market-data source boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime
from qts.data.adapters.ibkr_market_data import (
    IbkrMarketDataAdapter,
    IbkrMarketDataSubscription,
)
from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
from qts.data.subscriptions import (
    LogicalSubscription,
    LogicalSubscriptionKey,
    MarketDataSubscriptionEvent,
    MarketDataSubscriptionEventType,
    SourceStreamType,
    logical_key,
)
from qts.data.transports.ibkr_tws_market_data_transport import (
    IbkrBarPayload,
    IbkrMarketDataTypePayload,
    IbkrQuotePayload,
    IbkrTickPayload,
)
from qts.domain.market_data import Bar, Quote, Tick


@dataclass(frozen=True, slots=True)
class StreamingMarketDataSubscription:
    """Source-owned live/paper subscription state."""

    logical: LogicalSubscription
    broker_symbol: str
    source_id: str
    max_age: timedelta
    subscribed_at: datetime

    def __post_init__(self) -> None:
        if not self.broker_symbol.strip():
            raise ValueError("broker_symbol must not be empty")
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if self.max_age <= timedelta(0):
            raise ValueError("max_age must be positive")
        require_aware_datetime(self.subscribed_at, name="subscribed_at")


@dataclass(frozen=True, slots=True)
class StreamingMarketDataDegradation:
    """Data-source degradation signal for stale live/paper market data."""

    instrument_id: InstrumentId
    subscription: LogicalSubscriptionKey
    observed_at: datetime
    age: timedelta
    max_age: timedelta
    reason: str = "stale_market_data"

    def __post_init__(self) -> None:
        require_aware_datetime(self.observed_at, name="observed_at")
        if self.age <= self.max_age:
            raise ValueError("age must exceed max_age for stale data degradation")


StreamingMarketDataSubscriptionEvent = MarketDataSubscriptionEvent
StreamingMarketDataSubscriptionEventType = MarketDataSubscriptionEventType


class StreamingMarketDataSource:
    """Owns live/paper source subscriptions and normalized callback delivery."""

    def __init__(
        self,
        *,
        adapter: IbkrMarketDataAdapter,
        default_max_age: timedelta = timedelta(seconds=30),
        max_age_by_subscription: Mapping[LogicalSubscriptionKey, timedelta] | None = None,
    ) -> None:
        """Create a streaming source for one provider adapter."""

        if default_max_age <= timedelta(0):
            raise ValueError("default_max_age must be positive")
        self._adapter = adapter
        self._default_max_age = default_max_age
        self._max_age_by_subscription = dict(max_age_by_subscription or {})
        self._subscriptions: dict[LogicalSubscriptionKey, StreamingMarketDataSubscription] = {}
        self._last_event_at: dict[LogicalSubscriptionKey, datetime] = {}
        self._stale_emitted: set[LogicalSubscriptionKey] = set()
        self._pending: list[
            Tick
            | Quote
            | Bar
            | StreamingMarketDataDegradation
            | StreamingMarketDataSubscriptionEvent
            | MarketDataPermissionEvent
        ] = []

    @property
    def permission_state(self) -> MarketDataPermissionState:
        """Return the latest provider permission state."""

        return self._adapter.permission_state

    def subscribe(
        self,
        subscription: LogicalSubscription,
        *,
        max_age: timedelta | None = None,
        subscribed_at: datetime | None = None,
    ) -> IbkrMarketDataSubscription:
        """Register a logical subscription and return the provider request."""

        provider_subscription = self._adapter.subscription_for(subscription.instrument_id)
        key = logical_key(subscription)
        effective_max_age = max_age or self._max_age_by_subscription.get(key, self._default_max_age)
        state = StreamingMarketDataSubscription(
            logical=subscription,
            broker_symbol=provider_subscription.broker_symbol,
            source_id=provider_subscription.source_id,
            max_age=effective_max_age,
            subscribed_at=subscribed_at or datetime.now(UTC),
        )
        self._subscriptions[key] = state
        self._stale_emitted.discard(key)
        self._pending.append(
            self._subscription_event(
                StreamingMarketDataSubscriptionEventType.SUBSCRIBED,
                state,
                observed_at=state.subscribed_at,
            )
        )
        return provider_subscription

    def unsubscribe(
        self,
        subscription: LogicalSubscription,
        *,
        observed_at: datetime | None = None,
    ) -> None:
        """Remove a logical source subscription."""

        key = logical_key(subscription)
        state = self._subscriptions.pop(key, None)
        self._last_event_at.pop(key, None)
        self._stale_emitted.discard(key)
        if state is not None:
            self._pending.append(
                self._subscription_event(
                    StreamingMarketDataSubscriptionEventType.UNSUBSCRIBED,
                    state,
                    observed_at=observed_at or datetime.now(UTC),
                )
            )

    def mark_resubscribed(
        self,
        subscription: LogicalSubscription,
        *,
        observed_at: datetime | None = None,
    ) -> None:
        """Record a successful provider resubscribe for an active logical subscription."""

        state = self._require_subscription(logical_key(subscription))
        self._pending.append(
            self._subscription_event(
                StreamingMarketDataSubscriptionEventType.RESUBSCRIBED,
                state,
                observed_at=observed_at or datetime.now(UTC),
            )
        )

    def resubscribe_active_subscriptions(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> tuple[StreamingMarketDataSubscriptionEvent, ...]:
        """Record provider resubscribe evidence for all active logical subscriptions."""

        effective_observed_at = observed_at or datetime.now(UTC)
        events = tuple(
            self._subscription_event(
                StreamingMarketDataSubscriptionEventType.RESUBSCRIBED,
                state,
                observed_at=effective_observed_at,
            )
            for _, state in sorted(
                self._subscriptions.items(),
                key=lambda item: (
                    item[0].instrument_id.value,
                    item[0].requested_timeframe,
                    item[0].stream_type.value,
                ),
            )
        )
        self._pending.extend(events)
        return events

    def mark_subscription_failed(
        self,
        subscription: LogicalSubscription,
        *,
        reason: str,
        observed_at: datetime | None = None,
    ) -> None:
        """Record provider subscription failure for runtime degradation handling."""

        state = self._require_subscription(logical_key(subscription))
        self._pending.append(
            self._subscription_event(
                StreamingMarketDataSubscriptionEventType.FAILED,
                state,
                observed_at=observed_at or datetime.now(UTC),
                reason=reason,
            )
        )

    def on_tick(self, payload: IbkrTickPayload) -> Tick:
        """Normalize and enqueue a raw tick callback."""

        tick = self._adapter.on_tick(payload)
        self._record_event(
            instrument_id=tick.instrument_id,
            stream_type=SourceStreamType.TICK,
            event_time=tick.time,
        )
        self._pending.append(tick)
        return tick

    def on_quote(self, payload: IbkrQuotePayload) -> Quote:
        """Normalize and enqueue a raw quote callback."""

        quote = self._adapter.on_quote(payload)
        self._record_event(
            instrument_id=quote.instrument_id,
            stream_type=SourceStreamType.QUOTE,
            event_time=quote.time,
        )
        self._pending.append(quote)
        return quote

    def on_bar(self, payload: IbkrBarPayload) -> Bar:
        """Normalize a raw bar callback and enqueue complete bars."""

        bar = self._adapter.on_bar(payload)
        self._record_event(
            instrument_id=bar.instrument_id,
            stream_type=SourceStreamType.BAR,
            event_time=bar.end_time,
        )
        if bar.is_complete:
            self._pending.append(bar)
        return bar

    def on_market_data_type(self, payload: IbkrMarketDataTypePayload) -> MarketDataPermissionEvent:
        """Normalize and enqueue a provider permission-state callback."""

        event = self._adapter.on_market_data_type(payload)
        self._pending.append(event)
        return event

    def drain(
        self, *, observed_at: datetime | None = None
    ) -> tuple[
        Tick
        | Quote
        | Bar
        | StreamingMarketDataDegradation
        | StreamingMarketDataSubscriptionEvent
        | MarketDataPermissionEvent,
        ...,
    ]:
        """Return queued events and one-shot stale-data degradation signals."""

        self._append_stale_degradations(observed_at or datetime.now(UTC))
        drained = tuple(self._pending)
        self._pending.clear()
        return drained

    def subscription_snapshot(self) -> tuple[dict[str, str], ...]:
        """Return deterministic active subscription state for recovery."""

        rows: list[dict[str, str]] = []
        for key, state in sorted(
            self._subscriptions.items(),
            key=lambda item: (item[0].instrument_id.value, item[0].requested_timeframe),
        ):
            rows.append(
                {
                    "instrument_id": key.instrument_id.value,
                    "requested_timeframe": key.requested_timeframe,
                    "stream_type": state.logical.stream_type.value,
                    "broker_symbol": state.broker_symbol,
                    "source_id": state.source_id,
                    "subscribed_at": state.subscribed_at.isoformat(),
                }
            )
        return tuple(rows)

    def _record_event(
        self,
        *,
        instrument_id: InstrumentId,
        stream_type: SourceStreamType,
        event_time: datetime,
    ) -> None:
        require_aware_datetime(event_time, name="event_time")
        for key, subscription in self._subscriptions.items():
            if (
                key.instrument_id == instrument_id
                and subscription.logical.stream_type is stream_type
            ):
                self._last_event_at[key] = event_time
                self._stale_emitted.discard(key)

    def _append_stale_degradations(self, observed_at: datetime) -> None:
        require_aware_datetime(observed_at, name="observed_at")
        for key, subscription in self._subscriptions.items():
            reference_time = self._last_event_at.get(key, subscription.subscribed_at)
            age = observed_at - reference_time
            if age <= subscription.max_age or key in self._stale_emitted:
                continue
            self._pending.append(
                StreamingMarketDataDegradation(
                    instrument_id=key.instrument_id,
                    subscription=key,
                    observed_at=observed_at,
                    age=age,
                    max_age=subscription.max_age,
                )
            )
            self._stale_emitted.add(key)

    def _require_subscription(
        self,
        key: LogicalSubscriptionKey,
    ) -> StreamingMarketDataSubscription:
        try:
            return self._subscriptions[key]
        except KeyError as exc:
            raise KeyError(f"unknown streaming market-data subscription: {key}") from exc

    @staticmethod
    def _subscription_event(
        event_type: StreamingMarketDataSubscriptionEventType,
        state: StreamingMarketDataSubscription,
        *,
        observed_at: datetime,
        reason: str | None = None,
    ) -> StreamingMarketDataSubscriptionEvent:
        return StreamingMarketDataSubscriptionEvent(
            event_type=event_type,
            source_id=state.source_id,
            instrument_id=state.logical.instrument_id,
            subscription=logical_key(state.logical),
            broker_symbol=state.broker_symbol,
            observed_at=observed_at,
            reason=reason,
        )


__all__ = [
    "StreamingMarketDataDegradation",
    "StreamingMarketDataSource",
    "StreamingMarketDataSubscription",
    "StreamingMarketDataSubscriptionEvent",
    "StreamingMarketDataSubscriptionEventType",
]
