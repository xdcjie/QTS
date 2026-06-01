"""Walk-forward split definitions for optimizer validation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.backtest.pipeline import BacktestPipeline
from qts.research.optimizer.constraints import OptimizationConstraint
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.runner import extract_objective_from_manifest


@dataclass(frozen=True, slots=True)
class WalkForwardSplit:
    """One deterministic train/test window definition."""

    name: str
    train_start: date
    train_end: date
    test_start: date
    test_end: date

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("walk-forward split name must not be empty")
        if self.train_start >= self.train_end:
            raise ValueError("train_start must be before train_end")
        if self.test_start >= self.test_end:
            raise ValueError("test_start must be before test_end")
        if self.train_end > self.test_start:
            raise ValueError("train/test windows must be ordered and non-overlapping")

    def to_metadata(self) -> dict[str, str]:
        """Return a deterministic JSON-ready representation."""
        return {
            "name": self.name,
            "train_start": self.train_start.isoformat(),
            "train_end": self.train_end.isoformat(),
            "test_start": self.test_start.isoformat(),
            "test_end": self.test_end.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class WalkForwardPlan:
    """Collection of walk-forward split definitions."""

    splits: tuple[WalkForwardSplit, ...]

    def __post_init__(self) -> None:
        if not self.splits:
            raise ValueError("WalkForwardPlan requires at least one split")
        names = [split.name for split in self.splits]
        if len(set(names)) != len(names):
            raise ValueError("WalkForwardPlan split names must be unique")
        for previous, current in zip(self.splits, self.splits[1:], strict=False):
            if previous.test_end > current.train_start:
                raise ValueError("WalkForwardPlan splits must be ordered and non-overlapping")

    def to_metadata(self) -> tuple[dict[str, str], ...]:
        """Return deterministic JSON-ready split metadata."""
        return tuple(split.to_metadata() for split in self.splits)


@dataclass(frozen=True, slots=True)
class BacktestWalkForwardValidationJob:
    """Backtest-pipeline walk-forward validation job for selected candidates."""

    base_config_path: Path
    candidate_parameters: tuple[dict[str, Any], ...]
    objective_metric: str
    output_root: Path
    plan: WalkForwardPlan
    materialized_replay_cache_dir: Path | None = None

    def __init__(
        self,
        *,
        base_config_path: Path,
        candidate_parameters: Iterable[dict[str, Any]],
        objective_metric: str,
        output_root: Path,
        plan: WalkForwardPlan,
        materialized_replay_cache_dir: Path | None = None,
    ) -> None:
        candidates = tuple(dict(parameters) for parameters in candidate_parameters)
        if not candidates:
            raise ValueError("candidate_parameters must not be empty")
        if not objective_metric.strip():
            raise ValueError("objective_metric must not be empty")
        object.__setattr__(self, "base_config_path", Path(base_config_path))
        object.__setattr__(self, "candidate_parameters", candidates)
        object.__setattr__(self, "objective_metric", objective_metric)
        object.__setattr__(self, "output_root", Path(output_root))
        object.__setattr__(self, "plan", plan)
        object.__setattr__(
            self,
            "materialized_replay_cache_dir",
            None if materialized_replay_cache_dir is None else Path(materialized_replay_cache_dir),
        )


@dataclass(frozen=True, slots=True)
class WalkForwardValidationResult:
    """One candidate result for one walk-forward split phase."""

    split_name: str
    phase: str
    start: date
    end: date
    result: OptimizationResult


class BacktestWalkForwardValidationRunner:
    """Rerun selected optimizer candidates across walk-forward windows."""

    def run(
        self,
        job: BacktestWalkForwardValidationJob,
    ) -> tuple[WalkForwardValidationResult, ...]:
        """Run selected candidates on every train/test window."""
        job.output_root.mkdir(parents=True, exist_ok=True)
        base_pipeline = BacktestPipeline.from_yaml(job.base_config_path)
        if job.materialized_replay_cache_dir is not None:
            base_pipeline = base_pipeline.with_materialized_replay_cache(
                job.materialized_replay_cache_dir
            )
        base_pipeline.catalog()
        results: list[WalkForwardValidationResult] = []
        for split in job.plan.splits:
            for phase, start, end in (
                ("train", split.train_start, split.train_end),
                ("test", split.test_start, split.test_end),
            ):
                window_pipeline = base_pipeline.with_date_range(
                    start=_date_boundary(start),
                    end=_date_boundary(end),
                )
                for index, parameters in enumerate(job.candidate_parameters):
                    run_dir = job.output_root / split.name / phase / f"run-{index:04d}"
                    run_pipeline = window_pipeline.with_strategy_params(parameters)
                    engine, _bundle = run_pipeline.build_engine()
                    stream_result = engine.run_streaming(run_dir, compact_events=True)
                    manifest_path = Path(stream_result.manifest_path)
                    payload = _read_manifest(manifest_path)
                    results.append(
                        WalkForwardValidationResult(
                            split_name=split.name,
                            phase=phase,
                            start=start,
                            end=end,
                            result=OptimizationResult(
                                parameters=dict(parameters),
                                manifest_path=manifest_path,
                                manifest_hash=str(payload.get("manifest_hash", "")),
                                objective_value=extract_objective_from_manifest(
                                    payload,
                                    job.objective_metric,
                                ),
                            ),
                        )
                    )
        return tuple(results)


@dataclass(frozen=True, slots=True)
class WalkForwardValidationSummary:
    """Grouped validation evidence for walk-forward reruns."""

    windows: tuple[dict[str, Any], ...]

    @classmethod
    def from_results(
        cls,
        results: Sequence[WalkForwardValidationResult],
        *,
        constraints: Iterable[OptimizationConstraint] = (),
        capital_metric_config: dict[str, Any] | None = None,
    ) -> WalkForwardValidationSummary:
        """Build grouped validation evidence from walk-forward run results."""
        from qts.research.optimizer.validation import OptimizerValidationSummary

        groups: dict[tuple[str, str, date, date], list[OptimizationResult]] = {}
        for item in results:
            groups.setdefault((item.split_name, item.phase, item.start, item.end), []).append(
                item.result
            )
        windows: list[dict[str, Any]] = []
        for (split_name, phase, start, end), window_results in groups.items():
            summary = OptimizerValidationSummary.from_results(
                tuple(window_results),
                constraints,
                capital_metric_config=capital_metric_config,
            )
            payload = summary.to_payload()
            windows.append(
                {
                    "accepted_count": payload["accepted_count"],
                    "accepted_runs": payload["accepted_runs"],
                    "end": end.isoformat(),
                    "phase": phase,
                    "rejected_count": payload["rejected_count"],
                    "rejections": payload["rejections"],
                    "run_count": payload["run_count"],
                    "split_name": split_name,
                    "start": start.isoformat(),
                }
            )
        return cls(windows=tuple(windows))

    @property
    def run_count(self) -> int:
        """Return total walk-forward rerun count."""
        return sum(int(window["run_count"]) for window in self.windows)

    @property
    def window_count(self) -> int:
        """Return the number of validated split phases."""
        return len(self.windows)

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""
        return {
            "run_count": self.run_count,
            "window_count": self.window_count,
            "windows": list(self.windows),
        }


@dataclass(frozen=True, slots=True)
class WalkForwardRobustnessDecision:
    """Aggregate walk-forward robustness decision."""

    accepted: bool
    metrics: dict[str, Any]
    reasons: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic JSON-ready robustness evidence."""
        return {
            "accepted": self.accepted,
            "metrics": {
                name: _json_metric(value)
                for name, value in sorted(self.metrics.items(), key=lambda item: item[0])
            },
            "reasons": self.reasons,
        }


@dataclass(frozen=True, slots=True)
class WalkForwardRobustnessPolicy:
    """Validate aggregate walk-forward evidence across selected phases."""

    phases: tuple[str, ...] = ("test",)
    min_windows: int | None = None
    max_losing_windows: int | None = None
    min_window_pnl_usd: Decimal | None = None
    min_window_best_objective: Decimal | None = None
    min_total_pnl_usd: Decimal | None = None

    def __post_init__(self) -> None:
        phases = tuple(str(phase).strip() for phase in self.phases)
        if not phases or any(not phase for phase in phases):
            raise ValueError("walk-forward robustness phases must not be empty")
        object.__setattr__(self, "phases", phases)
        for name, value in (
            ("min_windows", self.min_windows),
            ("max_losing_windows", self.max_losing_windows),
        ):
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")
        min_window_pnl_usd = self._optional_decimal(
            "min_window_pnl_usd",
            self.min_window_pnl_usd,
        )
        min_window_best_objective = self._optional_decimal(
            "min_window_best_objective",
            self.min_window_best_objective,
        )
        min_total_pnl_usd = self._optional_decimal("min_total_pnl_usd", self.min_total_pnl_usd)
        object.__setattr__(self, "min_window_pnl_usd", min_window_pnl_usd)
        object.__setattr__(self, "min_window_best_objective", min_window_best_objective)
        object.__setattr__(self, "min_total_pnl_usd", min_total_pnl_usd)

    @staticmethod
    def _optional_decimal(name: str, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        parsed = Decimal(str(value))
        if not parsed.is_finite():
            raise ValueError(f"{name} must be finite")
        return parsed

    def evaluate(self, summary: WalkForwardValidationSummary) -> WalkForwardRobustnessDecision:
        """Return an aggregate robustness decision for selected windows."""
        selected = tuple(window for window in summary.windows if window.get("phase") in self.phases)
        window_pnls = tuple(self._window_pnl(window) for window in selected)
        window_objectives = tuple(self._window_best_objective(window) for window in selected)
        losing_window_count = sum(1 for pnl in window_pnls if pnl is not None and pnl < 0)
        total_pnl = sum((pnl for pnl in window_pnls if pnl is not None), Decimal("0"))
        metrics: dict[str, Any] = {
            "losing_window_count": losing_window_count,
            "total_pnl_usd": total_pnl,
            "window_count": len(selected),
        }
        if window_pnls:
            metrics["min_window_pnl_usd"] = min(
                pnl if pnl is not None else Decimal("0") for pnl in window_pnls
            )
        if window_objectives:
            metrics["min_window_best_objective"] = min(
                objective if objective is not None else Decimal("0")
                for objective in window_objectives
            )

        reasons: list[str] = []
        if self.min_windows is not None and len(selected) < self.min_windows:
            reasons.append(f"window_count={len(selected)} failed >= {self.min_windows}")
        if self.max_losing_windows is not None and losing_window_count > self.max_losing_windows:
            reasons.append(
                f"losing_window_count={losing_window_count} failed <= {self.max_losing_windows}"
            )
        if self.min_window_pnl_usd is not None:
            min_pnl = metrics.get("min_window_pnl_usd")
            if not isinstance(min_pnl, Decimal) or min_pnl < self.min_window_pnl_usd:
                reasons.append(
                    f"min_window_pnl_usd={min_pnl or 0} failed >= {self.min_window_pnl_usd}"
                )
        if self.min_window_best_objective is not None:
            min_objective = metrics.get("min_window_best_objective")
            if (
                not isinstance(min_objective, Decimal)
                or min_objective < self.min_window_best_objective
            ):
                reasons.append(
                    "min_window_best_objective="
                    f"{min_objective or 0} failed >= {self.min_window_best_objective}"
                )
        if self.min_total_pnl_usd is not None and total_pnl < self.min_total_pnl_usd:
            reasons.append(f"total_pnl_usd={total_pnl} failed >= {self.min_total_pnl_usd}")
        return WalkForwardRobustnessDecision(
            accepted=not reasons,
            metrics=metrics,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _window_pnl(window: dict[str, Any]) -> Decimal | None:
        values: list[Decimal] = []
        for run in _accepted_runs(window):
            capital_metrics = run.get("capital_metrics")
            if not isinstance(capital_metrics, dict):
                continue
            value = _optional_decimal(capital_metrics.get("pnl_usd"))
            if value is not None:
                values.append(value)
        if not values:
            return None
        return sum(values, Decimal("0"))

    @staticmethod
    def _window_best_objective(window: dict[str, Any]) -> Decimal | None:
        values = tuple(
            value
            for value in (
                _optional_decimal(run.get("objective_value")) for run in _accepted_runs(window)
            )
            if value is not None
        )
        if not values:
            return None
        return max(values)


def _date_boundary(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _read_manifest(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"walk-forward manifest must be a JSON object: {path}")
    return payload


def _accepted_runs(window: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    raw_runs = window.get("accepted_runs")
    if not isinstance(raw_runs, Sequence):
        return ()
    return tuple(run for run in raw_runs if isinstance(run, dict))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite():
        return None
    return parsed


def _json_metric(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    return value


__all__ = [
    "BacktestWalkForwardValidationJob",
    "BacktestWalkForwardValidationRunner",
    "WalkForwardPlan",
    "WalkForwardRobustnessDecision",
    "WalkForwardRobustnessPolicy",
    "WalkForwardSplit",
    "WalkForwardValidationResult",
    "WalkForwardValidationSummary",
]
