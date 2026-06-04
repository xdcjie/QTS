"""Replay market-data bundle assembly."""

from __future__ import annotations

import hashlib
import heapq
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from qts.core.ids import InstrumentId
from qts.data.bars.time_grid_synthesizer import BarTimeGridSynthesizer
from qts.data.bars.timeframe import AlignmentMode, Timeframe
from qts.data.historical.catalog import HistoricalCatalog, HistoricalDataset
from qts.data.historical.csv_dataset import HistoricalBarStream, iter_historical_bars
from qts.data.provenance import DatasetMetadata
from qts.data.sessions import RegularSessionWindow
from qts.domain.instruments import AssetClass, ContractSpec, FutureSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.future_roll import (
    FirstNoticeDateFutureContractSelector,
    FutureContractRollSpec,
    FutureRollRegistry,
)
from qts.registry.instrument_registry import InstrumentRegistry
from qts.registry.providers.exchange_calendar_provider import ExchangeCalendarProvider

if TYPE_CHECKING:
    from qts.runtime.config import BacktestRuntimeConfig


@dataclass(frozen=True, slots=True)
class ReplayMarketDataBundle:
    """Streaming inputs and side-channel metadata required by a backtest run."""

    bars: Iterator[Bar]
    dataset_stats: dict[str, dict[str, int]]
    exchange_timezone_by_instrument: dict[InstrumentId, str]
    session_window_by_instrument: dict[InstrumentId, RegularSessionWindow]
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


class ReplayMarketDataBundleBuilder:
    """Assemble replay-ready market data, registry, and provenance inputs."""

    _FILE_METADATA_CACHE: ClassVar[dict[tuple[str, int, int, int, int], tuple[str, int]]] = {}

    def __init__(self, *, config: BacktestRuntimeConfig, catalog: HistoricalCatalog) -> None:
        self._config = config
        self._catalog = catalog

    def build(self) -> ReplayMarketDataBundle:
        """Build replay inputs from the configured historical catalog."""

        roll_registry = self._roll_registry()
        bars, dataset_stats, exchange_timezones, session_windows = self._stream_configured_bars(
            self._catalog,
            roll_registry=roll_registry,
        )
        return ReplayMarketDataBundle(
            bars=bars,
            dataset_stats=dataset_stats,
            exchange_timezone_by_instrument=exchange_timezones,
            session_window_by_instrument=session_windows,
            instrument_registry=self._instrument_registry_for(
                self._catalog,
                roll_registry=roll_registry,
            ),
            dataset_metadata=self._dataset_metadata(self._catalog),
            contract_multipliers=self._contract_multipliers_for(self._catalog),
            future_roll_registry=roll_registry,
        )

    def _roll_registry(self) -> FutureRollRegistry | None:
        if not self._config.roll_policy.enabled:
            return None
        return FutureRollRegistry(retain_history=True)

    def _stream_configured_bars(
        self,
        catalog: HistoricalCatalog,
        *,
        roll_registry: FutureRollRegistry | None,
    ) -> tuple[
        Iterator[Bar],
        dict[str, dict[str, int]],
        dict[InstrumentId, str],
        dict[InstrumentId, RegularSessionWindow],
    ]:
        requested = set(self._config.symbols)
        stats: dict[str, dict[str, int]] = {}
        exchange_timezones: dict[InstrumentId, str] = {}
        session_windows: dict[InstrumentId, RegularSessionWindow] = {}
        streams: list[tuple[int, Iterator[Bar]]] = []
        for root_index, root in enumerate(self._config.roots):
            dataset = catalog.datasets[root]
            rolling_root = (
                self._config.roll_policy.enabled and root in requested and dataset.chain is not None
            )
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
                contract_selector = FirstNoticeDateFutureContractSelector(
                    contracts=tuple(
                        FutureContractRollSpec(
                            symbol=contract.symbol,
                            instrument_id=dataset.chain.instrument_id_for_symbol(contract.symbol),
                            first_notice_day=contract.first_notice_day,
                            expiry=contract.expiry,
                        )
                        for contract in dataset.chain.contracts
                    ),
                    session_offset=ExchangeCalendarProvider(
                        dataset.chain.trading_calendar
                    ).session_offset,
                    active_months=dataset.chain.active_months,
                    roll_sessions_before_first_notice=(
                        self._config.roll_policy.roll_sessions_before_first_notice
                    ),
                )
            exchange_timezone = self._exchange_timezone_for(dataset)
            session_window = dataset.session_window or (
                dataset.chain.session_window() if dataset.chain is not None else None
            )
            if exchange_timezone is not None and dataset.chain is not None:
                for contract in dataset.chain.contracts:
                    exchange_timezones.setdefault(
                        dataset.chain.instrument_id_for_symbol(contract.symbol),
                        exchange_timezone,
                    )
                    if session_window is not None:
                        session_windows.setdefault(
                            dataset.chain.instrument_id_for_symbol(contract.symbol),
                            session_window,
                        )
            if exchange_timezone is not None and continuous_id is not None:
                exchange_timezones.setdefault(continuous_id, exchange_timezone)
            if session_window is not None and continuous_id is not None:
                session_windows.setdefault(continuous_id, session_window)
            source_timeframe = dataset.source_timeframe or self._config.timeframe
            stream = iter_historical_bars(
                dataset.csv_path,
                dataset.symbol_resolver,
                timeframe=source_timeframe,
                start=self._config.start,
                end=self._config.end,
                contract_selector=contract_selector,
                continuous_instrument_id=continuous_id,
                session_window=session_window,
                schema=dataset.csv_schema,
            )
            per_root = self._iter_root_bars(
                root,
                stream,
                requested=requested,
                rolling_root=rolling_root,
                roll_registry=roll_registry,
                stats=stats,
                exchange_timezones=exchange_timezones,
                exchange_timezone=exchange_timezone,
            )
            streams.append(
                (
                    root_index,
                    self._with_time_grid_synthesis(per_root, timeframe=source_timeframe),
                )
            )
        return self._merge_ordered_bar_streams(streams), stats, exchange_timezones, session_windows

    def _with_time_grid_synthesis(self, stream: Iterator[Bar], *, timeframe: str) -> Iterator[Bar]:
        """Wrap a per-root bar stream so intra-session gaps emit synthetic bars."""

        parsed = Timeframe.parse(timeframe)
        if parsed.alignment is not AlignmentMode.CLOCK:
            return stream
        return BarTimeGridSynthesizer(timeframe=timeframe).synthesize(stream)

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
        if exchange_timezone is not None:
            exchange_timezones.setdefault(bar.instrument_id, exchange_timezone)

    @staticmethod
    def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None:
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
                            asset_class=AssetClass.FUTURE,
                            root_symbol=chain.root,
                            expiry=chain.contracts[0].expiry if chain.contracts else None,
                            initial_margin_rate=chain.initial_margin_rate,
                            tradable=False,
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
                            asset_class=AssetClass.FUTURE,
                            root_symbol=contract.root,
                            expiry=contract.expiry,
                            initial_margin_rate=contract.initial_margin_rate,
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
        root_symbol: str | None = None,
        expiry: datetime | date | None = None,
        initial_margin_rate: Decimal | None = None,
        tradable: bool = True,
    ) -> Instrument:
        derivative = None
        settlement = SettlementType.CASH
        if asset_class is AssetClass.FUTURE:
            if root_symbol is None or expiry is None:
                raise ValueError("future instruments require root_symbol and expiry")
            expiry_date = expiry.date() if isinstance(expiry, datetime) else expiry
            derivative = FutureSpec(
                expiry=expiry_date,
                underlying=InstrumentId(f"FUTURE_ROOT.{exchange}.{root_symbol}"),
                root_symbol=root_symbol,
            )
            settlement = SettlementType.PHYSICAL
        return Instrument(
            instrument_id=instrument_id,
            asset_class=asset_class,
            exchange=exchange,
            currency=currency,
            contract_spec=ContractSpec(
                tick_size=tick_size,
                lot_size=Decimal("1"),
                multiplier=multiplier,
                settlement=settlement,
                calendar_id=calendar_id,
                initial_margin_rate=initial_margin_rate,
            ),
            derivative=derivative,
            tradable=tradable,
        )

    def _dataset_metadata(
        self,
        catalog: HistoricalCatalog,
    ) -> tuple[DatasetMetadata, ...]:
        metadata_entries: list[DatasetMetadata] = []
        for root in self._config.roots:
            csv_path = catalog.datasets[root].csv_path
            content_hash, row_count = self._file_content_hash_and_row_count(csv_path)
            metadata_entries.append(
                DatasetMetadata(
                    dataset_id=(
                        f"{root}-{self._config.timeframe}-"
                        f"{self._config.start.isoformat()}-{self._config.end.isoformat()}"
                    ),
                    source=str(csv_path),
                    instrument_id=self._dataset_instrument_id(root, catalog.datasets[root]),
                    timeframe=self._config.timeframe,
                    timezone_policy=catalog.datasets[root].dataset.timezone_policy,
                    adjustment_policy=catalog.datasets[root].dataset.normalization_policy,
                    normalization_version="historical-csv-v1",
                    created_at=self._config.start,
                    content_hash=content_hash,
                    row_count=row_count,
                )
            )
        return tuple(metadata_entries)

    @classmethod
    def _file_content_hash_and_row_count(cls, path: Path) -> tuple[str, int]:
        """Return SHA-256 content hash and CSV data-row count in one pass."""

        stat = path.stat()
        cache_key = (
            str(path.resolve()),
            stat.st_dev,
            stat.st_ino,
            stat.st_size,
            stat.st_mtime_ns,
        )
        cached = cls._FILE_METADATA_CACHE.get(cache_key)
        if cached is not None:
            return cached

        hasher = hashlib.sha256()
        newline_count = 0
        trailing_bytes_after_newline = 0
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                hasher.update(chunk)
                chunk_newlines = chunk.count(b"\n")
                newline_count += chunk_newlines
                if chunk.endswith(b"\n"):
                    trailing_bytes_after_newline = 0
                else:
                    last_newline = chunk.rfind(b"\n")
                    trailing_bytes_after_newline = (
                        len(chunk) - last_newline - 1 if last_newline >= 0 else 1
                    )
        total_lines = newline_count + (1 if trailing_bytes_after_newline > 0 else 0)
        result = f"sha256:{hasher.hexdigest()}", max(total_lines - 1, 0)
        cls._FILE_METADATA_CACHE[cache_key] = result
        return result

    @classmethod
    def file_content_hash(cls, path: Path) -> str:
        """Return a stable content hash for the replay source file."""

        return cls._file_content_hash_and_row_count(path)[0]

    @classmethod
    def file_row_count(cls, path: Path) -> int:
        """Return the number of data rows in a replay CSV source file."""

        return cls._file_content_hash_and_row_count(path)[1]

    @staticmethod
    def _dataset_instrument_id(root: str, dataset: HistoricalDataset) -> InstrumentId:
        if dataset.chain is None:
            return InstrumentId(f"DATASET.{root}")
        return InstrumentId(f"FUTURE.{dataset.chain.exchange}.{root}.DATASET")

    def _contract_multipliers_for(
        self,
        catalog: HistoricalCatalog,
    ) -> dict[InstrumentId, Decimal]:
        multipliers: dict[InstrumentId, Decimal] = {}
        for root in self._config.roots:
            chain = catalog.datasets[root].chain
            if chain is None:
                continue
            for contract in chain.contracts:
                multipliers[chain.instrument_id_for_symbol(contract.symbol)] = contract.multiplier
        return multipliers


__all__ = [
    "ReplayMarketDataBundle",
    "ReplayMarketDataBundleBuilder",
]
