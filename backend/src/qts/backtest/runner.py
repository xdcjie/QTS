"""Backtest runner for config-driven historical runs."""

from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from qts.backtest.engine import BacktestEngine, BacktestStreamResult
from qts.data.historical.catalog import (
    HistoricalCatalog,
    HistoricalCatalogLoadConfig,
)
from qts.data.sources.replay_market_data_source import ReplayMarketDataSource
from qts.runtime.config import BacktestRuntimeConfig
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class BacktestRun:
    """Output of a backtest runner invocation."""

    result: BacktestStreamResult
    manifest_path: Path
    summary_path: Path
    artifact_paths: dict[str, Path]
    dataset_stats: dict[str, dict[str, int]]

    @property
    def processed_bars(self) -> int:
        """Perform processed_bars."""
        return self.result.processed_bars

    @property
    def report_hash(self) -> str:
        """Perform report_hash."""
        return self.result.report_hash


def run_backtest(
    config_path: Path,
    *,
    output_dir: Path = Path("runs/backtests"),
) -> BacktestRun:
    """Run a backtest and write partitioned streaming artifacts."""

    config = BacktestRuntimeConfig.from_yaml(config_path)
    catalog = HistoricalCatalog.load(_catalog_load_config(config))
    inputs = ReplayMarketDataSource(config, catalog).build()
    strategy = _load_strategy(config.strategy_class, config.strategy_params)
    result = BacktestEngine.from_config(
        config,
        bars=inputs.bars,
        strategy=strategy,
        instrument_registry=inputs.instrument_registry,
        dataset_metadata=inputs.dataset_metadata,
        future_roll_registry=inputs.future_roll_registry,
        exchange_timezone_by_instrument=inputs.exchange_timezone_by_instrument,
        contract_multipliers=inputs.contract_multipliers,
    ).run_streaming(output_dir)
    summary_path = output_dir / f"{result.run_id.value}.summary.json"
    summary_path.write_text(
        json.dumps(
            _streaming_summary_payload(
                result,
                config_path=config_path,
                manifest_path=result.manifest_path,
                dataset_stats=inputs.dataset_stats,
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return BacktestRun(
        result=result,
        manifest_path=result.manifest_path,
        summary_path=summary_path,
        artifact_paths={kind: Path(path) for kind, path in result.artifact_paths.items()},
        dataset_stats=inputs.dataset_stats,
    )


def _catalog_load_config(config: BacktestRuntimeConfig) -> HistoricalCatalogLoadConfig:
    """Perform _catalog_load_config."""
    if config.market_data.config_path is None or config.market_data.catalog is None:
        raise RuntimeError("market data reference is partially configured")
    return HistoricalCatalogLoadConfig.from_historical_market_data_config(
        config.market_data.config_path,
        catalog=config.market_data.catalog,
        roots=config.roots,
        instrument_ids=config.instrument_ids,
        requested_timeframe=config.timeframe,
    )


def _load_strategy(strategy_class: str, params: dict[str, Any]) -> Strategy:
    """Perform _load_strategy."""
    module_name, separator, class_name = strategy_class.partition(":")
    if not separator:
        module_name, _, class_name = strategy_class.rpartition(".")
    if not module_name or not class_name:
        raise ValueError("strategy_class must be 'module:Class' or 'module.Class'")
    module = _import_strategy_module(module_name)
    strategy_type = _strategy_type_from_module(module, class_name)
    return strategy_type(**params)


def _import_strategy_module(module_name: str) -> ModuleType:
    """Load a module that defines the requested strategy class."""
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        module_path = Path(*module_name.split(".")).with_suffix(".py")
        if not module_path.exists():
            raise
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def _strategy_type_from_module(module: ModuleType, class_name: str) -> type[Strategy]:
    """Extract the strategy class from a strategy module."""
    strategy_type = vars(module).get(class_name)
    if strategy_type is None:
        raise ValueError(f"strategy class '{class_name}' not found in module '{module.__name__}'")
    if not isinstance(strategy_type, type):
        raise TypeError(f"{class_name} in module '{module.__name__}' is not a class")
    if not issubclass(strategy_type, Strategy):
        raise TypeError(
            f"{class_name} in module '{module.__name__}' must subclass qts.strategy_sdk.Strategy"
        )
    return strategy_type


def _streaming_summary_payload(
    result: BacktestStreamResult,
    *,
    config_path: Path,
    manifest_path: Path,
    dataset_stats: dict[str, dict[str, int]],
) -> dict[str, Any]:
    """Perform _streaming_summary_payload."""
    processed_rows = sum(item["rows_seen"] for item in dataset_stats.values())
    emitted_bars = sum(item["bars_emitted"] for item in dataset_stats.values())
    excluded_spreads = sum(item["spreads_excluded"] for item in dataset_stats.values())
    contracts_excluded = sum(item.get("contracts_excluded", 0) for item in dataset_stats.values())
    return {
        "schema_version": "1",
        "run_id": result.run_id.value,
        "config_path": str(config_path),
        "status": "completed",
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
    "run_backtest",
]
