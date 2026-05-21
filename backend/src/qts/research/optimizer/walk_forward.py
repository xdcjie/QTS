"""Walk-forward split definitions for optimizer validation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
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

    def __init__(
        self,
        *,
        base_config_path: Path,
        candidate_parameters: Iterable[dict[str, Any]],
        objective_metric: str,
        output_root: Path,
        plan: WalkForwardPlan,
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


def _date_boundary(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _read_manifest(path: Path) -> dict[str, Any]:
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"walk-forward manifest must be a JSON object: {path}")
    return payload


__all__ = [
    "BacktestWalkForwardValidationJob",
    "BacktestWalkForwardValidationRunner",
    "WalkForwardPlan",
    "WalkForwardSplit",
    "WalkForwardValidationResult",
    "WalkForwardValidationSummary",
]
