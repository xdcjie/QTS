"""Backtest replay input assembly."""

from __future__ import annotations

import csv
import hashlib
import heapq
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.core.time import require_aware_datetime
from qts.data.historical.catalog import HistoricalCatalog, HistoricalDataset
from qts.data.historical.csv_dataset import HistoricalBarStream, iter_historical_bars
from qts.data.provenance import DatasetMetadata, ReplayDataAnomalyEvent, ReplayDataAnomalyType
from qts.data.subscriptions import (
    LogicalSubscription,
    LogicalSubscriptionKey,
    MarketDataSubscriptionEvent,
    MarketDataSubscriptionEventType,
    logical_key,
)
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, HighestVolumeFutureContractSelector
from qts.registry.instrument_registry import InstrumentRegistry
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
        ordered_bars = sorted(
            enumerate(tuple(bars)),
            key=lambda item: (
                item[1].end_time,
                item[1].instrument_id.value,
                item[1].timeframe,
                item[1].start_time,
                item[0],
            ),
        )
        for source_sequence, bar in ordered_bars:
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

    def poll_next(self) -> Bar | None:
        """Return the next visible bar for active subscriptions."""

        if self._closed:
            return None
        while self._events:
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


@dataclass(frozen=True, slots=True)
class ReplayMarketDataBundle:
    """Streaming inputs and side-channel metadata required by a backtest run."""

    bars: Iterator[Bar]
    dataset_stats: dict[str, dict[str, int]]
    exchange_timezone_by_instrument: dict[InstrumentId, str]
    instrument_registry: InstrumentRegistry
    dataset_metadata: tuple[DatasetMetadata, ...]
    contract_multipliers: dict[InstrumentId, Decimal]
    future_roll_registry: FutureRollRegistry | None

    def provenance_payload_for(self, bar: Bar) -> dict[str, str | int | None]:
        """Return dataset provenance payload for a replayed market-data event."""

        for metadata in self.dataset_metadata:
            if metadata.instrument_id == bar.instrument_id and metadata.timeframe == bar.timeframe:
                return {
                    "source_id": metadata.source,
                    "dataset_id": metadata.dataset_id,
                    "provider": metadata.source,
                    "permission_state": None,
                    "adjustment_mode": metadata.adjustment_policy,
                    "content_hash": metadata.content_hash,
                    "row_count": metadata.row_count,
                }
        raise KeyError(f"missing replay provenance for bar: {bar.instrument_id} {bar.timeframe}")


class ReplayMarketDataSource:
    """Build replay-ready market data, registry, and provenance inputs."""

    def __init__(self, config: BacktestRuntimeConfig, catalog: HistoricalCatalog) -> None:
        """Perform __init__."""
        self._config = config
        self._catalog = catalog

    def build(self) -> ReplayMarketDataBundle:
        """Perform build."""
        roll_registry = self._roll_registry()
        bars, dataset_stats, exchange_timezones = self._stream_configured_bars(
            self._catalog,
            roll_registry=roll_registry,
        )
        return ReplayMarketDataBundle(
            bars=bars,
            dataset_stats=dataset_stats,
            exchange_timezone_by_instrument=exchange_timezones,
            instrument_registry=self._instrument_registry_for(
                self._catalog,
                roll_registry=roll_registry,
            ),
            dataset_metadata=self._dataset_metadata(self._catalog),
            contract_multipliers=self._contract_multipliers_for(self._catalog),
            future_roll_registry=roll_registry,
        )

    def _roll_registry(self) -> FutureRollRegistry | None:
        """Perform _roll_registry."""
        if not self._config.roll_policy.enabled:
            return None
        return FutureRollRegistry(retain_history=len(self._config.roots) > 1)

    def _stream_configured_bars(
        self,
        catalog: HistoricalCatalog,
        *,
        roll_registry: FutureRollRegistry | None,
    ) -> tuple[Iterator[Bar], dict[str, dict[str, int]], dict[InstrumentId, str]]:
        """Perform _stream_configured_bars."""
        requested = set(self._config.symbols)
        stats: dict[str, dict[str, int]] = {}
        exchange_timezones: dict[InstrumentId, str] = {}
        streams: list[tuple[int, Iterator[Bar]]] = []
        for root_index, root in enumerate(self._config.roots):
            dataset = catalog.datasets[root]
            rolling_root = self._config.roll_policy.enabled and root in requested
            continuous_id: InstrumentId | None = None
            contract_selector = None
            if rolling_root:
                if dataset.chain is None:
                    raise ValueError(f"rolling futures require chain metadata for root: {root}")
                if roll_registry is None:
                    raise RuntimeError("roll registry is required for rolling futures")
                continuous_id = roll_registry.register_root(
                    root_symbol=root,
                    exchange=dataset.chain.exchange,
                    contracts=tuple(
                        dataset.chain.instrument_id_for_symbol(contract.symbol)
                        for contract in dataset.chain.contracts
                    ),
                )
                contract_selector = HighestVolumeFutureContractSelector()
            exchange_timezone = self._exchange_timezone_for(dataset)
            if exchange_timezone is not None and dataset.chain is not None:
                for contract in dataset.chain.contracts:
                    exchange_timezones.setdefault(
                        dataset.chain.instrument_id_for_symbol(contract.symbol),
                        exchange_timezone,
                    )
            if exchange_timezone is not None and continuous_id is not None:
                exchange_timezones.setdefault(continuous_id, exchange_timezone)
            source_timeframe = dataset.source_timeframe or self._config.timeframe
            stream = iter_historical_bars(
                dataset.csv_path,
                dataset.symbol_resolver,
                timeframe=source_timeframe,
                start=self._config.start,
                end=self._config.end,
                contract_selector=contract_selector,
                continuous_instrument_id=continuous_id,
                schema=dataset.csv_schema,
            )
            streams.append(
                (
                    root_index,
                    self._iter_root_bars(
                        root,
                        stream,
                        requested=requested,
                        rolling_root=rolling_root,
                        roll_registry=roll_registry,
                        stats=stats,
                        exchange_timezones=exchange_timezones,
                        exchange_timezone=exchange_timezone,
                    ),
                )
            )
        return self._merge_ordered_bar_streams(streams), stats, exchange_timezones

    def _iter_root_bars(
        self,
        root: str,
        stream: HistoricalBarStream,
        *,
        requested: set[str],
        rolling_root: bool,
        roll_registry: FutureRollRegistry | None,
        stats: dict[str, dict[str, int]],
        exchange_timezones: dict[InstrumentId, str],
        exchange_timezone: str | None,
    ) -> Iterator[Bar]:
        """Perform _iter_root_bars."""
        recorded_roll_selections = 0
        try:
            for bar in stream:
                if rolling_root:
                    if roll_registry is None:
                        raise RuntimeError("roll registry is required for rolling futures")
                    for selection in stream.roll_selections[recorded_roll_selections:]:
                        roll_registry.record_selection(selection)
                    recorded_roll_selections = len(stream.roll_selections)
                    self._record_exchange_timezone(
                        bar,
                        exchange_timezones=exchange_timezones,
                        exchange_timezone=exchange_timezone,
                    )
                    yield bar
                    continue
                if bar.instrument_id.value.rsplit(".", 1)[-1] in requested:
                    self._record_exchange_timezone(
                        bar,
                        exchange_timezones=exchange_timezones,
                        exchange_timezone=exchange_timezone,
                    )
                    yield bar
        finally:
            stats[root] = stream.stats.as_dict()

    @staticmethod
    def _merge_ordered_bar_streams(
        streams: list[tuple[int, Iterator[Bar]]],
    ) -> Iterator[Bar]:
        """Perform _merge_ordered_bar_streams."""
        heap: list[tuple[object, int, int, Bar, Iterator[Bar]]] = []
        sequence = 0
        for root_index, stream in streams:
            try:
                bar = next(stream)
            except StopIteration:
                continue
            heapq.heappush(heap, (bar.end_time, sequence, root_index, bar, stream))
            sequence += 1
        while heap:
            _, _, root_index, bar, stream = heapq.heappop(heap)
            yield bar
            try:
                next_bar = next(stream)
            except StopIteration:
                continue
            heapq.heappush(heap, (next_bar.end_time, sequence, root_index, next_bar, stream))
            sequence += 1

    @staticmethod
    def _record_exchange_timezone(
        bar: Bar,
        *,
        exchange_timezones: dict[InstrumentId, str],
        exchange_timezone: str | None,
    ) -> None:
        """Perform _record_exchange_timezone."""
        if exchange_timezone is not None:
            exchange_timezones.setdefault(bar.instrument_id, exchange_timezone)

    @staticmethod
    def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None:
        """Perform _exchange_timezone_for."""
        if dataset.exchange_timezone is not None:
            return dataset.exchange_timezone
        if dataset.chain is not None:
            return dataset.chain.timezone
        return None

    def _instrument_registry_for(
        self,
        catalog: HistoricalCatalog,
        *,
        roll_registry: FutureRollRegistry | None,
    ) -> InstrumentRegistry:
        """Perform _instrument_registry_for."""
        registry = InstrumentRegistry()
        requested = set(self._config.symbols)
        for root in self._config.roots:
            dataset = catalog.datasets[root]
            if dataset.chain is not None:
                chain = dataset.chain
                if self._config.roll_policy.enabled and root in requested:
                    if roll_registry is None:
                        raise RuntimeError("roll registry is required for rolling futures")
                    registry.register(
                        root,
                        self._instrument_for(
                            roll_registry.continuous_instrument_id(root),
                            exchange=chain.exchange,
                            currency=chain.currency,
                            tick_size=chain.tick_size,
                            multiplier=chain.multiplier,
                            calendar_id=chain.trading_calendar,
                        ),
                    )
                for contract in chain.contracts:
                    registry.register(
                        contract.symbol,
                        self._instrument_for(
                            chain.instrument_id_for_symbol(contract.symbol),
                            exchange=contract.exchange,
                            currency=contract.currency,
                            tick_size=contract.tick_size,
                            multiplier=contract.multiplier,
                            calendar_id=contract.trading_calendar,
                        ),
                    )
        for symbol, instrument_id in self._config.instrument_ids.items():
            registry.register(
                symbol,
                self._instrument_for(
                    instrument_id,
                    exchange="BACKTEST",
                    currency="USD",
                    tick_size=Decimal("0.01"),
                    multiplier=Decimal("1"),
                    calendar_id="BACKTEST",
                    asset_class=AssetClass.EQUITY,
                ),
            )
        return registry

    @staticmethod
    def _instrument_for(
        instrument_id: InstrumentId,
        *,
        exchange: str,
        currency: str,
        tick_size: Decimal,
        multiplier: Decimal,
        calendar_id: str,
        asset_class: AssetClass = AssetClass.EQUITY,
    ) -> Instrument:
        """Perform _instrument_for."""
        return Instrument(
            instrument_id=instrument_id,
            asset_class=asset_class,
            exchange=exchange,
            currency=currency,
            contract_spec=ContractSpec(
                tick_size=tick_size,
                lot_size=Decimal("1"),
                multiplier=multiplier,
                settlement=SettlementType.CASH,
                calendar_id=calendar_id,
            ),
        )

    def _dataset_metadata(
        self,
        catalog: HistoricalCatalog,
    ) -> tuple[DatasetMetadata, ...]:
        """Perform _dataset_metadata."""
        return tuple(
            DatasetMetadata(
                dataset_id=(
                    f"{root}-{self._config.timeframe}-"
                    f"{self._config.start.isoformat()}-{self._config.end.isoformat()}"
                ),
                source=str(catalog.datasets[root].csv_path),
                instrument_id=self._dataset_instrument_id(root, catalog.datasets[root]),
                timeframe=self._config.timeframe,
                timezone_policy=catalog.datasets[root].dataset.timezone_policy,
                adjustment_policy=catalog.datasets[root].dataset.normalization_policy,
                normalization_version="historical-csv-v1",
                created_at=self._config.start,
                content_hash=self._file_content_hash(catalog.datasets[root].csv_path),
                row_count=self._file_row_count(catalog.datasets[root].csv_path),
            )
            for root in self._config.roots
        )

    @staticmethod
    def _file_content_hash(path: Path) -> str:
        """Return a stable content hash for the replay source file."""
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return f"sha256:{hasher.hexdigest()}"

    @staticmethod
    def _file_row_count(path: Path) -> int:
        """Return the number of data rows in a replay CSV source file."""
        with path.open(encoding="utf-8", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))

    @staticmethod
    def _dataset_instrument_id(root: str, dataset: HistoricalDataset) -> InstrumentId:
        """Perform _dataset_instrument_id."""
        if dataset.chain is None:
            return InstrumentId(f"DATASET.{root}")
        return InstrumentId(f"FUTURE.{dataset.chain.exchange}.{root}.DATASET")

    def _contract_multipliers_for(
        self,
        catalog: HistoricalCatalog,
    ) -> dict[InstrumentId, Decimal]:
        """Perform _contract_multipliers_for."""
        multipliers: dict[InstrumentId, Decimal] = {}
        for root in self._config.roots:
            chain = catalog.datasets[root].chain
            if chain is None:
                continue
            for contract in chain.contracts:
                multipliers[chain.instrument_id_for_symbol(contract.symbol)] = contract.multiplier
        return multipliers


__all__ = [
    "ReplayMarketDataSource",
    "ReplayMarketDataBundle",
    "SubscriptionReplayMarketDataSource",
]
