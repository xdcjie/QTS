"""Backtest-config-driven parameter sweep.

Routes every combination through the same ``BacktestPipeline`` that
``scripts/run_backtest.py`` uses. The optimizer's only job is to vary
``strategy_params`` across a grid; all instrument/calendar/cost/risk
wiring stays identical to a single-run backtest, which preserves
backtest/optimizer parity.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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

    def __post_init__(self) -> None:
        if not self.objective_metric.strip():
            raise ValueError("objective_metric must not be empty")
        if not self.base_config_path.exists():
            raise FileNotFoundError(f"base backtest config not found: {self.base_config_path}")


class BacktestPipelineRunner:
    """Iterate a parameter grid through the shared backtest pipeline."""

    def run(self, job: BacktestPipelineJob) -> tuple[OptimizationResult, ...]:
        """Run every combination and return ranked results."""
        job.output_root.mkdir(parents=True, exist_ok=True)
        base_pipeline = BacktestPipeline.from_yaml(job.base_config_path)
        base_pipeline.catalog()  # warm the cached catalog before the loop
        results: list[OptimizationResult] = []
        for index, combination in enumerate(job.parameter_grid):
            run_dir = job.output_root / f"run-{index:04d}"
            run_pipeline = base_pipeline.with_strategy_params(combination)
            engine, _bundle = run_pipeline.build_engine()
            stream_result = engine.run_streaming(run_dir)
            manifest_path = Path(stream_result.manifest_path)
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            objective_value = extract_objective_from_manifest(payload, job.objective_metric)
            results.append(
                OptimizationResult(
                    parameters=dict(combination),
                    manifest_path=manifest_path,
                    manifest_hash=str(payload.get("manifest_hash", "")),
                    objective_value=objective_value,
                )
            )
        return tuple(sorted(results, key=lambda r: r.objective_value, reverse=True))


__all__ = ["BacktestPipelineJob", "BacktestPipelineRunner"]
