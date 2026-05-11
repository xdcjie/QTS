"""Research backtest runner for config-driven historical runs."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from qts.backtest.config import BacktestRunConfig
from qts.backtest.engine import BacktestEngine, BacktestResult
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
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, HighestVolumeFutureContractSelector
from qts.registry.symbol_resolution import StaticSymbolResolver
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class ResearchBacktestRun:
    """Output of a research backtest runner invocation."""

    result: BacktestResult
    report_path: Path
    dataset_stats: dict[str, dict[str, int]]


def run_research_backtest(
    config_path: Path,
    *,
    output_dir: Path = Path("runs/backtests"),
) -> ResearchBacktestRun:
    """Run a research backtest from YAML config and write a report JSON artifact."""

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
    return ResearchBacktestRun(result=result, report_path=report_path, dataset_stats=dataset_stats)


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


def _exchange_timezone_for(dataset: HistoricalDataset) -> str | None:
    if dataset.exchange_timezone is not None:
        return dataset.exchange_timezone
    if dataset.chain is not None:
        return dataset.chain.timezone
    return None


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


__all__ = ["ResearchBacktestRun", "run_research_backtest"]
