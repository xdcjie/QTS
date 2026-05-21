"""Failure-window veto validation for selected optimizer candidates."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.pipeline import BacktestPipeline
from qts.research.optimizer.constraints import OptimizationConstraint
from qts.research.optimizer.result import OptimizationResult
from qts.research.optimizer.runner import extract_objective_from_manifest
from qts.research.optimizer.validation import OptimizerValidationSummary


@dataclass(frozen=True, slots=True)
class FailureWindow:
    """One adverse optimizer validation window."""

    name: str
    start: date
    end: date
    report_only: bool = False

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("failure window name must not be empty")
        if self.start >= self.end:
            raise ValueError("failure window start must be before end")

    def to_metadata(self) -> dict[str, str | bool]:
        """Return a deterministic JSON-ready representation."""
        return {
            "end": self.end.isoformat(),
            "name": self.name,
            "report_only": self.report_only,
            "start": self.start.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class FailureWindowVetoJob:
    """Backtest-pipeline failure-window veto validation job."""

    base_config_path: Path
    candidate_parameters: tuple[dict[str, Any], ...]
    objective_metric: str
    output_root: Path
    windows: tuple[FailureWindow, ...]
    report_only_windows: tuple[FailureWindow, ...] = ()

    def __init__(
        self,
        *,
        base_config_path: Path,
        candidate_parameters: Iterable[dict[str, Any]],
        objective_metric: str,
        output_root: Path,
        windows: Iterable[FailureWindow],
        report_only_windows: Iterable[FailureWindow] = (),
    ) -> None:
        candidates = tuple(dict(parameters) for parameters in candidate_parameters)
        if not candidates:
            raise ValueError("candidate_parameters must not be empty")
        if not objective_metric.strip():
            raise ValueError("objective_metric must not be empty")
        veto_windows = tuple(
            FailureWindow(
                name=window.name,
                start=window.start,
                end=window.end,
                report_only=False,
            )
            for window in windows
        )
        if not veto_windows:
            raise ValueError("FailureWindowVetoJob requires at least one veto window")
        report_windows = tuple(
            FailureWindow(
                name=window.name,
                start=window.start,
                end=window.end,
                report_only=True,
            )
            for window in report_only_windows
        )
        window_names = [window.name for window in (*veto_windows, *report_windows)]
        duplicate_names = tuple(
            sorted({name for name in window_names if window_names.count(name) > 1})
        )
        if duplicate_names:
            raise ValueError(
                "duplicate window names are not allowed: " + ", ".join(duplicate_names)
            )
        object.__setattr__(self, "base_config_path", Path(base_config_path))
        object.__setattr__(self, "candidate_parameters", candidates)
        object.__setattr__(self, "objective_metric", objective_metric)
        object.__setattr__(self, "output_root", Path(output_root))
        object.__setattr__(self, "windows", veto_windows)
        object.__setattr__(self, "report_only_windows", report_windows)


@dataclass(frozen=True, slots=True)
class FailureWindowVetoResult:
    """One selected candidate result for one failure-window rerun."""

    candidate_index: int
    candidate_id: str
    window_name: str
    start: date
    end: date
    report_only: bool
    result: OptimizationResult


class FailureWindowVetoRunner:
    """Rerun selected optimizer candidates across veto and report-only windows."""

    def run(self, job: FailureWindowVetoJob) -> tuple[FailureWindowVetoResult, ...]:
        """Run selected candidates on every configured failure window."""
        job.output_root.mkdir(parents=True, exist_ok=True)
        base_pipeline = BacktestPipeline.from_yaml(job.base_config_path)
        base_pipeline.catalog()
        results: list[FailureWindowVetoResult] = []
        for window in (*job.windows, *job.report_only_windows):
            window_pipeline = base_pipeline.with_date_range(
                start=_date_boundary(window.start),
                end=_date_boundary(window.end),
            )
            window_kind = "report-only" if window.report_only else "veto"
            for index, parameters in enumerate(job.candidate_parameters):
                run_dir = job.output_root / window.name / window_kind / f"run-{index:04d}"
                run_pipeline = window_pipeline.with_strategy_params(parameters)
                engine, _bundle = run_pipeline.build_engine()
                stream_result = engine.run_streaming(run_dir, compact_events=True)
                manifest_path = Path(stream_result.manifest_path)
                payload = _read_manifest(manifest_path)
                results.append(
                    FailureWindowVetoResult(
                        candidate_index=index,
                        candidate_id=_candidate_id(index, parameters),
                        window_name=window.name,
                        start=window.start,
                        end=window.end,
                        report_only=window.report_only,
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
class FailureWindowVetoSummary:
    """Candidate-level promotion decision from failure-window evidence."""

    accepted_candidates: tuple[dict[str, Any], ...]
    rejected_candidates: tuple[dict[str, Any], ...]
    veto_windows: tuple[dict[str, Any], ...]
    report_only_windows: tuple[dict[str, Any], ...]

    @classmethod
    def from_results(
        cls,
        results: Sequence[FailureWindowVetoResult],
        constraints: Iterable[OptimizationConstraint] = (),
        *,
        capital_metric_config: dict[str, Any] | None = None,
    ) -> FailureWindowVetoSummary:
        """Build candidate-level veto evidence from failure-window reruns."""
        materialized_constraints = tuple(constraints)
        candidate_windows: dict[str, list[dict[str, Any]]] = {}
        candidate_indexes: dict[str, int] = {}
        candidate_parameters: dict[str, dict[str, Any]] = {}
        veto_windows: list[dict[str, Any]] = []
        report_only_windows: list[dict[str, Any]] = []

        for item in results:
            summary = OptimizerValidationSummary.from_results(
                (item.result,),
                materialized_constraints,
                capital_metric_config=capital_metric_config,
            )
            payload = summary.to_payload()
            evidence = {
                "accepted_count": payload["accepted_count"],
                "accepted_runs": payload["accepted_runs"],
                "candidate_id": item.candidate_id,
                "candidate_index": item.candidate_index,
                "end": item.end.isoformat(),
                "rejected_count": payload["rejected_count"],
                "rejections": payload["rejections"],
                "report_only": item.report_only,
                "run_count": payload["run_count"],
                "start": item.start.isoformat(),
                "window_name": item.window_name,
            }
            candidate_indexes.setdefault(item.candidate_id, item.candidate_index)
            candidate_parameters.setdefault(
                item.candidate_id,
                _json_safe_parameters(item.result.parameters),
            )
            candidate_windows.setdefault(item.candidate_id, []).append(evidence)
            if item.report_only:
                report_only_windows.append(evidence)
            else:
                veto_windows.append(evidence)

        accepted_candidates: list[dict[str, Any]] = []
        rejected_candidates: list[dict[str, Any]] = []
        for candidate_id, windows in candidate_windows.items():
            failed_veto_windows = tuple(
                window["window_name"]
                for window in windows
                if not window["report_only"] and int(window["rejected_count"]) > 0
            )
            candidate_evidence: dict[str, Any] = {
                "candidate_id": candidate_id,
                "candidate_index": candidate_indexes[candidate_id],
                "parameters": candidate_parameters[candidate_id],
                "windows": tuple(windows),
            }
            if failed_veto_windows:
                rejected_candidates.append(
                    {**candidate_evidence, "failed_veto_windows": failed_veto_windows}
                )
            else:
                accepted_candidates.append(candidate_evidence)

        return cls(
            accepted_candidates=tuple(accepted_candidates),
            rejected_candidates=tuple(rejected_candidates),
            veto_windows=tuple(veto_windows),
            report_only_windows=tuple(report_only_windows),
        )

    @property
    def candidate_count(self) -> int:
        """Return the number of selected candidates represented in evidence."""
        return len(self.accepted_candidates) + len(self.rejected_candidates)

    @property
    def decision(self) -> dict[str, Any]:
        """Return the promotion decision payload."""
        accepted = bool(self.accepted_candidates)
        return {
            "accepted": accepted,
            "reasons": () if accepted else ("no selected candidate survived failure-window veto",),
        }

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready payload."""
        return {
            "accepted_candidates": self.accepted_candidates,
            "candidate_count": self.candidate_count,
            "decision": self.decision,
            "rejected_candidates": self.rejected_candidates,
            "report_only_windows": self.report_only_windows,
            "veto_windows": self.veto_windows,
        }


def _date_boundary(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"failure-window veto manifest must be a JSON object: {path}")
    return payload


def _candidate_id(index: int, parameters: dict[str, Any]) -> str:
    payload = _json_safe_parameters(parameters)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]
    return f"candidate-{index:04d}-{digest}"


def _json_safe_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    return {
        str(name): _json_safe_parameter_value(value, path=str(name))
        for name, value in parameters.items()
    }


def _json_safe_parameter_value(value: Any, *, path: str) -> Any:
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"optimizer parameter {path} must be finite")
        return str(value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"optimizer parameter {path} must be finite")
        return value
    if isinstance(value, (list, tuple)):
        return [
            _json_safe_parameter_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"unsupported optimizer parameter value at {path}: {type(value).__name__}")


__all__ = [
    "FailureWindow",
    "FailureWindowVetoJob",
    "FailureWindowVetoResult",
    "FailureWindowVetoRunner",
    "FailureWindowVetoSummary",
]
