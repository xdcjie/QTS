"""Backtest-config-driven parameter sweep.

Routes every combination through the same ``BacktestPipeline`` that
``scripts/run_backtest.py`` uses. The optimizer's only job is to vary
``strategy_params`` across a grid; all instrument/calendar/cost/risk
wiring stays identical to a single-run backtest, which preserves
backtest/optimizer parity.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from time import monotonic
from typing import Any

from qts.backtest.pipeline import BacktestPipeline
from qts.research.optimizer.parameter_space import ParameterGrid
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.runner import extract_objective_from_manifest


@dataclass(frozen=True, slots=True)
class BacktestPipelineJob:
    """Optimizer job rooted in a ``configs/backtest.yaml``-style file.

    Per combination the runner derives a sibling ``BacktestPipeline``
    whose ``strategy_params`` merge the grid values on top of the base
    config; the catalog is shared across combinations.
    """

    base_config_path: Path
    parameter_grid: ParameterGrid
    output_root: Path
    objective_metric: str = "sharpe_ratio"
    materialized_replay_cache_dir: Path | None = None
    equity_curve_sample_interval: int = 1

    def __post_init__(self) -> None:
        if not self.objective_metric.strip():
            raise ValueError("objective_metric must not be empty")
        if (
            isinstance(self.equity_curve_sample_interval, bool)
            or self.equity_curve_sample_interval < 1
        ):
            raise ValueError("equity_curve_sample_interval must be a positive integer")
        if self.materialized_replay_cache_dir is not None:
            object.__setattr__(
                self,
                "materialized_replay_cache_dir",
                Path(self.materialized_replay_cache_dir),
            )
        if not self.base_config_path.exists():
            raise FileNotFoundError(f"base backtest config not found: {self.base_config_path}")


class BacktestPipelineRunner:
    """Iterate a parameter grid through the shared backtest pipeline."""

    def run(self, job: BacktestPipelineJob) -> tuple[OptimizationResult, ...]:
        """Run every combination and return ranked results."""
        job.output_root.mkdir(parents=True, exist_ok=True)
        base_pipeline = BacktestPipeline.from_yaml(job.base_config_path)
        if job.materialized_replay_cache_dir is not None:
            base_pipeline = base_pipeline.with_materialized_replay_cache(
                job.materialized_replay_cache_dir
            )
        base_pipeline.catalog()  # warm the cached catalog before the loop
        results: list[OptimizationResult] = []
        total_runs = job.parameter_grid.size()
        sweep_started_at = monotonic()
        for index, combination in enumerate(job.parameter_grid):
            run_dir = job.output_root / f"run-{index:04d}"
            run_pipeline = base_pipeline.with_strategy_params(combination)
            engine, _bundle = run_pipeline.build_engine()
            started_at = monotonic()
            stream_result = run_streaming_backtest(
                engine,
                run_dir,
                equity_curve_sample_interval=job.equity_curve_sample_interval,
            )
            elapsed_seconds = Decimal(str(round(monotonic() - started_at, 6)))
            bars_per_second = _bars_per_second(
                processed_bars=stream_result.processed_bars,
                elapsed_seconds=elapsed_seconds,
            )
            _write_optimizer_progress(
                completed_runs=index + 1,
                total_runs=total_runs,
                sweep_started_at=sweep_started_at,
                processed_bars=stream_result.processed_bars,
                elapsed_seconds=elapsed_seconds,
                bars_per_second=bars_per_second,
            )
            manifest_path = Path(stream_result.manifest_path)
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            objective_value = extract_objective_from_manifest(payload, job.objective_metric)
            results.append(
                OptimizationResult(
                    parameters=dict(combination),
                    manifest_path=manifest_path,
                    manifest_hash=str(payload.get("manifest_hash", "")),
                    objective_value=objective_value,
                    processed_bars=stream_result.processed_bars,
                    trading_bars=stream_result.trading_bars,
                    elapsed_seconds=elapsed_seconds,
                    bars_per_second=bars_per_second,
                    equity_curve_sample_interval=job.equity_curve_sample_interval,
                )
            )
        return tuple(sorted(results, key=lambda r: r.objective_value, reverse=True))


def run_streaming_backtest(
    engine: Any,
    output_dir: Path,
    *,
    equity_curve_sample_interval: int,
) -> Any:
    if equity_curve_sample_interval == 1:
        return engine.run_streaming(output_dir, compact_events=True)
    return engine.run_streaming(
        output_dir,
        compact_events=True,
        equity_curve_sample_interval=equity_curve_sample_interval,
    )


def _bars_per_second(*, processed_bars: int, elapsed_seconds: Decimal) -> Decimal:
    if elapsed_seconds <= 0:
        return Decimal("0")
    return Decimal(processed_bars) / elapsed_seconds


def _write_optimizer_progress(
    *,
    completed_runs: int,
    total_runs: int,
    sweep_started_at: float,
    processed_bars: int,
    elapsed_seconds: Decimal,
    bars_per_second: Decimal,
) -> None:
    sweep_elapsed = monotonic() - sweep_started_at
    avg_run_seconds = sweep_elapsed / completed_runs if completed_runs else 0.0
    eta_seconds = avg_run_seconds * max(total_runs - completed_runs, 0)
    print(  # noqa: T201 - interactive optimizer progress is written to stderr.
        "optimizer "
        f"trial={completed_runs}/{total_runs} "
        f"processed_bars={processed_bars:,} "
        f"elapsed={_format_seconds(float(elapsed_seconds))} "
        f"bars_per_second={float(bars_per_second):,.0f} "
        f"sweep_elapsed={_format_seconds(sweep_elapsed)} "
        f"eta={_format_seconds(eta_seconds)}",
        file=sys.stderr,
    )


def _format_seconds(seconds: float) -> str:
    rounded = int(max(seconds, 0.0))
    if rounded < 60:
        return f"{rounded}s"
    minutes, seconds_part = divmod(rounded, 60)
    if minutes < 60:
        return f"{minutes}m{seconds_part:02d}s"
    hours, minutes_part = divmod(minutes, 60)
    return f"{hours}h{minutes_part:02d}m"


__all__ = ["BacktestPipelineJob", "BacktestPipelineRunner"]
