"""Research backtest runner for config-driven GC/SI runs."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from qts.backtest.config import BacktestRunConfig
from qts.backtest.engine import BacktestEngine, BacktestResult
from qts.core.ids import InstrumentId
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.data.historical.gc_si import load_gc_si_catalog
from qts.data.provenance import DatasetMetadata
from qts.domain.market_data import Bar
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
    catalog = load_gc_si_catalog(config.dataset_root)
    bars, dataset_stats = _load_configured_bars(config, catalog)
    strategy = _load_strategy(config.strategy_class, config.strategy_params)
    metadata = _dataset_metadata(config)
    result = BacktestEngine.from_config(
        config,
        bars=bars,
        strategy=strategy,
        dataset_metadata=metadata,
    ).run()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{result.run_id.value}.json"
    report_path.write_text(result.report.to_json(), encoding="utf-8")
    return ResearchBacktestRun(result=result, report_path=report_path, dataset_stats=dataset_stats)


def _load_configured_bars(
    config: BacktestRunConfig,
    catalog: Any,
) -> tuple[tuple[Bar, ...], dict[str, dict[str, int]]]:
    requested = set(config.symbols)
    bars: list[Bar] = []
    stats: dict[str, dict[str, int]] = {}
    for root in config.roots:
        dataset = catalog.datasets[root]
        stream = iter_historical_bars(
            dataset.csv_path,
            dataset.chain,
            timeframe=config.timeframe,
            start=config.start,
            end=config.end,
        )
        bars.extend(
            bar for bar in stream if bar.instrument_id.value.rsplit(".", 1)[-1] in requested
        )
        stats[root] = stream.stats.as_dict()
    return tuple(bars), stats


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


def _dataset_metadata(config: BacktestRunConfig) -> tuple[DatasetMetadata, ...]:
    return tuple(
        DatasetMetadata(
            dataset_id=f"{root}-{config.timeframe}-{config.start.isoformat()}-{config.end.isoformat()}",
            source=str(config.dataset_root / "data" / f"{root.lower()}.csv"),
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
