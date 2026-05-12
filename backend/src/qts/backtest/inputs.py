"""Backtest replay input assembly."""

from __future__ import annotations

import heapq
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal

from qts.backtest.config import BacktestRunConfig
from qts.core.ids import InstrumentId
from qts.data.historical.catalog import HistoricalCatalog, HistoricalDataset
from qts.data.historical.csv_dataset import HistoricalBarStream, iter_historical_bars
from qts.data.provenance import DatasetMetadata
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, HighestVolumeFutureContractSelector
from qts.registry.instrument_registry import InstrumentRegistry


@dataclass(frozen=True, slots=True)
class BacktestInputBundle:
    """Streaming inputs and side-channel metadata required by a backtest run."""

    bars: Iterator[Bar]
    dataset_stats: dict[str, dict[str, int]]
    exchange_timezone_by_instrument: dict[InstrumentId, str]
    instrument_registry: InstrumentRegistry
    dataset_metadata: tuple[DatasetMetadata, ...]
    contract_multipliers: dict[InstrumentId, Decimal]
    future_roll_registry: FutureRollRegistry | None


class BacktestInputBuilder:
    """Build replay-ready market data, registry, and provenance inputs."""

    def __init__(self, config: BacktestRunConfig, catalog: HistoricalCatalog) -> None:
        self._config = config
        self._catalog = catalog

    def build(self) -> BacktestInputBundle:
        roll_registry = self._roll_registry()
        bars, dataset_stats, exchange_timezones = self._stream_configured_bars(
            self._catalog,
            roll_registry=roll_registry,
        )
        return BacktestInputBundle(
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
        if not self._config.roll_policy.enabled:
            return None
        return FutureRollRegistry(retain_history=len(self._config.roots) > 1)

    def _stream_configured_bars(
        self,
        catalog: HistoricalCatalog,
        *,
        roll_registry: FutureRollRegistry | None,
    ) -> tuple[Iterator[Bar], dict[str, dict[str, int]], dict[InstrumentId, str]]:
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
        return tuple(
            DatasetMetadata(
                dataset_id=(
                    f"{root}-{self._config.timeframe}-"
                    f"{self._config.start.isoformat()}-{self._config.end.isoformat()}"
                ),
                source=str(catalog.datasets[root].csv_path),
                instrument_id=self._dataset_instrument_id(root, catalog.datasets[root]),
                timeframe=self._config.timeframe,
                timezone_policy="source UTC timestamps; exchange session semantics",
                adjustment_policy="raw",
                normalization_version="historical-csv-v1",
                created_at=self._config.start,
                content_hash=None,
            )
            for root in self._config.roots
        )

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


__all__ = ["BacktestInputBuilder", "BacktestInputBundle"]
