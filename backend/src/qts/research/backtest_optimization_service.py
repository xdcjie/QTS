"""Backtest + parameter-optimization research service.

Owns the single/matrix backtest runs and the optimizer sweep + walk-forward /
failure-window validation workflows extracted from ``ResearchSession``
(QTS-FINAL-011), so the facade keeps no backtest/optimization orchestration
directly. Only the three config values it needs (backtest config path, output
root, objective metric) are injected, not the whole session.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestStreamResult
from qts.backtest.pipeline import BacktestPipeline
from qts.research.optimizer.constraints import OptimizationConstraint
from qts.research.optimizer.failure_veto import (
    FailureWindow,
    FailureWindowVetoJob,
    FailureWindowVetoRunner,
    FailureWindowVetoSummary,
)
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.walk_forward import (
    BacktestWalkForwardValidationJob,
    BacktestWalkForwardValidationRunner,
    WalkForwardPlan,
    WalkForwardValidationSummary,
)


class BacktestOptimizationService:
    """Owns single/matrix backtests and optimizer sweep + validation reruns."""

    def __init__(
        self,
        *,
        backtest_config_path: Path,
        output_root: Path,
        objective_metric: str,
    ) -> None:
        """Create the service bound to the backtest config + output + objective."""
        self._backtest_config_path = backtest_config_path
        self._output_root = output_root
        self._objective_metric = objective_metric

    def parameter_grid(self, parameters: Mapping[str, Sequence[Any]]) -> ParameterGrid:
        """Return a stable optimizer parameter grid from notebook inputs."""

        spaces: list[ParameterSpace] = []
        for name, values in parameters.items():
            value_tuple = tuple(values)
            if not value_tuple:
                raise ValueError("parameter values must not be empty")
            spaces.append(ParameterSpace(name=str(name), values=value_tuple))
        return ParameterGrid(*spaces)

    def run_backtest(
        self,
        *,
        backtest_config_path: str | Path | None = None,
        end: datetime | None = None,
        materialized_replay_cache_dir: Path | None = None,
        start: datetime | None = None,
        strategy_params: Mapping[str, Any] | None = None,
        output_dir: Path | None = None,
    ) -> BacktestStreamResult:
        """Run one backtest through the shared ``BacktestPipeline``."""

        if (start is None) != (end is None):
            raise ValueError("start and end must be provided together")
        pipeline = BacktestPipeline.from_yaml(
            Path(backtest_config_path)
            if backtest_config_path is not None
            else self._backtest_config_path
        )
        if materialized_replay_cache_dir is not None:
            pipeline = pipeline.with_materialized_replay_cache(materialized_replay_cache_dir)
        if start is not None and end is not None:
            pipeline = pipeline.with_date_range(start=start, end=end)
        if strategy_params:
            pipeline = pipeline.with_strategy_params(strategy_params)
        engine, _bundle = pipeline.build_engine()
        return engine.run_streaming(
            output_dir or self._output_root / "single-run",
            compact_events=True,
        )

    def run_backtest_matrix(
        self,
        *,
        base_strategy_params: Mapping[str, Any],
        candidates: Sequence[Mapping[str, Any]],
        metrics: Sequence[str],
        output_root: Path,
        periods: Sequence[Mapping[str, Any]],
        backtest_config_path: str | Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Run a candidate/period backtest matrix through one cached pipeline."""

        base_pipeline = BacktestPipeline.from_yaml(
            Path(backtest_config_path)
            if backtest_config_path is not None
            else self._backtest_config_path
        )
        if materialized_replay_cache_dir is not None:
            base_pipeline = base_pipeline.with_materialized_replay_cache(
                materialized_replay_cache_dir
            )
        base_pipeline.catalog()
        rows: list[dict[str, Any]] = []
        for period in periods:
            period_name = str(period["name"])
            start = period["start"]
            end = period["end"]
            if not isinstance(start, datetime) or not isinstance(end, datetime):
                raise TypeError("backtest matrix periods must contain datetime start/end")
            period_pipeline = base_pipeline.with_date_range(start=start, end=end)
            for candidate in candidates:
                candidate_name = str(candidate["name"])
                candidate_params = candidate.get("strategy_params", {})
                if not isinstance(candidate_params, Mapping):
                    raise TypeError("backtest matrix candidate strategy_params must be a mapping")
                strategy_params = {**dict(base_strategy_params), **dict(candidate_params)}
                run_pipeline = period_pipeline.with_strategy_params(strategy_params)
                engine, _bundle = run_pipeline.build_engine()
                result = engine.run_streaming(
                    output_root / period_name / candidate_name,
                    compact_events=True,
                )
                manifest_path = Path(result.manifest_path)
                manifest_metrics = self._manifest_metrics(manifest_path)
                row = {
                    "candidate": candidate_name,
                    "manifest_path": str(manifest_path),
                    "period": period_name,
                    "processed_bars": result.processed_bars,
                    "strategy_params": strategy_params,
                    "trading_bars": result.trading_bars,
                }
                row.update({metric: manifest_metrics.get(metric) for metric in metrics})
                rows.append(row)
        return tuple(rows)

    @staticmethod
    def _manifest_metrics(manifest_path: Path) -> dict[str, str]:
        if not manifest_path.exists():
            return {}
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        metrics = payload.get("metrics", {})
        if not isinstance(metrics, Mapping):
            return {}
        return {str(key): str(value) for key, value in metrics.items()}

    def optimize(
        self,
        *,
        parameters: Mapping[str, Sequence[Any]],
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> tuple[OptimizationResult, ...]:
        """Run a parameter sweep through ``BacktestPipelineRunner``."""

        return BacktestPipelineRunner().run(
            BacktestPipelineJob(
                base_config_path=self._backtest_config_path,
                parameter_grid=self.parameter_grid(parameters),
                output_root=output_root or self._output_root / "optimizer",
                objective_metric=objective_metric or self._objective_metric,
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )

    def validate_optimizer_walk_forward(
        self,
        *,
        candidate_parameters: Sequence[Mapping[str, Any]],
        plan: WalkForwardPlan,
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: Mapping[str, Any] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> WalkForwardValidationSummary:
        """Rerun selected optimizer candidates across walk-forward windows."""
        results = BacktestWalkForwardValidationRunner().run(
            BacktestWalkForwardValidationJob(
                base_config_path=self._backtest_config_path,
                candidate_parameters=tuple(dict(parameters) for parameters in candidate_parameters),
                objective_metric=objective_metric or self._objective_metric,
                output_root=output_root or self._output_root / "walk-forward",
                plan=plan,
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )
        return WalkForwardValidationSummary.from_results(
            results,
            constraints=constraints,
            capital_metric_config=(
                None if capital_metric_config is None else dict(capital_metric_config)
            ),
        )

    def validate_optimizer_failure_window_veto(
        self,
        *,
        candidate_parameters: Sequence[Mapping[str, Any]],
        windows: Sequence[FailureWindow],
        report_only_windows: Sequence[FailureWindow] = (),
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: Mapping[str, Any] | None = None,
        objective_metric: str | None = None,
        output_root: Path | None = None,
        materialized_replay_cache_dir: Path | None = None,
    ) -> FailureWindowVetoSummary:
        """Rerun selected optimizer candidates across failure-veto windows."""
        results = FailureWindowVetoRunner().run(
            FailureWindowVetoJob(
                base_config_path=self._backtest_config_path,
                candidate_parameters=tuple(dict(parameters) for parameters in candidate_parameters),
                objective_metric=objective_metric or self._objective_metric,
                output_root=output_root or self._output_root / "failure-veto",
                windows=tuple(windows),
                report_only_windows=tuple(report_only_windows),
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )
        return FailureWindowVetoSummary.from_results(
            results,
            constraints=constraints,
            capital_metric_config=(
                None if capital_metric_config is None else dict(capital_metric_config)
            ),
        )


__all__ = ["BacktestOptimizationService"]
