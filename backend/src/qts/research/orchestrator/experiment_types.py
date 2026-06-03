"""Experiment value records for the research orchestrator.

The job, trial-result, and experiment-result dataclasses (with their payload
(de)serialization) extracted from ResearchExperimentRunner (QTS-FINAL-011) so the
records and the orchestration logic have separate owners.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qts.research.orchestrator.trial_helpers import (
    _mapping,
)

_BACKTEST_PIPELINE_MODE = "backtest_pipeline"
_EXECUTION_MODES = frozenset({_BACKTEST_PIPELINE_MODE})


@dataclass(frozen=True, slots=True)
class ResearchExperimentJob:
    """One bounded experiment job with deterministic trial inputs."""

    job_id: str
    generation_id: str
    manifest_payload: Mapping[str, Any]
    output_root: Path
    trials: tuple[Mapping[str, Any], ...]
    attempt: int = 1
    parent_job_id: str | None = None
    execution_mode: str = _BACKTEST_PIPELINE_MODE
    equity_curve_sample_interval: int = 1

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id is required")
        if not self.generation_id.strip():
            raise ValueError("generation_id is required")
        if self.attempt < 1:
            raise ValueError("attempt must be positive")
        execution_mode = str(self.execution_mode).strip()
        if execution_mode not in _EXECUTION_MODES:
            raise ValueError(f"unsupported execution_mode: {self.execution_mode}")
        if (
            isinstance(self.equity_curve_sample_interval, bool)
            or self.equity_curve_sample_interval < 1
        ):
            raise ValueError("equity_curve_sample_interval must be a positive integer")
        object.__setattr__(self, "execution_mode", execution_mode)
        object.__setattr__(self, "manifest_payload", dict(self.manifest_payload))
        object.__setattr__(self, "output_root", Path(self.output_root))
        object.__setattr__(self, "trials", tuple(dict(trial) for trial in self.trials))

    @property
    def output_dir(self) -> Path:
        """Return the deterministic directory owned by this job."""

        return self.output_root / self.generation_id / self.job_id

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic queue/job payload."""

        return {
            "attempt": self.attempt,
            "equity_curve_sample_interval": self.equity_curve_sample_interval,
            "execution_mode": self.execution_mode,
            "generation_id": self.generation_id,
            "job_id": self.job_id,
            "manifest_payload": dict(self.manifest_payload),
            "output_root": str(self.output_root),
            "parent_job_id": self.parent_job_id,
            "trials": [dict(trial) for trial in self.trials],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchExperimentJob:
        """Restore an experiment job from queue state."""

        trials = payload.get("trials")
        if not isinstance(trials, Sequence) or isinstance(trials, str):
            raise ValueError("trials must be a sequence")
        return cls(
            job_id=cls._text(payload, "job_id"),
            generation_id=cls._text(payload, "generation_id"),
            manifest_payload=_mapping(payload, "manifest_payload"),
            output_root=Path(cls._text(payload, "output_root")),
            trials=tuple(_mapping(trial, "trial") for trial in trials),
            attempt=cls._int(payload.get("attempt", 1), "attempt"),
            parent_job_id=(
                None if payload.get("parent_job_id") is None else str(payload["parent_job_id"])
            ),
            execution_mode=str(payload.get("execution_mode", _BACKTEST_PIPELINE_MODE)),
            equity_curve_sample_interval=cls._int(
                payload.get("equity_curve_sample_interval", 1),
                "equity_curve_sample_interval",
            ),
        )

    @staticmethod
    def _text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    @staticmethod
    def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return dict(value)

    @staticmethod
    def _int(value: Any, field_name: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        return value


@dataclass(frozen=True, slots=True)
class ResearchTrialResult:
    """Artifact paths and status for one experiment trial."""

    trial_id: str
    status: str
    manifest_hash: str
    manifest_path: Path
    data_quality_path: Path
    reproducibility_path: Path
    metrics_path: Path
    failures_path: Path | None = None
    evidence_bundle_id: str | None = None
    validation_artifact_paths: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in {"succeeded", "failed"}:
            raise ValueError(f"unsupported trial status: {self.status}")
        object.__setattr__(
            self,
            "validation_artifact_paths",
            {str(key): str(value) for key, value in self.validation_artifact_paths.items()},
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready trial result."""

        return {
            "data_quality_path": str(self.data_quality_path),
            "evidence_bundle_id": self.evidence_bundle_id,
            "failures_path": None if self.failures_path is None else str(self.failures_path),
            "manifest_hash": self.manifest_hash,
            "manifest_path": str(self.manifest_path),
            "metrics_path": str(self.metrics_path),
            "reproducibility_path": str(self.reproducibility_path),
            "status": self.status,
            "trial_id": self.trial_id,
            "validation_artifact_paths": dict(self.validation_artifact_paths),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchTrialResult:
        """Restore a trial result from queue state."""

        failures_path = payload.get("failures_path")
        evidence_bundle_id = payload.get("evidence_bundle_id")
        return cls(
            trial_id=cls._text(payload, "trial_id"),
            status=cls._text(payload, "status"),
            manifest_hash=cls._text(payload, "manifest_hash"),
            manifest_path=Path(cls._text(payload, "manifest_path")),
            data_quality_path=Path(cls._text(payload, "data_quality_path")),
            reproducibility_path=Path(cls._text(payload, "reproducibility_path")),
            metrics_path=Path(cls._text(payload, "metrics_path")),
            failures_path=None if failures_path is None else Path(str(failures_path)),
            evidence_bundle_id=(None if evidence_bundle_id is None else str(evidence_bundle_id)),
            validation_artifact_paths=_mapping(
                payload.get("validation_artifact_paths", {}),
                "validation_artifact_paths",
            ),
        )

    @staticmethod
    def _text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    @staticmethod
    def _mapping(value: Any, field_name: str) -> Mapping[str, str]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return {str(key): str(item) for key, item in value.items()}


@dataclass(frozen=True, slots=True)
class ResearchExperimentResult:
    """Deterministic experiment-run artifact index."""

    job_id: str
    generation_id: str
    status: str
    output_dir: Path
    workflow_summary_path: Path
    candidate_results_path: Path
    failures_path: Path
    metrics_path: Path
    data_quality_path: Path
    reproducibility_path: Path
    audit_log_path: Path
    trials: tuple[ResearchTrialResult, ...]

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready result payload."""

        return {
            "audit_log_path": str(self.audit_log_path),
            "candidate_results_path": str(self.candidate_results_path),
            "data_quality_path": str(self.data_quality_path),
            "failures_path": str(self.failures_path),
            "generation_id": self.generation_id,
            "job_id": self.job_id,
            "metrics_path": str(self.metrics_path),
            "output_dir": str(self.output_dir),
            "reproducibility_path": str(self.reproducibility_path),
            "status": self.status,
            "trials": [trial.to_payload() for trial in self.trials],
            "workflow_summary_path": str(self.workflow_summary_path),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ResearchExperimentResult:
        """Restore an experiment result from queue state."""

        trials = payload.get("trials")
        if not isinstance(trials, Sequence) or isinstance(trials, str):
            raise ValueError("trials must be a sequence")
        return cls(
            job_id=cls._text(payload, "job_id"),
            generation_id=cls._text(payload, "generation_id"),
            status=cls._text(payload, "status"),
            output_dir=Path(cls._text(payload, "output_dir")),
            workflow_summary_path=Path(cls._text(payload, "workflow_summary_path")),
            candidate_results_path=Path(cls._text(payload, "candidate_results_path")),
            failures_path=Path(cls._text(payload, "failures_path")),
            metrics_path=Path(cls._text(payload, "metrics_path")),
            data_quality_path=Path(cls._text(payload, "data_quality_path")),
            reproducibility_path=Path(cls._text(payload, "reproducibility_path")),
            audit_log_path=Path(cls._text(payload, "audit_log_path")),
            trials=tuple(
                ResearchTrialResult.from_payload(_mapping(trial, "trial")) for trial in trials
            ),
        )

    @staticmethod
    def _text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    @staticmethod
    def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return dict(value)


@dataclass(frozen=True, slots=True)
class _TrialExecutionArtifacts:
    metrics_payload: Mapping[str, Any]
    manifest_hash: str
    manifest_path: Path | None = None
    manifest_payload: Mapping[str, Any] | None = None
    manifest_fields: Mapping[str, Any] | None = None
    artifact_paths: Mapping[str, Path] | None = None


__all__ = [
    "ResearchExperimentJob",
    "ResearchExperimentResult",
    "ResearchTrialResult",
]
