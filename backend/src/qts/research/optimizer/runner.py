"""Sequential parameter-sweep runner.

Routes every combination through ``BacktestEngine.run_streaming`` so the
optimizer cannot accidentally use a shortcut path. Results are ranked by
the configured objective metric descending.
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.research.optimizer.job import OptimizationJob
from qts.research.optimizer.result import OptimizationResult


def extract_objective_from_manifest(payload: dict[str, Any], metric_name: str) -> Decimal:
    """Pull a metric from a backtest manifest's statistics/metrics block.

    Shared by the factory-based ``OptimizationRunner`` and the
    config-driven ``BacktestPipelineRunner`` so both code paths use the
    same objective lookup contract.
    """
    for section in ("statistics", "metrics"):
        block = payload.get(section)
        if not isinstance(block, dict):
            continue
        if metric_name not in block:
            continue
        raw = block[metric_name]
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError):
            continue
    raise KeyError(
        f"manifest at {payload.get('run_id')!r} has no Decimal-parseable "
        f"objective {metric_name!r} under statistics/metrics"
    )


class OptimizationRunner:
    """Iterate a parameter grid sequentially and return ranked results."""

    def run(self, job: OptimizationJob) -> tuple[OptimizationResult, ...]:
        """Run every combination in the job's grid and return ranked results.

        Each combination produces a fresh subdirectory under
        ``job.output_root``; the resulting manifest is parsed for the
        configured objective metric.
        """
        job.output_root.mkdir(parents=True, exist_ok=True)
        results: list[OptimizationResult] = []
        for index, combination in enumerate(job.parameter_grid):
            run_dir = job.output_root / f"run-{index:04d}"
            engine = BacktestEngine(
                strategy=job.strategy_factory(combination),
                bars=list(job.bars_factory()),
                initial_cash=job.initial_cash,
            )
            stream_result = engine.run_streaming(run_dir, compact_events=True)
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


__all__ = ["OptimizationRunner", "extract_objective_from_manifest"]
