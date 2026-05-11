"""Backtest runner for config-driven historical runs."""

from __future__ import annotations

import heapq
import importlib
import importlib.util
import json
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qts.backtest.config import BacktestRunConfig
from qts.backtest.engine import BacktestEngine, BacktestResult, BacktestStreamResult
from qts.core.ids import InstrumentId
from qts.data.historical.catalog import (
    HistoricalCatalog,
    HistoricalDataset,
    load_historical_catalog,
    load_historical_catalog_from_config,
)
from qts.data.historical.config import HistoricalDataConfig
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.data.provenance import DatasetMetadata
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, HighestVolumeFutureContractSelector
from qts.registry.instrument_registry import InstrumentRegistry
from qts.registry.symbol_resolution import StaticSymbolResolver
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class BacktestRun:
    """Output of a backtest runner invocation."""

    result: BacktestResult
    report_path: Path
    dataset_stats: dict[str, dict[str, int]]


@dataclass(frozen=True, slots=True)
class StreamingBacktestRun:
    """Output of a streaming backtest runner invocation."""

    result: BacktestStreamResult
    manifest_path: Path
    summary_path: Path
    artifact_paths: dict[str, Path]
    dataset_stats: dict[str, dict[str, int]]

    @property
    def processed_bars(self) -> int:
        return self.result.processed_bars

    @property
    def report_hash(self) -> str:
        return self.result.report_hash


def run_backtest(
    config_path: Path,
    *,
    output_dir: Path = Path("runs/backtests"),
) -> BacktestRun:
    """Run a backtest from YAML config and write a report JSON artifact."""

    config = BacktestRunConfig.from_yaml(config_path)
    historical_data_config = _historical_data_config_for(config)
    catalog = _load_catalog(config, historical_data_config=historical_data_config)
    bars, dataset_stats, roll_registry, exchange_timezones = _load_configured_bars(config, catalog)
    strategy = _load_strategy(config.strategy_class, config.strategy_params)
    metadata = _dataset_metadata(config, catalog)
    result = BacktestEngine.from_config(
        config,
        bars=bars,
        strategy=strategy,
        dataset_metadata=metadata,
        future_roll_registry=roll_registry,
        exchange_timezone_by_instrument=exchange_timezones,
    ).run()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{result.run_id.value}.json"
    report_path.write_text(result.report.to_json(), encoding="utf-8")
    return BacktestRun(result=result, report_path=report_path, dataset_stats=dataset_stats)


def run_streaming_backtest(
    config_path: Path,
    *,
    output_dir: Path = Path("runs/backtests"),
) -> StreamingBacktestRun:
    """Run a backtest and write partitioned streaming artifacts."""

    config = BacktestRunConfig.from_yaml(config_path)
    historical_data_config = _historical_data_config_for(config)
    catalog = _load_catalog(config, historical_data_config=historical_data_config)
    roll_registry = (
        FutureRollRegistry(retain_history=len(config.roots) > 1)
        if config.roll_policy.enabled
        else None
    )
    bars, dataset_stats, exchange_timezones = _stream_configured_bars(
        config,
        catalog,
        roll_registry=roll_registry,
    )
    instrument_registry = _instrument_registry_for(config, catalog, roll_registry=roll_registry)
    strategy = _load_strategy(config.strategy_class, config.strategy_params)
    metadata = _dataset_metadata(config, catalog)
    result = BacktestEngine.streaming_from_config(
        config,
        bars=bars,
        strategy=strategy,
        instrument_registry=instrument_registry,
        dataset_metadata=metadata,
        future_roll_registry=roll_registry,
        exchange_timezone_by_instrument=exchange_timezones,
    ).run_streaming(output_dir)
    summary_path = output_dir / f"{result.run_id.value}.summary.json"
    summary_path.write_text(
        json.dumps(
            _streaming_summary_payload(
                result,
                manifest_path=result.manifest_path,
                dataset_stats=dataset_stats,
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return StreamingBacktestRun(
        result=result,
        manifest_path=result.manifest_path,
        summary_path=summary_path,
        artifact_paths={kind: Path(path) for kind, path in result.artifact_paths.items()},
        dataset_stats=dataset_stats,
    )


def _historical_data_config_for(config: BacktestRunConfig) -> HistoricalDataConfig | None:
    if not config.market_data.is_configured:
        return None
    if config.market_data.config_path is None:
        raise RuntimeError("market data config path is not configured")
    return HistoricalDataConfig.from_yaml(config.market_data.config_path)


def _load_catalog(
    config: BacktestRunConfig,
    *,
    historical_data_config: HistoricalDataConfig | None,
) -> HistoricalCatalog:
    symbol_resolvers = _symbol_resolvers_from_config(
        config,
        historical_data_config=historical_data_config,
    )
    if historical_data_config is not None:
        if config.market_data.catalog is None:
            raise RuntimeError("market data catalog is not configured")
        return load_historical_catalog_from_config(
            historical_data_config,
            catalog=config.market_data.catalog,
            roots=config.roots,
            symbol_resolvers=symbol_resolvers,
            requested_timeframe=config.timeframe,
        )
    if config.dataset_root is None:
        raise RuntimeError("legacy dataset_root is not configured")
    return load_historical_catalog(
        config.dataset_root,
        roots=config.roots,
        symbol_resolvers=symbol_resolvers,
    )


def _load_configured_bars(
    config: BacktestRunConfig,
    catalog: HistoricalCatalog,
) -> tuple[
    tuple[Bar, ...],
    dict[str, dict[str, int]],
    FutureRollRegistry | None,
    dict[InstrumentId, str],
]:
    requested = set(config.symbols)
    bars: list[Bar] = []
    stats: dict[str, dict[str, int]] = {}
    exchange_timezones: dict[InstrumentId, str] = {}
    roll_registry = FutureRollRegistry() if config.roll_policy.enabled else None
    for root in config.roots:
        dataset = catalog.datasets[root]
        rolling_root = config.roll_policy.enabled and root in requested
        continuous_id: InstrumentId | None = None
        contract_selector = None
        if rolling_root:
            if dataset.chain is None:
                raise ValueError(f"rolling futures require chain metadata for root: {root}")
            assert roll_registry is not None
            continuous_id = roll_registry.register_root(
                root_symbol=root,
                exchange=dataset.chain.exchange,
                contracts=tuple(
                    dataset.chain.instrument_id_for_symbol(contract.symbol)
                    for contract in dataset.chain.contracts
                ),
            )
            contract_selector = HighestVolumeFutureContractSelector()
        source_timeframe = dataset.source_timeframe or config.timeframe
        stream = iter_historical_bars(
            dataset.csv_path,
            dataset.symbol_resolver,
            timeframe=source_timeframe,
            start=config.start,
            end=config.end,
            contract_selector=contract_selector,
            continuous_instrument_id=continuous_id,
            schema=dataset.csv_schema,
        )
        if rolling_root:
            source_bars = tuple(stream)
            assert roll_registry is not None
            for selection in stream.roll_selections:
                roll_registry.record_selection(selection)
            bars.extend(source_bars)
            _record_exchange_timezones(
                source_bars,
                exchange_timezones=exchange_timezones,
                exchange_timezone=_exchange_timezone_for(dataset),
            )
        else:
            source_bars = tuple(
                bar for bar in stream if bar.instrument_id.value.rsplit(".", 1)[-1] in requested
            )
            bars.extend(source_bars)
            _record_exchange_timezones(
                source_bars,
                exchange_timezones=exchange_timezones,
                exchange_timezone=_exchange_timezone_for(dataset),
            )
        stats[root] = stream.stats.as_dict()
    return tuple(bars), stats, roll_registry, exchange_timezones


def _stream_configured_bars(
    config: BacktestRunConfig,
    catalog: HistoricalCatalog,
    *,
    roll_registry: FutureRollRegistry | None,
) -> tuple[Iterator[Bar], dict[str, dict[str, int]], dict[InstrumentId, str]]:
    requested = set(config.symbols)
    stats: dict[str, dict[str, int]] = {}
    exchange_timezones: dict[InstrumentId, str] = {}
    streams = []
    for root_index, root in enumerate(config.roots):
        dataset = catalog.datasets[root]
        rolling_root = config.roll_policy.enabled and root in requested
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
        exchange_timezone = _exchange_timezone_for(dataset)
        if exchange_timezone is not None and dataset.chain is not None:
            for contract in dataset.chain.contracts:
                exchange_timezones.setdefault(
                    dataset.chain.instrument_id_for_symbol(contract.symbol),
                    exchange_timezone,
                )
        if exchange_timezone is not None and continuous_id is not None:
            exchange_timezones.setdefault(continuous_id, exchange_timezone)
        source_timeframe = dataset.source_timeframe or config.timeframe
        stream = iter_historical_bars(
            dataset.csv_path,
            dataset.symbol_resolver,
            timeframe=source_timeframe,
            start=config.start,
            end=config.end,
            contract_selector=contract_selector,
            continuous_instrument_id=continuous_id,
            schema=dataset.csv_schema,
        )
        streams.append(
            (
                root_index,
                _iter_root_bars(
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
    return _merge_ordered_bar_streams(streams), stats, exchange_timezones


def _iter_root_bars(
    root: str,
    stream: Any,
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
                _record_exchange_timezone(
                    bar,
                    exchange_timezones=exchange_timezones,
                    exchange_timezone=exchange_timezone,
                )
                yield bar
                continue
            if bar.instrument_id.value.rsplit(".", 1)[-1] in requested:
                _record_exchange_timezone(
                    bar,
                    exchange_timezones=exchange_timezones,
                    exchange_timezone=exchange_timezone,
                )
                yield bar
    finally:
        stats[root] = stream.stats.as_dict()


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


def _record_exchange_timezones(
    source_bars: tuple[Bar, ...],
    *,
    exchange_timezones: dict[InstrumentId, str],
    exchange_timezone: str | None,
) -> None:
    if exchange_timezone is None:
        return
    for bar in source_bars:
        exchange_timezones.setdefault(bar.instrument_id, exchange_timezone)


def _record_exchange_timezone(
    bar: Bar,
    *,
    exchange_timezones: dict[InstrumentId, str],
    exchange_timezone: str | None,
) -> None:
    if exchange_timezone is not None:
        exchange_timezones.setdefault(bar.instrument_id, exchange_timezone)


def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None:
    if dataset.exchange_timezone is not None:
        return dataset.exchange_timezone
    if dataset.chain is not None:
        return dataset.chain.timezone
    return None


def _instrument_registry_for(
    config: BacktestRunConfig,
    catalog: HistoricalCatalog,
    *,
    roll_registry: FutureRollRegistry | None,
) -> InstrumentRegistry:
    registry = InstrumentRegistry()
    requested = set(config.symbols)
    for root in config.roots:
        dataset = catalog.datasets[root]
        if dataset.chain is not None:
            chain = dataset.chain
            if config.roll_policy.enabled and root in requested:
                if roll_registry is None:
                    raise RuntimeError("roll registry is required for rolling futures")
                registry.register(
                    root,
                    _instrument_for(
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
                    _instrument_for(
                        chain.instrument_id_for_symbol(contract.symbol),
                        exchange=contract.exchange,
                        currency=contract.currency,
                        tick_size=contract.tick_size,
                        multiplier=contract.multiplier,
                        calendar_id=contract.trading_calendar,
                    ),
                )
    for symbol, instrument_id in config.instrument_ids.items():
        registry.register(
            symbol,
            _instrument_for(
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


def _load_strategy(strategy_class: str, params: dict[str, Any]) -> Strategy:
    module_name, separator, class_name = strategy_class.partition(":")
    if not separator:
        module_name, _, class_name = strategy_class.rpartition(".")
    if not module_name or not class_name:
        raise ValueError("strategy_class must be 'module:Class' or 'module.Class'")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        module_path = Path(*module_name.split(".")).with_suffix(".py")
        if not module_path.exists():
            raise
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    strategy_type = getattr(module, class_name)
    return cast(Strategy, strategy_type(**params))


def _symbol_resolvers_from_config(
    config: BacktestRunConfig,
    *,
    historical_data_config: HistoricalDataConfig | None = None,
) -> dict[str, StaticSymbolResolver]:
    if not config.instrument_ids:
        return {}
    return {
        root: StaticSymbolResolver(config.instrument_ids)
        for root in config.roots
        if not _chain_path_exists(
            config,
            root,
            historical_data_config=historical_data_config,
        )
    }


def _chain_path_exists(
    config: BacktestRunConfig,
    root: str,
    *,
    historical_data_config: HistoricalDataConfig | None,
) -> bool:
    if historical_data_config is not None:
        if config.market_data.catalog is None:
            raise RuntimeError("market data catalog is not configured")
        chain_path = historical_data_config.resolve_dataset(
            config.market_data.catalog,
            root,
        ).chain_path
        return chain_path is not None and chain_path.exists()
    if config.dataset_root is None:
        return False
    return (config.dataset_root / "chains" / f"{root}.json").exists()


def _dataset_metadata(
    config: BacktestRunConfig,
    catalog: HistoricalCatalog,
) -> tuple[DatasetMetadata, ...]:
    return tuple(
        DatasetMetadata(
            dataset_id=f"{root}-{config.timeframe}-{config.start.isoformat()}-{config.end.isoformat()}",
            source=str(catalog.datasets[root].csv_path),
            instrument_id=InstrumentId(f"FUTURE.CME.{root}.DATASET"),
            timeframe=config.timeframe,
            timezone_policy="source UTC timestamps; exchange session semantics",
            adjustment_policy="raw",
            normalization_version="historical-csv-v1",
            created_at=config.start,
            content_hash=None,
        )
        for root in config.roots
    )


def _streaming_summary_payload(
    result: BacktestStreamResult,
    *,
    manifest_path: Path,
    dataset_stats: dict[str, dict[str, int]],
) -> dict[str, Any]:
    processed_rows = sum(item["rows_seen"] for item in dataset_stats.values())
    emitted_bars = sum(item["bars_emitted"] for item in dataset_stats.values())
    excluded_spreads = sum(item["spreads_excluded"] for item in dataset_stats.values())
    contracts_excluded = sum(item.get("contracts_excluded", 0) for item in dataset_stats.values())
    return {
        "contracts_excluded": contracts_excluded,
        "processed_rows": processed_rows,
        "emitted_bars": emitted_bars,
        "excluded_spreads": excluded_spreads,
        "manifest_path": str(manifest_path),
        "report_hash": result.report_hash,
        "processed_bars": result.processed_bars,
        "warmup_bars": result.warmup_bars,
        "trading_bars": result.trading_bars,
    }


__all__ = [
    "BacktestRun",
    "StreamingBacktestRun",
    "run_backtest",
    "run_streaming_backtest",
]
