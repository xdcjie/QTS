"""Backtest runner for config-driven historical runs.

Thin orchestrator: ``BacktestPipeline`` owns the catalog + engine
wiring; this module owns the streaming-summary side effects and the
``BacktestRun`` result shape returned to API/CLI callers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestStreamResult
from qts.backtest.pipeline import BacktestPipeline


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

    pipeline = BacktestPipeline.from_yaml(config_path)
    engine, inputs = pipeline.build_engine()
    result = engine.run_streaming(output_dir, compact_events=True)
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
