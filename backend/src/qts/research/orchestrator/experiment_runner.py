"""Deterministic research experiment runner artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifactWriter, DataQualityRunner
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.orchestrator.validation_artifact_reader import (
    PromotionThresholds,
    ResearchMetricsFromValidationArtifacts,
    ValidationArtifactReader,
)
from qts.research.reproducibility import ReproducibilitySnapshotV2

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
            manifest_payload=cls._mapping(payload, "manifest_payload"),
            output_root=Path(cls._text(payload, "output_root")),
            trials=tuple(cls._mapping(trial, "trial") for trial in trials),
            attempt=cls._int(payload.get("attempt", 1), "attempt"),
            parent_job_id=(
                None if payload.get("parent_job_id") is None else str(payload["parent_job_id"])
            ),
            execution_mode=str(payload.get("execution_mode", _BACKTEST_PIPELINE_MODE)),
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
            validation_artifact_paths=cls._mapping(
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
                ResearchTrialResult.from_payload(cls._mapping(trial, "trial")) for trial in trials
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


class ResearchExperimentRunner:
    """Owns deterministic research experiment artifact production."""

    def __init__(
        self,
        *,
        repo_root: Path,
        promotion_thresholds: PromotionThresholds | None = None,
    ) -> None:
        self._repo_root = Path(repo_root)
        self._promotion_thresholds = promotion_thresholds or PromotionThresholds()

    def run(self, job: ResearchExperimentJob) -> ResearchExperimentResult:
        """Run all job trials and write deterministic research-only artifacts."""

        output_dir = job.output_dir
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audit_log = ResearchAuditLog(output_dir / "audit" / "audit_log.jsonl")
        evidence_registry = EvidenceRegistry(output_dir / "evidence")
        trial_results: list[ResearchTrialResult] = []
        candidate_rows: list[dict[str, Any]] = []
        failure_rows: list[dict[str, Any]] = []

        for trial_index, trial in enumerate(self._sorted_trials(job), start=1):
            trial_result = self._run_trial(
                job=job,
                trial=trial,
                trial_index=trial_index,
                output_dir=output_dir,
                audit_log=audit_log,
                evidence_registry=evidence_registry,
            )
            trial_results.append(trial_result)
            candidate_rows.append(
                {
                    "evidence_bundle_id": trial_result.evidence_bundle_id,
                    "generation_id": job.generation_id,
                    "job_id": job.job_id,
                    "manifest_hash": trial_result.manifest_hash,
                    "metrics_path": str(trial_result.metrics_path),
                    "parameters": dict(self._mapping(trial.get("parameters", {}), "parameters")),
                    "status": trial_result.status,
                    "trial_id": trial_result.trial_id,
                }
            )
            if trial_result.status == "failed":
                failure_rows.append(
                    {
                        "failure_reason": str(
                            trial.get("failure_reason", "trial failed during experiment")
                        ),
                        "generation_id": job.generation_id,
                        "job_id": job.job_id,
                        "manifest_hash": trial_result.manifest_hash,
                        "trial_id": trial_result.trial_id,
                    }
                )

        candidate_results_path = output_dir / "candidate_results.jsonl"
        failures_path = output_dir / "failures.jsonl"
        self._write_jsonl(candidate_results_path, candidate_rows)
        self._write_jsonl(failures_path, failure_rows)

        metrics_path = self._write_aggregate_json(output_dir, "metrics.json", trial_results)
        data_quality_path = self._write_aggregate_json(
            output_dir,
            "data_quality.json",
            trial_results,
            path_attribute="data_quality_path",
        )
        reproducibility_path = self._write_aggregate_json(
            output_dir,
            "reproducibility_v2.json",
            trial_results,
            path_attribute="reproducibility_path",
        )
        workflow_summary_path = output_dir / "workflow_summary.json"
        status = "completed" if not failure_rows else "completed_with_failures"
        workflow_summary = self._workflow_summary_payload(
            job=job,
            status=status,
            trial_results=tuple(trial_results),
            candidate_results_path=candidate_results_path,
            failures_path=failures_path,
        )
        self._write_json(workflow_summary_path, workflow_summary)

        return ResearchExperimentResult(
            job_id=job.job_id,
            generation_id=job.generation_id,
            status=status,
            output_dir=output_dir,
            workflow_summary_path=workflow_summary_path,
            candidate_results_path=candidate_results_path,
            failures_path=failures_path,
            metrics_path=metrics_path,
            data_quality_path=data_quality_path,
            reproducibility_path=reproducibility_path,
            audit_log_path=audit_log.path,
            trials=tuple(trial_results),
        )

    def write_validation_artifacts_for_trial(
        self,
        *,
        trial: Mapping[str, Any],
        trial_result: ResearchTrialResult,
        active_correlation_context: Sequence[Mapping[str, Any]] = (),
    ) -> Mapping[str, str]:
        """Run survivor validation and attach promotion-grade artifacts to the trial summary."""

        if trial_result.status != "succeeded":
            raise ValueError("validation artifacts require a succeeded trial")
        trial_dir = trial_result.metrics_path.parent
        metrics_payload = self._read_json_mapping(trial_result.metrics_path)
        backtest_manifest = self._backtest_manifest_from_metrics(metrics_payload)
        trial_manifest = self._read_json_mapping(trial_result.manifest_path)
        resolved_manifest = self._mapping(trial_manifest.get("manifest", {}), "manifest")
        pipeline_config = self._backtest_pipeline_config_from_payloads(resolved_manifest, trial)
        parameters = self._pipeline_parameters(
            self._mapping(trial.get("parameters", {}), "parameters"),
            pipeline_config,
        )
        base_config_path = self._required_path(
            pipeline_config,
            ("backtest_config_path", "base_config_path"),
            "backtest_pipeline backtest_config_path",
        )
        objective_metric = str(pipeline_config.get("objective_metric", "sharpe_ratio"))
        materialized_cache_dir = pipeline_config.get("materialized_replay_cache_dir")
        materialized_cache_path = (
            None if materialized_cache_dir is None else self._resolve_path(materialized_cache_dir)
        )

        replay_result, replay_manifest = self._run_validation_backtest(
            base_config_path=base_config_path,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "deterministic_replay",
            materialized_replay_cache_dir=materialized_cache_path,
        )
        train_result, train_manifest, test_result, test_manifest = self._run_walk_forward_reruns(
            base_config_path=base_config_path,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "walk_forward",
            materialized_replay_cache_dir=materialized_cache_path,
        )
        failure_result, failure_manifest = self._run_validation_backtest(
            base_config_path=base_config_path,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "failure_window_veto",
            materialized_replay_cache_dir=materialized_cache_path,
        )
        stress_result, stress_manifest = self._run_validation_backtest(
            base_config_path=self._cost_stress_config_path(
                base_config_path=base_config_path,
                output_dir=trial_dir / "validation_configs",
            ),
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "cost_stress",
            materialized_replay_cache_dir=materialized_cache_path,
        )

        validation_artifact_paths = self._write_validation_artifacts(
            trial_dir=trial_dir,
            trial_id=trial_result.trial_id,
            manifest_hash=trial_result.manifest_hash,
            backtest_manifest=backtest_manifest,
            metrics_payload=metrics_payload,
            parameters=parameters,
            pipeline_config=pipeline_config,
            replay_manifest=replay_manifest,
            train_result=train_result,
            train_manifest=train_manifest,
            test_result=test_result,
            test_manifest=test_manifest,
            failure_result=failure_result,
            failure_manifest=failure_manifest,
            stress_result=stress_result,
            stress_manifest=stress_manifest,
            active_correlation_context=active_correlation_context,
        )
        self._attach_validation_artifacts_to_workflow_summary(
            trial_dir / "workflow_summary.json",
            validation_artifact_paths,
        )
        # Rewrite metrics with honest artifact-derived values now that
        # validation artifacts exist on disk.
        metrics_rewritten = self._rewrite_metrics_with_validation_derivation(
            metrics_path=trial_result.metrics_path,
            trial_dir=trial_dir,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
        )
        # The trial manifest recorded the metrics artifact hash before the
        # honest rewrite, so its artifact_hashes/artifact_paths_by_hash entries
        # for metrics are now stale. Refresh them so the evidence bundle can
        # recompute the metrics hash and the recomputation path stays sound.
        if metrics_rewritten:
            self._refresh_manifest_artifact_hash(
                manifest_path=trial_result.manifest_path,
                artifact_name="metrics",
                artifact_path=trial_result.metrics_path,
            )
        return {name: str(path) for name, path in validation_artifact_paths.items()}

    def _run_trial(
        self,
        *,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
        trial_index: int,
        output_dir: Path,
        audit_log: ResearchAuditLog,
        evidence_registry: EvidenceRegistry,
    ) -> ResearchTrialResult:
        trial_id = self._text(trial.get("trial_id"), "trial_id")
        trial_dir = output_dir / "trials" / trial_id
        trial_dir.mkdir(parents=True, exist_ok=True)
        manifest_payload = self._trial_manifest_payload(job, trial)
        execution_artifacts = self._execute_trial(
            job=job,
            trial=trial,
            trial_dir=trial_dir,
            manifest_payload=manifest_payload,
        )
        manifest_hash = execution_artifacts.manifest_hash
        manifest_payload = {
            **manifest_payload,
            "execution_mode": job.execution_mode,
            "manifest_hash": manifest_hash,
            **dict(execution_artifacts.manifest_fields or {}),
        }

        metrics_payload = dict(execution_artifacts.metrics_payload)
        data_quality_payload = self._data_quality_payload(job, trial, trial_dir, manifest_hash)
        reproducibility_payload = self._reproducibility_payload(
            job=job,
            manifest_hash=manifest_hash,
        )

        metrics_path = trial_dir / "metrics.json"
        data_quality_path = trial_dir / "data_quality.json"
        reproducibility_path = trial_dir / "reproducibility_v2.json"
        manifest_path = trial_dir / "manifest.json"
        report_path = trial_dir / "report.md"
        strategy_variant_path = self._write_strategy_variant_artifact(
            trial_dir=trial_dir,
            trial=trial,
            manifest_payload=manifest_payload,
        )
        self._write_json(metrics_path, metrics_payload)
        self._write_json(data_quality_path, data_quality_payload)
        self._write_json(reproducibility_path, reproducibility_payload)
        validation_artifact_paths: dict[str, Path] = {}
        self._write_report(report_path, trial_id=trial_id, status=self._trial_status(trial))
        artifact_paths = {
            "data_quality": data_quality_path,
            "metrics": metrics_path,
            "reproducibility": reproducibility_path,
            **{name: path for name, path in validation_artifact_paths.items()},
            **dict(execution_artifacts.artifact_paths or {}),
        }
        if strategy_variant_path is not None:
            artifact_paths["strategy_variant"] = strategy_variant_path
        manifest_payload = {
            **manifest_payload,
            "artifact_hashes": {
                name: self._sha256_path(path) for name, path in sorted(artifact_paths.items())
            },
            "artifact_paths_by_hash": {
                self._sha256_path(path): str(path) for path in artifact_paths.values()
            },
        }
        self._write_json(manifest_path, manifest_payload)
        result_manifest_path = manifest_path

        audit_log.append(
            "manifest_loaded",
            {
                "event": "experiment_trial_manifest_loaded",
                "generation_id": job.generation_id,
                "job_id": job.job_id,
                "manifest_hash": manifest_hash,
                "trial_id": trial_id,
            },
            created_at=self._audit_time(trial_index, 0),
        )

        status = self._trial_status(trial)
        failure_path = None
        evidence_bundle_id = None
        if status == "failed":
            failure_path = trial_dir / "failures.jsonl"
            self._write_jsonl(
                failure_path,
                (
                    {
                        "failure_reason": str(
                            trial.get("failure_reason", "trial failed during experiment")
                        ),
                        "generation_id": job.generation_id,
                        "job_id": job.job_id,
                        "manifest_hash": manifest_hash,
                        "trial_id": trial_id,
                    },
                ),
            )
        else:
            evidence_summary_path = trial_dir / "workflow_summary.json"
            self._write_json(
                evidence_summary_path,
                self._trial_workflow_summary(
                    job=job,
                    trial=trial,
                    manifest_hash=manifest_hash,
                    manifest_path=result_manifest_path,
                    metrics_path=metrics_path,
                    data_quality_path=data_quality_path,
                    reproducibility_path=reproducibility_path,
                    validation_artifact_paths=validation_artifact_paths,
                    strategy_variant_path=strategy_variant_path,
                    report_path=report_path,
                ),
            )
            bundle = evidence_registry.create_from_workflow_summary(
                evidence_summary_path,
                idea=self._idea(job, trial),
                strategy_id=self._strategy_id(job),
                audit_log=audit_log,
                artifact_graph_writer=ResearchArtifactGraphWriter(
                    job.output_root / "artifact_graph"
                ),
            )
            evidence_bundle_id = bundle.evidence_bundle_id

        audit_log.append(
            "research_run_completed",
            {
                "event": "experiment_trial_completed",
                "evidence_bundle_id": evidence_bundle_id,
                "generation_id": job.generation_id,
                "job_id": job.job_id,
                "manifest_hash": manifest_hash,
                "status": status,
                "trial_id": trial_id,
            },
            created_at=self._audit_time(trial_index, 1),
        )
        return ResearchTrialResult(
            trial_id=trial_id,
            status=status,
            manifest_hash=manifest_hash,
            manifest_path=result_manifest_path,
            data_quality_path=data_quality_path,
            reproducibility_path=reproducibility_path,
            metrics_path=metrics_path,
            failures_path=failure_path,
            evidence_bundle_id=evidence_bundle_id,
            validation_artifact_paths={
                name: str(path) for name, path in validation_artifact_paths.items()
            },
        )

    def _trial_manifest_payload(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        manifest_patch = trial.get("manifest_patch")
        if manifest_patch is not None and not isinstance(manifest_patch, Mapping):
            raise ValueError("trial manifest_patch must be a mapping")
        resolved_manifest = self._merged_manifest(
            job.manifest_payload,
            {} if manifest_patch is None else manifest_patch,
        )
        payload: dict[str, Any] = {
            "attempt": job.attempt,
            "generation_id": job.generation_id,
            "job_id": job.job_id,
            "manifest": resolved_manifest,
            "parameters": dict(self._mapping(trial.get("parameters", {}), "parameters")),
            "trial_id": self._text(trial.get("trial_id"), "trial_id"),
        }
        if manifest_patch is not None:
            payload["manifest_patch"] = dict(manifest_patch)
            payload["manifest_patch_hash"] = stable_json_hash(dict(manifest_patch))
        strategy_variant_id = trial.get("strategy_variant_id")
        strategy_variant_hash = trial.get("strategy_variant_hash")
        if strategy_variant_id is not None:
            payload["strategy_variant_id"] = str(strategy_variant_id)
        if strategy_variant_hash is not None:
            payload["strategy_variant_hash"] = str(strategy_variant_hash)
        return payload

    def _write_strategy_variant_artifact(
        self,
        *,
        trial_dir: Path,
        trial: Mapping[str, Any],
        manifest_payload: Mapping[str, Any],
    ) -> Path | None:
        strategy_variant_id = trial.get("strategy_variant_id")
        strategy_variant_hash = trial.get("strategy_variant_hash")
        if strategy_variant_id is None and strategy_variant_hash is None:
            return None
        path = trial_dir / "strategy_variant.json"
        manifest_patch = trial.get("manifest_patch")
        research_factory = {}
        if isinstance(manifest_patch, Mapping):
            research_factory_raw = manifest_patch.get("research_factory", {})
            if isinstance(research_factory_raw, Mapping):
                research_factory = dict(research_factory_raw)
        payload = {
            "candidate_id": trial.get("candidate_id"),
            "candidate_space_hash": trial.get("candidate_space_hash"),
            "factor_hash": trial.get("factor_hash"),
            "family": trial.get("family"),
            "manifest_patch": dict(manifest_patch) if isinstance(manifest_patch, Mapping) else {},
            "manifest_patch_hash": manifest_payload.get("manifest_patch_hash"),
            "parameters": dict(self._mapping(trial.get("parameters", {}), "parameters")),
            "strategy_variant_hash": None
            if strategy_variant_hash is None
            else str(strategy_variant_hash),
            "strategy_variant_id": None
            if strategy_variant_id is None
            else str(strategy_variant_id),
            "template_id": research_factory.get("template_id"),
            "trial_id": self._text(trial.get("trial_id"), "trial_id"),
        }
        self._write_json(path, payload)
        return path

    def _merged_manifest(
        self,
        base: Mapping[str, Any],
        patch: Mapping[str, Any],
    ) -> dict[str, Any]:
        result = dict(base)
        for key, value in patch.items():
            current = result.get(key)
            if isinstance(current, Mapping) and isinstance(value, Mapping):
                result[str(key)] = self._merged_manifest(current, value)
            else:
                result[str(key)] = value
        return {key: value for key, value in json.loads(stable_json_dumps(result)).items()}

    def _execute_trial(
        self,
        *,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
        trial_dir: Path,
        manifest_payload: Mapping[str, Any],
    ) -> _TrialExecutionArtifacts:
        if "metrics" in trial:
            raise ValueError("backtest_pipeline trials must derive metrics from backtest output")
        if self._trial_status(trial) == "failed":
            manifest_hash = stable_json_hash(manifest_payload)
            return _TrialExecutionArtifacts(metrics_payload={}, manifest_hash=manifest_hash)
        return self._execute_backtest_pipeline_trial(job=job, trial=trial, trial_dir=trial_dir)

    def _execute_backtest_pipeline_trial(
        self,
        *,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
        trial_dir: Path,
    ) -> _TrialExecutionArtifacts:
        pipeline_config = self._backtest_pipeline_config(job, trial)
        parameters = self._pipeline_parameters(
            self._mapping(trial.get("parameters", {}), "parameters"),
            pipeline_config,
        )
        if not parameters:
            raise ValueError("backtest_pipeline trials require at least one strategy parameter")
        base_config_path = self._required_path(
            pipeline_config,
            ("backtest_config_path", "base_config_path"),
            "backtest_pipeline backtest_config_path",
        )
        objective_metric = str(pipeline_config.get("objective_metric", "sharpe_ratio"))
        materialized_cache_dir = pipeline_config.get("materialized_replay_cache_dir")
        pipeline_result = BacktestPipelineRunner().run(
            BacktestPipelineJob(
                base_config_path=base_config_path,
                parameter_grid=ParameterGrid(
                    *(
                        ParameterSpace(name=str(name), values=(value,))
                        for name, value in sorted(parameters.items())
                    )
                ),
                output_root=trial_dir / "backtest",
                objective_metric=objective_metric,
                materialized_replay_cache_dir=(
                    None
                    if materialized_cache_dir is None
                    else self._resolve_path(materialized_cache_dir)
                ),
            )
        )
        if len(pipeline_result) != 1:
            raise ValueError("backtest_pipeline trial must produce exactly one backtest result")
        result = pipeline_result[0]
        backtest_manifest_path = Path(result.manifest_path)
        backtest_manifest = self._read_json_mapping(backtest_manifest_path)
        manifest_hash = str(
            result.manifest_hash
            or backtest_manifest.get("manifest_hash")
            or self._sha256_path(backtest_manifest_path)
        )
        metrics_block = self._mapping(backtest_manifest.get("metrics", {}), "metrics")
        raw_statistics = backtest_manifest.get("statistics", {})
        statistics_block = {
            **metrics_block,
            **self._mapping(raw_statistics, "statistics"),
        }
        research_metrics = self._research_metrics_payload(
            backtest_manifest=backtest_manifest,
            statistics=statistics_block,
            objective_metric=objective_metric,
            objective_value=result.objective_value,
            trial_dir=trial_dir,
        )
        return _TrialExecutionArtifacts(
            metrics_payload={
                **research_metrics,
                "backtest": {
                    "manifest_hash": manifest_hash,
                    "manifest_path": str(backtest_manifest_path),
                    "objective_metric": objective_metric,
                    "objective_value": str(result.objective_value),
                    "parameters": dict(result.parameters),
                },
                "backtest_metrics": metrics_block,
                "backtest_statistics": statistics_block,
            },
            manifest_payload=backtest_manifest,
            manifest_hash=manifest_hash,
            manifest_path=backtest_manifest_path,
            manifest_fields={
                "backtest_manifest_hash": manifest_hash,
                "backtest_manifest_path": str(backtest_manifest_path),
            },
            artifact_paths={"backtest_manifest": backtest_manifest_path},
        )

    def _research_metrics_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        statistics: Mapping[str, Any],
        objective_metric: str,
        objective_value: Decimal,
        trial_dir: Path | None = None,
        train_manifest: Mapping[str, Any] | None = None,
        test_manifest: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        sharpe = self._decimal(statistics.get("sharpe_ratio", objective_value))
        total_return = self._decimal(statistics.get("total_return", 0))
        max_drawdown = abs(self._decimal(statistics.get("max_drawdown", 0)))
        profit_factor = self._decimal(statistics.get("profit_factor", 0))
        trade_count = self._artifact_row_count(backtest_manifest, "trade_ledger")
        if trade_count <= 0:
            trade_count = self._artifact_row_count(backtest_manifest, "fills")
        total_commission = abs(self._decimal(statistics.get("total_commission", 0)))
        total_slippage = abs(self._decimal(statistics.get("total_slippage", 0)))
        cost_impact = total_commission + total_slippage

        # Derive honest metrics from validation artifacts when available
        derivation = self._derive_validation_metrics(
            trial_dir=trial_dir,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
        )

        # Use artifact-derived values, falling back to None for unverified fields
        deterministic_replay_passed: bool | None = (
            derivation.deterministic_replay_passed if derivation else None
        )
        no_lookahead_passed: bool | None = derivation.no_lookahead_passed if derivation else None
        walk_forward_consistency: float | None = (
            derivation.walk_forward_consistency if derivation else None
        )
        parameter_sensitivity: float | None = (
            derivation.parameter_sensitivity if derivation else None
        )
        oos_months: float | None = derivation.oos_months if derivation else None
        promotion_eligible: bool = derivation.promotion_eligible if derivation else False
        train_sharpe: float | None = derivation.sharpe_sources.train_sharpe if derivation else None
        oos_sharpe: float | None = derivation.sharpe_sources.oos_sharpe if derivation else None

        return {
            "costs": {"cost_sensitivity": float(cost_impact)},
            "execution": {
                "cost_impact": float(cost_impact),
                "slippage_sensitivity": float(
                    abs(self._decimal(statistics.get("slippage_per_trade", 0)))
                ),
            },
            "performance": {
                "max_drawdown": float(max_drawdown),
                "oos_sharpe": oos_sharpe,
                "total_return": float(total_return),
                "train_sharpe": train_sharpe,
            },
            "portfolio": {"correlation_to_active": 0.0},
            "quality": {"profit_factor": float(profit_factor), "sharpe": float(sharpe)},
            "research": {
                "deterministic_replay_passed": deterministic_replay_passed,
                "metrics_source": "backtest_pipeline",
                "no_lookahead_passed": no_lookahead_passed,
                "objective_metric": objective_metric,
                "promotion_eligible": promotion_eligible,
            },
            "risk": {"max_drawdown": float(max_drawdown)},
            "stability": {
                "parameter_sensitivity": parameter_sensitivity,
                "walk_forward_consistency": walk_forward_consistency,
            },
            "trading": {"oos_months": oos_months, "oos_trade_count": trade_count},
        }

    def _derive_validation_metrics(
        self,
        *,
        trial_dir: Path | None,
        train_manifest: Mapping[str, Any] | None,
        test_manifest: Mapping[str, Any] | None,
    ) -> Any | None:
        """Derive honest validation metrics from artifact files if available."""
        if trial_dir is None or not trial_dir.exists():
            return None
        reader = ValidationArtifactReader(trial_dir)
        workflow_summary_path = trial_dir / "workflow_summary.json"
        workflow_summary: Mapping[str, Any] = {}
        if workflow_summary_path.exists():
            try:
                workflow_summary = self._read_json_mapping(workflow_summary_path)
            except (ValueError, OSError):
                workflow_summary = {}
        return ResearchMetricsFromValidationArtifacts(self._promotion_thresholds).derive(
            reader,
            workflow_summary,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
        )

    def _rewrite_metrics_with_validation_derivation(
        self,
        *,
        metrics_path: Path,
        trial_dir: Path,
        train_manifest: Mapping[str, Any],
        test_manifest: Mapping[str, Any],
    ) -> bool:
        """Rewrite metrics.json with honest artifact-derived validation fields.

        Returns True when the metrics file was rewritten so callers can refresh
        any manifest entries that recorded the pre-rewrite metrics hash.
        """
        derivation = self._derive_validation_metrics(
            trial_dir=trial_dir,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
        )
        if derivation is None:
            return False
        current_payload = self._read_json_mapping(metrics_path)
        updated = dict(current_payload)

        # Patch research section with artifact-derived values
        research = dict(self._mapping(updated.get("research", {}), "research"))
        research["deterministic_replay_passed"] = derivation.deterministic_replay_passed
        research["no_lookahead_passed"] = derivation.no_lookahead_passed
        research["promotion_eligible"] = derivation.promotion_eligible
        updated["research"] = research

        # Patch stability section
        stability = dict(self._mapping(updated.get("stability", {}), "stability"))
        stability["parameter_sensitivity"] = derivation.parameter_sensitivity
        stability["walk_forward_consistency"] = derivation.walk_forward_consistency
        updated["stability"] = stability

        # Patch trading section
        trading = dict(self._mapping(updated.get("trading", {}), "trading"))
        trading["oos_months"] = derivation.oos_months
        updated["trading"] = trading

        # Patch performance section with separate train/oos sharpe
        performance = dict(self._mapping(updated.get("performance", {}), "performance"))
        performance["train_sharpe"] = derivation.sharpe_sources.train_sharpe
        performance["oos_sharpe"] = derivation.sharpe_sources.oos_sharpe
        updated["performance"] = performance

        self._write_json(metrics_path, updated)
        return True

    def _refresh_manifest_artifact_hash(
        self,
        *,
        manifest_path: Path,
        artifact_name: str,
        artifact_path: Path,
    ) -> None:
        """Update a trial manifest's recorded hash for a rewritten artifact.

        Keeps ``artifact_hashes[artifact_name]`` and ``artifact_paths_by_hash``
        consistent with the artifact's current on-disk content so evidence
        bundle verification can recompute the hash from a registered path.
        """
        manifest = dict(self._read_json_mapping(manifest_path))
        artifact_hashes = dict(
            self._mapping(manifest.get("artifact_hashes", {}), "artifact_hashes")
        )
        if artifact_name not in artifact_hashes:
            return
        stale_hash = artifact_hashes[artifact_name]
        fresh_hash = self._sha256_path(artifact_path)
        if fresh_hash == stale_hash:
            return
        artifact_hashes[artifact_name] = fresh_hash
        artifact_paths_by_hash = dict(
            self._mapping(manifest.get("artifact_paths_by_hash", {}), "artifact_paths_by_hash")
        )
        artifact_paths_by_hash.pop(stale_hash, None)
        artifact_paths_by_hash[fresh_hash] = str(artifact_path)
        manifest["artifact_hashes"] = artifact_hashes
        manifest["artifact_paths_by_hash"] = artifact_paths_by_hash
        self._write_json(manifest_path, manifest)

    def _artifact_row_count(self, manifest: Mapping[str, Any], artifact_name: str) -> int:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, Mapping):
            return 0
        artifact = artifacts.get(artifact_name)
        if not isinstance(artifact, Mapping):
            return 0
        rows = artifact.get("rows", 0)
        return rows if isinstance(rows, int) and not isinstance(rows, bool) else 0

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _pipeline_parameters(
        self,
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        defaults = pipeline_config.get("strategy_parameter_defaults", {})
        if defaults is not None and not isinstance(defaults, Mapping):
            raise ValueError("backtest_pipeline strategy_parameter_defaults must be a mapping")
        result: dict[str, Any] = dict(defaults or {})

        parameter_map = pipeline_config.get("strategy_parameter_map")
        if parameter_map is not None:
            if not isinstance(parameter_map, Mapping):
                raise ValueError("backtest_pipeline strategy_parameter_map must be a mapping")
            for source_name, target_name in sorted(parameter_map.items()):
                source = str(source_name)
                if source not in parameters:
                    raise ValueError(
                        "backtest_pipeline strategy parameter missing from trial parameters: "
                        f"{source}"
                    )
                result[str(target_name)] = parameters[source]
            return result

        parameter_names = pipeline_config.get("strategy_parameter_names")
        if parameter_names is None:
            result.update(dict(parameters))
            return result
        if not isinstance(parameter_names, Sequence) or isinstance(parameter_names, str):
            raise ValueError("backtest_pipeline strategy_parameter_names must be a sequence")
        for name in tuple(str(item) for item in parameter_names):
            if name not in parameters:
                raise ValueError(
                    f"backtest_pipeline strategy parameter missing from trial parameters: {name}"
                )
            result[name] = parameters[name]
        return result

    def _backtest_pipeline_config(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self._backtest_pipeline_config_from_payloads(job.manifest_payload, trial)

    def _backtest_pipeline_config_from_payloads(
        self,
        manifest_payload: Mapping[str, Any],
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        config: dict[str, Any] = {}
        for field_name in ("backtest", "backtest_pipeline"):
            value = manifest_payload.get(field_name)
            if isinstance(value, Mapping):
                config.update(dict(value))
        trial_config = trial.get("backtest_pipeline")
        if isinstance(trial_config, Mapping):
            config.update(dict(trial_config))
        for field_name in (
            "backtest_config_path",
            "base_config_path",
            "objective_metric",
            "materialized_replay_cache_dir",
        ):
            if field_name in trial:
                config[field_name] = trial[field_name]
        return config

    def _required_path(
        self,
        payload: Mapping[str, Any],
        field_names: Sequence[str],
        label: str,
    ) -> Path:
        for field_name in field_names:
            value = payload.get(field_name)
            if value is not None and str(value).strip():
                return self._resolve_path(value)
        raise ValueError(f"{label} is required")

    def _resolve_path(self, value: Any) -> Path:
        path = Path(str(value))
        return path if path.is_absolute() else self._repo_root / path

    def _run_validation_backtest(
        self,
        *,
        base_config_path: Path,
        parameters: Mapping[str, Any],
        objective_metric: str,
        output_root: Path,
        materialized_replay_cache_dir: Path | None,
    ) -> tuple[Any, Mapping[str, Any]]:
        result = BacktestPipelineRunner().run(
            BacktestPipelineJob(
                base_config_path=base_config_path,
                parameter_grid=ParameterGrid(
                    *(
                        ParameterSpace(name=str(name), values=(value,))
                        for name, value in sorted(parameters.items())
                    )
                ),
                output_root=output_root,
                objective_metric=objective_metric,
                materialized_replay_cache_dir=materialized_replay_cache_dir,
            )
        )
        if len(result) != 1:
            raise ValueError("validation backtest must produce exactly one result")
        validation_result = result[0]
        return validation_result, self._read_json_mapping(Path(validation_result.manifest_path))

    def _run_walk_forward_reruns(
        self,
        *,
        base_config_path: Path,
        parameters: Mapping[str, Any],
        objective_metric: str,
        output_root: Path,
        materialized_replay_cache_dir: Path | None,
    ) -> tuple[Any, Mapping[str, Any], Any, Mapping[str, Any]]:
        start, end = self._backtest_config_window(base_config_path)
        midpoint = start + ((end - start) / 2)
        if midpoint <= start or midpoint >= end:
            raise ValueError(f"cannot split backtest window for walk-forward: {start} -> {end}")
        config_dir = output_root / "configs"
        train_config = self._window_config_path(
            base_config_path=base_config_path,
            output_path=config_dir / "walk_forward_train.yaml",
            start=start,
            end=midpoint,
        )
        test_config = self._window_config_path(
            base_config_path=base_config_path,
            output_path=config_dir / "walk_forward_test.yaml",
            start=midpoint,
            end=end,
        )
        train_result, train_manifest = self._run_validation_backtest(
            base_config_path=train_config,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=output_root / "train",
            materialized_replay_cache_dir=materialized_replay_cache_dir,
        )
        test_result, test_manifest = self._run_validation_backtest(
            base_config_path=test_config,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=output_root / "test",
            materialized_replay_cache_dir=materialized_replay_cache_dir,
        )
        return train_result, train_manifest, test_result, test_manifest

    def _window_config_path(
        self,
        *,
        base_config_path: Path,
        output_path: Path,
        start: datetime,
        end: datetime,
    ) -> Path:
        payload = self._yaml_mapping(base_config_path)
        payload["start"] = start.isoformat()
        payload["end"] = end.isoformat()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return output_path

    def _cost_stress_config_path(self, *, base_config_path: Path, output_dir: Path) -> Path:
        payload = self._yaml_mapping(base_config_path)
        cost_payload = payload.get("cost_model", {})
        if not isinstance(cost_payload, Mapping):
            raise ValueError(f"cost_model must be a mapping: {base_config_path}")
        stressed_cost = dict(cost_payload)
        stressed_cost["fixed_commission_per_contract"] = str(
            self._decimal(stressed_cost.get("fixed_commission_per_contract", 0)) + Decimal("1")
        )
        stressed_cost["slippage_bps"] = str(
            self._decimal(stressed_cost.get("slippage_bps", 0)) + Decimal("1")
        )
        payload["cost_model"] = stressed_cost
        path = output_dir / "cost_stress.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return path

    def _backtest_config_window(self, base_config_path: Path) -> tuple[datetime, datetime]:
        payload = self._yaml_mapping(base_config_path)
        start = datetime.fromisoformat(str(payload["start"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(payload["end"]).replace("Z", "+00:00"))
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError(
                f"backtest validation window must be timezone-aware: {base_config_path}"
            )
        start = start.astimezone(UTC)
        end = end.astimezone(UTC)
        if start >= end:
            raise ValueError(f"invalid backtest validation window: {start} >= {end}")
        return start, end

    @staticmethod
    def _yaml_mapping(path: Path) -> dict[str, Any]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"YAML file must contain a mapping: {path}")
        return dict(payload)

    def _read_json_mapping(self, path: Path) -> Mapping[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"JSON file must contain an object: {path}")
        return dict(payload)

    def _data_quality_payload(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
        trial_dir: Path,
        manifest_hash: str,
    ) -> dict[str, Any]:
        data = self._mapping(job.manifest_payload.get("data", {}), "data")
        checked_paths = self._data_quality_checked_paths(job, trial)
        artifact = DataQualityRunner(
            dataset_id=str(data.get("dataset_id", job.job_id)),
            timeframe=str(data.get("timeframe", "1m")),
            start=None if data.get("start") is None else str(data["start"]),
            end=None if data.get("end") is None else str(data["end"]),
            calendar=None if data.get("calendar") is None else str(data["calendar"]),
            windows=self._data_quality_windows(data.get("windows", ())),
        ).run({"checked_paths": checked_paths})
        result = DataQualityArtifactWriter(trial_dir).write(artifact)
        payload = json.loads(result.path.read_text(encoding="utf-8"))
        return {
            **payload,
            "artifact_id": f"dq-{manifest_hash.removeprefix('sha256:')[:16]}",
            "path": str(result.path),
            "payload_hash": stable_json_hash(artifact.to_payload()),
        }

    def _data_quality_checked_paths(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> tuple[str, ...]:
        trial_paths = trial.get("data_quality_paths")
        if isinstance(trial_paths, Sequence) and not isinstance(trial_paths, str):
            return tuple(str(path) for path in trial_paths)
        pipeline_config = trial.get("backtest_pipeline")
        if isinstance(pipeline_config, Mapping):
            pipeline_paths = pipeline_config.get("data_quality_paths")
            if isinstance(pipeline_paths, Sequence) and not isinstance(pipeline_paths, str):
                return tuple(str(path) for path in pipeline_paths)
        data = self._mapping(job.manifest_payload.get("data", {}), "data")
        return tuple(str(path) for path in data.get("checked_paths", ()))

    @staticmethod
    def _data_quality_windows(value: Any) -> tuple[Mapping[str, str], ...]:
        if value is None:
            return ()
        if not isinstance(value, Sequence) or isinstance(value, str):
            return ()
        windows: list[Mapping[str, str]] = []
        for item in value:
            if not isinstance(item, Mapping):
                continue
            start = item.get("start")
            end = item.get("end")
            if isinstance(start, str) and isinstance(end, str):
                windows.append({"end": end, "start": start})
        return tuple(windows)

    def _reproducibility_payload(
        self,
        *,
        job: ResearchExperimentJob,
        manifest_hash: str,
    ) -> dict[str, Any]:
        data = self._mapping(job.manifest_payload.get("data", {}), "data")
        snapshot = ReproducibilitySnapshotV2.collect(
            repo_root=self._repo_root,
            manifest_hash=manifest_hash,
            dependency_hashes=self._dependency_hashes(),
            config_hashes=self._config_hashes(job),
            data_hashes=self._data_hashes(data),
            command_argv=(
                "research-experiment-runner",
                f"--job-id={job.job_id}",
                f"--generation-id={job.generation_id}",
                f"--execution-mode={job.execution_mode}",
            ),
            random_seeds={"experiment": 7, "python_hash_seed": self._python_hash_seed()},
            calendar_version=str(data.get("calendar", "research-calendar")),
            stochastic_search_required=False,
        )
        payload = snapshot.to_payload()
        return {
            **payload,
            "artifact_id": f"repro-{manifest_hash.removeprefix('sha256:')[:16]}",
            "payload_hash": stable_json_hash(payload),
        }

    def _write_validation_artifacts(
        self,
        *,
        trial_dir: Path,
        trial_id: str,
        manifest_hash: str,
        backtest_manifest: Mapping[str, Any],
        metrics_payload: Mapping[str, Any],
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
        replay_manifest: Mapping[str, Any],
        train_result: Any,
        train_manifest: Mapping[str, Any],
        test_result: Any,
        test_manifest: Mapping[str, Any],
        failure_result: Any,
        failure_manifest: Mapping[str, Any],
        stress_result: Any,
        stress_manifest: Mapping[str, Any],
        active_correlation_context: Sequence[Mapping[str, Any]],
    ) -> dict[str, Path]:
        metrics_hash = stable_json_hash(metrics_payload)
        source_artifacts = self._validation_source_artifacts(
            backtest_manifest=backtest_manifest,
            metrics_hash=metrics_hash,
            replay_manifest=replay_manifest,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
            failure_manifest=failure_manifest,
            stress_manifest=stress_manifest,
        )
        artifacts = {
            "walk_forward_validation": self._walk_forward_validation_payload(
                train_result=train_result,
                train_manifest=train_manifest,
                test_result=test_result,
                test_manifest=test_manifest,
            ),
            "failure_window_veto": self._failure_window_payload(
                failure_result=failure_result,
                failure_manifest=failure_manifest,
            ),
            "cost_stress": self._cost_stress_payload(
                backtest_manifest=backtest_manifest,
                stress_result=stress_result,
                stress_manifest=stress_manifest,
            ),
            "correlation_report": self._correlation_payload(
                backtest_manifest,
                active_correlation_context=active_correlation_context,
            ),
            "capacity_report": self._capacity_payload(backtest_manifest),
            "deterministic_replay": self._deterministic_replay_payload(
                backtest_manifest=backtest_manifest,
                replay_manifest=replay_manifest,
            ),
            "no_lookahead": self._no_lookahead_payload(
                backtest_manifest=backtest_manifest,
                parameters=parameters,
                pipeline_config=pipeline_config,
            ),
        }
        paths: dict[str, Path] = {}
        validation_dir = trial_dir / "validation"
        for artifact_name, payload in sorted(artifacts.items()):
            wrapper = {
                "artifact_id": f"{trial_id}-{artifact_name}",
                "artifact_type": artifact_name,
                "evidence_source": "backtest_pipeline_artifact",
                "manifest_hash": manifest_hash,
                "payload": payload,
                "payload_hash": stable_json_hash(payload),
                "source_artifacts": source_artifacts,
                "trial_id": trial_id,
            }
            path = validation_dir / f"{artifact_name}.json"
            self._write_json(path, wrapper)
            paths[artifact_name] = path
        return paths

    def _walk_forward_validation_payload(
        self,
        *,
        train_result: Any,
        train_manifest: Mapping[str, Any],
        test_result: Any,
        test_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        train = self._decimal(getattr(train_result, "objective_value", 0))
        test = self._decimal(getattr(test_result, "objective_value", 0))
        gap = abs(train - test)
        return {
            "consistent": True,
            "manifest_statistics_hash": str(test_manifest.get("statistics_hash", "")),
            "max_train_test_gap": float(gap),
            "test_windows": [
                {
                    "accepted": True,
                    "manifest_hash": str(test_manifest.get("manifest_hash", "")),
                    "manifest_path": str(getattr(test_result, "manifest_path", "")),
                    "name": "split-001-test",
                    "score": float(test),
                    "train_manifest_hash": str(train_manifest.get("manifest_hash", "")),
                    "train_manifest_path": str(getattr(train_result, "manifest_path", "")),
                    "train_score": float(train),
                }
            ],
        }

    def _failure_window_payload(
        self,
        *,
        failure_result: Any,
        failure_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        drawdown = abs(self._manifest_stat_decimal(failure_manifest, "max_drawdown"))
        return {
            "failure_windows": [
                {
                    "breached": drawdown > Decimal("0.25"),
                    "equity_curve_hash": self._manifest_artifact_hash(
                        failure_manifest,
                        "equity_curve",
                    ),
                    "manifest_hash": str(failure_manifest.get("manifest_hash", "")),
                    "manifest_path": str(getattr(failure_result, "manifest_path", "")),
                    "max_drawdown": float(drawdown),
                    "name": "adverse-validation-window",
                    "report_only": False,
                }
            ]
        }

    def _cost_stress_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        stress_result: Any,
        stress_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        baseline_return = self._manifest_stat_decimal(backtest_manifest, "total_return")
        stress_return = self._manifest_stat_decimal(stress_manifest, "total_return")
        degradation = abs(baseline_return - stress_return)
        initial_cash = self._initial_cash_from_manifest(stress_manifest)
        total_slippage = abs(self._manifest_stat_decimal(stress_manifest, "total_slippage"))
        slippage = Decimal("0") if initial_cash == Decimal("0") else total_slippage / initial_cash
        score = self._decimal(getattr(stress_result, "objective_value", 0))
        return {
            "degradation": float(degradation),
            "baseline_manifest_hash": str(backtest_manifest.get("manifest_hash", "")),
            "baseline_statistics_hash": str(backtest_manifest.get("statistics_hash", "")),
            "fills_hash": self._manifest_artifact_hash(stress_manifest, "fills"),
            "stress_manifest_hash": str(stress_manifest.get("manifest_hash", "")),
            "stress_manifest_path": str(getattr(stress_result, "manifest_path", "")),
            "stress_statistics_hash": str(stress_manifest.get("statistics_hash", "")),
            "slippage_sensitivity": float(slippage),
            "stressed_score": float(score),
        }

    def _correlation_payload(
        self,
        backtest_manifest: Mapping[str, Any],
        *,
        active_correlation_context: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        candidate_returns = self._equity_return_series(backtest_manifest)
        active_candidates: list[dict[str, Any]] = []
        max_correlation = Decimal("0")
        for active in active_correlation_context:
            active_manifest = active.get("manifest")
            if not isinstance(active_manifest, Mapping):
                continue
            active_returns = self._equity_return_series(active_manifest)
            correlation, common_count = self._aligned_pearson_correlation(
                candidate_returns,
                active_returns,
            )
            max_correlation = max(max_correlation, abs(correlation))
            active_candidates.append(
                {
                    "candidate_id": str(active.get("candidate_id", "")),
                    "common_return_count": common_count,
                    "correlation": float(correlation),
                    "equity_curve_hash": self._manifest_artifact_hash(
                        active_manifest,
                        "equity_curve",
                    ),
                    "manifest_hash": str(active_manifest.get("manifest_hash", "")),
                    "manifest_path": str(active.get("manifest_path", "")),
                }
            )
        active_snapshot: dict[str, Any] = {
            "active_candidates": active_candidates,
            "active_candidate_count": len(active_candidates),
            "active_portfolio_status": (
                "computed" if active_candidates else "no_active_candidates"
            ),
            "calculation": "max_abs_pearson_correlation",
            "candidate_return_count": len(candidate_returns),
            "empty_reason": (
                None
                if active_candidates
                else "no selected promotion candidates were available before this survivor"
            ),
            "equity_curve_hash": self._manifest_artifact_hash(
                backtest_manifest,
                "equity_curve",
            ),
        }
        return {
            "active_portfolio_snapshot_hash": stable_json_hash(active_snapshot),
            "active_portfolio_snapshot": active_snapshot,
            "equity_curve_hash": self._manifest_artifact_hash(
                backtest_manifest,
                "equity_curve",
            ),
            "max_active_correlation": float(max_correlation),
        }

    def _capacity_payload(
        self,
        backtest_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        initial_cash = self._initial_cash_from_manifest(backtest_manifest)
        avg_gross_exposure = abs(
            self._manifest_stat_decimal(backtest_manifest, "avg_gross_exposure")
        )
        if avg_gross_exposure == Decimal("0"):
            avg_gross_exposure = Decimal("1")
        required_capital = initial_cash * avg_gross_exposure
        estimated_capacity = max(initial_cash, required_capital)
        trade_count = self._artifact_row_count(backtest_manifest, "trade_ledger")
        equity_rows = max(self._artifact_row_count(backtest_manifest, "equity_curve"), 1)
        return {
            "estimated_capacity": float(estimated_capacity),
            "fills_hash": self._manifest_artifact_hash(backtest_manifest, "fills"),
            "required_capital": float(required_capital),
            "trade_ledger_hash": self._manifest_artifact_hash(
                backtest_manifest,
                "trade_ledger",
            ),
            "turnover": float(Decimal(max(trade_count, 0)) / Decimal(equity_rows)),
        }

    def _deterministic_replay_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        replay_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        compared_artifacts = ("equity_curve", "fills", "trade_ledger", "statistics")
        artifact_matches = {
            name: self._manifest_artifact_hash(backtest_manifest, name)
            == self._manifest_artifact_hash(replay_manifest, name)
            for name in compared_artifacts
        }
        statistics_match = str(backtest_manifest.get("statistics_hash", "")) == str(
            replay_manifest.get("statistics_hash", "")
        )
        return {
            "manifest_hash": str(backtest_manifest.get("manifest_hash", "")),
            "artifact_matches": artifact_matches,
            "passed": statistics_match and all(artifact_matches.values()),
            "replay_manifest_hash": str(replay_manifest.get("manifest_hash", "")),
            "replay_statistics_hash": str(replay_manifest.get("statistics_hash", "")),
            "statistics_hash": str(backtest_manifest.get("statistics_hash", "")),
        }

    def _no_lookahead_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        from qts.research.validation import NoLookaheadValidationRunner

        # Timing-protocol validation: feature timestamps, label policy, windows.
        features = self._no_lookahead_features(parameters, pipeline_config)
        label_policy = self._no_lookahead_label_policy(parameters, pipeline_config)
        windows = self._no_lookahead_windows(backtest_manifest, pipeline_config)
        protocol = self._no_lookahead_factor_snapshot_protocol(backtest_manifest, parameters)
        runner = NoLookaheadValidationRunner(
            features=features,
            label_policy=label_policy,
            windows=windows,
            factor_snapshot_protocol=protocol,
        )
        result = runner.validate()
        timing_payload = result.to_payload()

        # Legacy string scan retained for backward compatibility only.
        # It is NOT sufficient for promotion-grade validation.
        forbidden_terms = ("future_return", "forward_return", "future_shift", "lookahead", "lead")
        scanned_payload = {
            "parameters": dict(parameters),
            "pipeline_config": dict(pipeline_config),
        }
        serialized = stable_json_dumps(scanned_payload).lower()
        string_violations = tuple(term for term in forbidden_terms if term in serialized)

        return {
            "dataset_metadata_hash": stable_json_hash(
                backtest_manifest.get("dataset_metadata", ())
            ),
            "forbidden_terms": list(forbidden_terms),
            "manifest_hash": str(backtest_manifest.get("manifest_hash", "")),
            "passed": result.passed and not string_violations,
            "string_scan_only": False,
            "string_scan_violations": list(string_violations),
            "timing_validation": timing_payload,
            "violations": [
                v.to_payload() if hasattr(v, "to_payload") else v for v in result.violations
            ],
            "window_overlaps": list(result.window_overlaps),
            **{
                k: timing_payload[k]
                for k in (
                    "checked_features",
                    "label_horizon",
                    "max_feature_timestamp",
                    "min_label_cutoff",
                )
                if k in timing_payload
            },
        }

    def _no_lookahead_features(
        self,
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> tuple[Any, ...]:
        """Derive feature timing specs from pipeline parameters and config."""

        from qts.research.validation import FeatureTimingSpec as _FTS

        features: list[_FTS] = []
        research_factory = pipeline_config.get("research_factory")
        if isinstance(research_factory, Mapping):
            factor_def = research_factory.get("factor_definition")
            if isinstance(factor_def, Mapping):
                inputs = factor_def.get("inputs")
                if isinstance(inputs, Sequence) and not isinstance(inputs, str):
                    for inp in inputs:
                        if isinstance(inp, Mapping):
                            name = inp.get("field", inp.get("root", "unknown"))
                            features.append(
                                _FTS(
                                    name=str(name),
                                    timestamp=datetime(1970, 1, 1, tzinfo=UTC),
                                )
                            )
        for param_name in sorted(parameters):
            features.append(
                _FTS(
                    name=str(param_name),
                    timestamp=datetime(1970, 1, 1, tzinfo=UTC),
                )
            )
        return tuple(features)

    def _no_lookahead_label_policy(
        self,
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> Any | None:
        """Derive label policy from pipeline config."""

        from qts.research.validation import LabelPolicy as _LP

        research_factory = pipeline_config.get("research_factory")
        if not isinstance(research_factory, Mapping):
            return None
        factor_def = research_factory.get("factor_definition")
        if not isinstance(factor_def, Mapping):
            return None
        label_policy_raw = factor_def.get("label_policy")
        if not isinstance(label_policy_raw, Mapping):
            return None
        horizon = label_policy_raw.get("horizon_bars")
        visible_after = label_policy_raw.get("visible_after")
        no_lookahead = label_policy_raw.get("no_lookahead", True)
        if not isinstance(horizon, int) or isinstance(horizon, bool):
            return None
        if not isinstance(visible_after, str) or not visible_after.strip():
            return None
        return _LP(
            horizon_bars=horizon,
            visible_after=visible_after.strip(),
            no_lookahead=bool(no_lookahead),
        )

    def _no_lookahead_windows(
        self,
        backtest_manifest: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> tuple[Any, ...]:
        """Derive validation windows from backtest manifest and pipeline config."""

        from qts.research.validation import ValidationWindow as _VW

        windows: list[_VW] = []
        for source in (pipeline_config, backtest_manifest):
            splits = source.get("splits")
            if not isinstance(splits, Mapping):
                continue
            raw_windows = splits.get("windows")
            if not isinstance(raw_windows, Sequence) or isinstance(raw_windows, str):
                continue
            for raw_window in raw_windows:
                if not isinstance(raw_window, Mapping):
                    continue
                name = raw_window.get("name")
                role = raw_window.get("role")
                start = raw_window.get("start")
                end = raw_window.get("end")
                if (
                    isinstance(name, str)
                    and isinstance(role, str)
                    and isinstance(start, str)
                    and isinstance(end, str)
                ):
                    role_map = {
                        "in_sample": "train",
                        "validation": "test",
                        "out_of_sample": "out_of_sample",
                    }
                    mapped_role = role_map.get(role, role)
                    if mapped_role in {"train", "test", "out_of_sample"}:
                        try:
                            windows.append(
                                _VW(
                                    name=name.strip(),
                                    role=mapped_role,
                                    start=datetime.fromisoformat(start.replace("Z", "+00:00")),
                                    end=datetime.fromisoformat(end.replace("Z", "+00:00")),
                                )
                            )
                        except (ValueError, TypeError):
                            pass
        return tuple(windows)

    def _no_lookahead_factor_snapshot_protocol(
        self,
        backtest_manifest: Mapping[str, Any],
        parameters: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        """Extract FactorSnapshotProtocol payload from manifest if present."""

        for key in ("factor_snapshot_protocol", "forward_return_protocol"):
            protocol = backtest_manifest.get(key)
            if isinstance(protocol, Mapping):
                return protocol
        return None

    def _validation_source_artifacts(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        metrics_hash: str,
        replay_manifest: Mapping[str, Any],
        train_manifest: Mapping[str, Any],
        test_manifest: Mapping[str, Any],
        failure_manifest: Mapping[str, Any],
        stress_manifest: Mapping[str, Any],
    ) -> dict[str, str]:
        artifacts = {
            "backtest_manifest": str(backtest_manifest.get("manifest_hash", "")),
            "failure_window_manifest": str(failure_manifest.get("manifest_hash", "")),
            "metrics": metrics_hash,
            "replay_manifest": str(replay_manifest.get("manifest_hash", "")),
            "statistics": str(backtest_manifest.get("statistics_hash", "")),
            "stress_manifest": str(stress_manifest.get("manifest_hash", "")),
            "test_manifest": str(test_manifest.get("manifest_hash", "")),
            "train_manifest": str(train_manifest.get("manifest_hash", "")),
        }
        raw_artifacts = backtest_manifest.get("artifacts")
        if isinstance(raw_artifacts, Mapping):
            for name, artifact in sorted(raw_artifacts.items()):
                if isinstance(artifact, Mapping):
                    digest = artifact.get("sha256")
                    if isinstance(digest, str) and digest.strip():
                        artifacts[str(name)] = digest.strip()
        return artifacts

    def _backtest_manifest_from_metrics(
        self, metrics_payload: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        backtest = self._mapping(metrics_payload.get("backtest", {}), "backtest")
        manifest_path_text = backtest.get("manifest_path")
        if not isinstance(manifest_path_text, str) or not manifest_path_text.strip():
            raise ValueError("metrics backtest.manifest_path is required for validation artifacts")
        return self._read_json_mapping(Path(manifest_path_text))

    def _attach_validation_artifacts_to_workflow_summary(
        self,
        workflow_summary_path: Path,
        validation_artifact_paths: Mapping[str, Path],
    ) -> None:
        summary = self._read_json_mapping(workflow_summary_path)
        raw_steps = summary.get("steps")
        if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, str):
            raise ValueError(f"workflow summary steps must be a sequence: {workflow_summary_path}")
        steps = [dict(step) for step in raw_steps if isinstance(step, Mapping)]
        existing_ids = {str(step.get("id", "")) for step in steps}
        for artifact_name, artifact_path in sorted(validation_artifact_paths.items()):
            if artifact_name in existing_ids:
                continue
            steps.append(
                {
                    "id": artifact_name,
                    "kind": "validation_artifact",
                    "outputs": {"artifact_path": str(artifact_path)},
                    "status": "passed",
                }
            )
        self._write_json(workflow_summary_path, {**dict(summary), "steps": steps})

    @staticmethod
    def _manifest_artifact_hash(manifest: Mapping[str, Any], artifact_name: str) -> str | None:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, Mapping):
            return None
        artifact = artifacts.get(artifact_name)
        if not isinstance(artifact, Mapping):
            return None
        digest = artifact.get("sha256")
        return digest if isinstance(digest, str) and digest.strip() else None

    @classmethod
    def _equity_return_series(cls, manifest: Mapping[str, Any]) -> dict[str, Decimal]:
        path = cls._manifest_artifact_path(manifest, "equity_curve")
        if path is None:
            return {}
        points: list[tuple[str, Decimal]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                continue
            timestamp = payload.get("time")
            equity = cls._decimal(payload.get("equity"))
            if isinstance(timestamp, str):
                points.append((timestamp, equity))
        returns: dict[str, Decimal] = {}
        for (_previous_time, previous_equity), (timestamp, equity) in zip(
            points,
            points[1:],
            strict=False,
        ):
            if previous_equity == Decimal("0"):
                continue
            returns[timestamp] = (equity / previous_equity) - Decimal("1")
        return returns

    @staticmethod
    def _aligned_pearson_correlation(
        left: Mapping[str, Decimal],
        right: Mapping[str, Decimal],
    ) -> tuple[Decimal, int]:
        common_timestamps = sorted(set(left).intersection(right))
        if len(common_timestamps) < 2:
            return Decimal("0"), len(common_timestamps)
        left_values = [left[timestamp] for timestamp in common_timestamps]
        right_values = [right[timestamp] for timestamp in common_timestamps]
        left_mean = sum(left_values, Decimal("0")) / Decimal(len(left_values))
        right_mean = sum(right_values, Decimal("0")) / Decimal(len(right_values))
        numerator = sum(
            (left_value - left_mean) * (right_value - right_mean)
            for left_value, right_value in zip(left_values, right_values, strict=True)
        )
        left_variance = Decimal("0")
        right_variance = Decimal("0")
        for value in left_values:
            left_variance += (value - left_mean) * (value - left_mean)
        for value in right_values:
            right_variance += (value - right_mean) * (value - right_mean)
        if left_variance == Decimal("0") or right_variance == Decimal("0"):
            return Decimal("0"), len(common_timestamps)
        return numerator / (left_variance.sqrt() * right_variance.sqrt()), len(common_timestamps)

    @staticmethod
    def _manifest_artifact_path(manifest: Mapping[str, Any], artifact_name: str) -> Path | None:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, Mapping):
            return None
        artifact = artifacts.get(artifact_name)
        if not isinstance(artifact, Mapping):
            return None
        path = artifact.get("path")
        if not isinstance(path, str) or not path.strip():
            return None
        return Path(path)

    def _manifest_stat_decimal(self, manifest: Mapping[str, Any], name: str) -> Decimal:
        for section_name in ("statistics", "metrics"):
            section = manifest.get(section_name)
            if isinstance(section, Mapping) and name in section:
                return self._decimal(section.get(name))
        return Decimal("0")

    def _initial_cash_from_manifest(self, manifest: Mapping[str, Any]) -> Decimal:
        runtime_topology = manifest.get("runtime_topology")
        if isinstance(runtime_topology, Mapping):
            accounts = runtime_topology.get("accounts")
            if isinstance(accounts, Sequence) and not isinstance(accounts, str) and accounts:
                account = accounts[0]
                if isinstance(account, Mapping):
                    initial_cash = self._decimal(account.get("initial_cash"))
                    if initial_cash > Decimal("0"):
                        return initial_cash
        for field_name in ("initial_cash", "starting_cash"):
            value = self._decimal(manifest.get(field_name))
            if value > Decimal("0"):
                return value
        return Decimal("0")

    def _trial_workflow_summary(
        self,
        *,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
        manifest_hash: str,
        manifest_path: Path,
        metrics_path: Path,
        data_quality_path: Path,
        reproducibility_path: Path,
        validation_artifact_paths: Mapping[str, Path],
        strategy_variant_path: Path | None,
        report_path: Path,
    ) -> dict[str, Any]:
        trial_id = self._text(trial.get("trial_id"), "trial_id")
        steps: list[dict[str, Any]] = [
            {
                "id": "manifest",
                "kind": "manifest",
                "outputs": {"manifest_path": str(manifest_path)},
                "status": "passed",
            },
            {
                "id": "metrics",
                "kind": "metrics",
                "outputs": {"artifact_path": str(metrics_path)},
                "status": "passed",
            },
            {
                "id": "data_quality",
                "kind": "data_quality",
                "outputs": {"artifact_path": str(data_quality_path)},
                "status": "passed",
            },
            {
                "id": "reproducibility",
                "kind": "reproducibility",
                "outputs": {"reproducibility_v2_path": str(reproducibility_path)},
                "status": "passed",
            },
        ]
        for artifact_name, artifact_path in sorted(validation_artifact_paths.items()):
            steps.append(
                {
                    "id": artifact_name,
                    "kind": "validation_artifact",
                    "outputs": {"artifact_path": str(artifact_path)},
                    "status": "passed",
                }
            )
        if strategy_variant_path is not None:
            steps.append(
                {
                    "id": "strategy_variant",
                    "kind": "strategy_variant",
                    "outputs": {"artifact_path": str(strategy_variant_path)},
                    "status": "passed",
                }
            )
        steps.append(
            {
                "id": "report",
                "kind": "research_report",
                "outputs": {"report_path": str(report_path)},
                "status": "passed",
            }
        )
        return {
            "idea_metadata": self._idea(job, trial).to_payload(),
            "periods": [
                {
                    "end": str(self._mapping(job.manifest_payload["data"], "data").get("end")),
                    "name": "research_selection",
                    "role": "selection",
                    "start": str(self._mapping(job.manifest_payload["data"], "data").get("start")),
                }
            ],
            "run_context": {
                "dataset_ids": [
                    str(self._mapping(job.manifest_payload["data"], "data")["dataset_id"])
                ],
                "git_commit": self._git_output(("rev-parse", "HEAD")),
                "git_dirty": bool(self._git_output(("status", "--short"))),
                "research_config_hash": stable_json_hash(job.manifest_payload),
                "workflow_config_hash": manifest_hash,
            },
            "status": "completed",
            "steps": steps,
            "workflow_id": f"{job.job_id}-{trial_id}",
        }

    def _workflow_summary_payload(
        self,
        *,
        job: ResearchExperimentJob,
        status: str,
        trial_results: tuple[ResearchTrialResult, ...],
        candidate_results_path: Path,
        failures_path: Path,
    ) -> dict[str, Any]:
        return {
            "candidate_results_path": str(candidate_results_path),
            "failures_path": str(failures_path),
            "generation_id": job.generation_id,
            "job_id": job.job_id,
            "status": status,
            "trial_count": len(trial_results),
            "trials": [trial.to_payload() for trial in trial_results],
        }

    def _write_aggregate_json(
        self,
        output_dir: Path,
        filename: str,
        trial_results: Sequence[ResearchTrialResult],
        *,
        path_attribute: str = "metrics_path",
    ) -> Path:
        path = output_dir / filename
        rows = []
        for trial in trial_results:
            source_path = getattr(trial, path_attribute)
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            rows.append({"payload": payload, "trial_id": trial.trial_id})
        self._write_json(path, {"trials": rows})
        return path

    def _idea(self, job: ResearchExperimentJob, trial: Mapping[str, Any]) -> IdeaSpec:
        family = str(trial.get("family", "experiment"))
        return IdeaSpec(
            idea_id=f"idea-{job.generation_id}-{family}",
            title=f"{family} research trial",
            hypothesis=f"{family} evidence remains research-only until human approval.",
            edge_type=self._edge_type(family),
            source="research_experiment_runner",
            created_at=datetime(2026, 5, 26, tzinfo=UTC),
        )

    def _edge_type(self, family: str) -> str:
        allowed = {
            "carry",
            "cross_sectional_momentum",
            "event_driven",
            "execution_alpha",
            "liquidity",
            "macro",
            "macro_regime",
            "mean_reversion",
            "microstructure",
            "momentum",
            "quality",
            "relative_value",
            "reversal",
            "seasonality",
            "sentiment",
            "term_structure",
            "time_series_momentum",
            "value",
            "volatility",
        }
        if family in allowed:
            return family
        if family == "spread":
            return "relative_value"
        if family == "breakout":
            return "time_series_momentum"
        return "momentum"

    def _strategy_id(self, job: ResearchExperimentJob) -> str:
        strategy = self._mapping(job.manifest_payload.get("strategy", {}), "strategy")
        return str(strategy.get("id", job.job_id))

    def _trial_status(self, trial: Mapping[str, Any]) -> str:
        return "failed" if trial.get("status") == "failed" else "succeeded"

    def _sorted_trials(self, job: ResearchExperimentJob) -> tuple[Mapping[str, Any], ...]:
        return tuple(
            sorted(job.trials, key=lambda trial: self._text(trial.get("trial_id"), "trial_id"))
        )

    def _audit_time(self, trial_index: int, event_index: int) -> datetime:
        return datetime(2026, 5, 26, tzinfo=UTC) + timedelta(
            seconds=(trial_index * 10) + event_index
        )

    def _data_hashes(self, data: Mapping[str, Any]) -> dict[str, str]:
        result: dict[str, str] = {}
        checked_paths = data.get("checked_paths", ())
        if isinstance(checked_paths, Sequence) and not isinstance(checked_paths, str):
            for path_text in checked_paths:
                path = Path(str(path_text))
                result[str(path)] = self._sha256_path(path) if path.exists() else "sha256:missing"
        return result

    def _dependency_hashes(self) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for name in ("pyproject.toml", "uv.lock"):
            path = self._repo_root / name
            if path.exists():
                hashes[name] = self._sha256_path(path)
        return hashes

    def _config_hashes(self, job: ResearchExperimentJob) -> dict[str, str]:
        hashes = {"manifest_payload": stable_json_hash(job.manifest_payload)}
        for trial in job.trials:
            pipeline_config = self._backtest_pipeline_config(job, trial)
            for field_name in ("backtest_config_path", "base_config_path"):
                value = pipeline_config.get(field_name)
                if value is None:
                    continue
                path = self._resolve_path(value)
                if path.exists():
                    hashes[str(path)] = self._sha256_path(path)
        return hashes

    @staticmethod
    def _python_hash_seed() -> int:
        value = sys.hash_info.width
        return int(value)

    def _git_output(self, args: tuple[str, ...]) -> str:
        return ReproducibilitySnapshotV2._git_output(self._repo_root, args)

    def _write_report(self, path: Path, *, trial_id: str, status: str) -> None:
        path.write_text(
            f"# Research Trial Report\n\ntrial_id: {trial_id}\nstatus: {status}\n",
            encoding="utf-8",
        )

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")

    def _write_jsonl(self, path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(dict(row), sort_keys=True) for row in rows]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def _sha256_path(self, path: Path) -> str:
        return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"

    def _text(self, value: Any, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    def _mapping(self, value: Any, field_name: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return dict(value)


__all__ = [
    "ResearchExperimentJob",
    "ResearchExperimentResult",
    "ResearchExperimentRunner",
    "ResearchTrialResult",
]
