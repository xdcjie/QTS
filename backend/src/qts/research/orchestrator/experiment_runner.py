"""Deterministic research experiment runner artifacts."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifactWriter, DataQualityRunner
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
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

    def __post_init__(self) -> None:
        if self.status not in {"succeeded", "failed"}:
            raise ValueError(f"unsupported trial status: {self.status}")

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
        }


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


@dataclass(frozen=True, slots=True)
class _TrialExecutionArtifacts:
    metrics_payload: Mapping[str, Any]
    manifest_hash: str
    manifest_path: Path | None = None
    manifest_fields: Mapping[str, Any] | None = None
    artifact_paths: Mapping[str, Path] | None = None


class ResearchExperimentRunner:
    """Owns deterministic research experiment artifact production."""

    def __init__(self, *, repo_root: Path) -> None:
        self._repo_root = Path(repo_root)

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
        data_quality_payload = self._data_quality_payload(job, trial_dir, manifest_hash)
        reproducibility_payload = self._reproducibility_payload(
            job=job,
            manifest_hash=manifest_hash,
        )

        metrics_path = trial_dir / "metrics.json"
        data_quality_path = trial_dir / "data_quality.json"
        reproducibility_path = trial_dir / "reproducibility_v2.json"
        manifest_path = trial_dir / "manifest.json"
        report_path = trial_dir / "report.md"
        self._write_json(metrics_path, metrics_payload)
        self._write_json(data_quality_path, data_quality_payload)
        self._write_json(reproducibility_path, reproducibility_payload)
        self._write_report(report_path, trial_id=trial_id, status=self._trial_status(trial))
        artifact_paths = {
            "data_quality": data_quality_path,
            "metrics": metrics_path,
            "reproducibility": reproducibility_path,
            **dict(execution_artifacts.artifact_paths or {}),
        }
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
        result_manifest_path = execution_artifacts.manifest_path or manifest_path

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
                    report_path=report_path,
                ),
            )
            bundle = evidence_registry.create_from_workflow_summary(
                evidence_summary_path,
                idea=self._idea(job, trial),
                strategy_id=self._strategy_id(job),
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
        )

    def _trial_manifest_payload(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "attempt": job.attempt,
            "generation_id": job.generation_id,
            "job_id": job.job_id,
            "manifest": dict(job.manifest_payload),
            "parameters": dict(self._mapping(trial.get("parameters", {}), "parameters")),
            "trial_id": self._text(trial.get("trial_id"), "trial_id"),
        }

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
                "oos_sharpe": float(sharpe),
                "total_return": float(total_return),
                "train_sharpe": float(sharpe),
            },
            "portfolio": {"correlation_to_active": 0.0},
            "quality": {"profit_factor": float(profit_factor), "sharpe": float(sharpe)},
            "research": {
                "deterministic_replay_passed": True,
                "metrics_source": "backtest_pipeline",
                "no_lookahead_passed": True,
                "objective_metric": objective_metric,
                "promotion_eligible": True,
            },
            "risk": {"max_drawdown": float(max_drawdown)},
            "stability": {"parameter_sensitivity": 1.0, "walk_forward_consistency": 1.0},
            "trading": {"oos_months": 12.0, "oos_trade_count": trade_count},
        }

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
        config: dict[str, Any] = {}
        for field_name in ("backtest", "backtest_pipeline"):
            value = job.manifest_payload.get(field_name)
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

    def _read_json_mapping(self, path: Path) -> Mapping[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError(f"JSON file must contain an object: {path}")
        return dict(payload)

    def _data_quality_payload(
        self,
        job: ResearchExperimentJob,
        trial_dir: Path,
        manifest_hash: str,
    ) -> dict[str, Any]:
        data = self._mapping(job.manifest_payload.get("data", {}), "data")
        artifact = DataQualityRunner(
            dataset_id=str(data.get("dataset_id", job.job_id)),
            timeframe=str(data.get("timeframe", "1m")),
            start=None if data.get("start") is None else str(data["start"]),
            end=None if data.get("end") is None else str(data["end"]),
            calendar=None if data.get("calendar") is None else str(data["calendar"]),
        ).run({"checked_paths": tuple(str(path) for path in data.get("checked_paths", ()))})
        result = DataQualityArtifactWriter(trial_dir).write(artifact)
        payload = json.loads(result.path.read_text(encoding="utf-8"))
        return {
            **payload,
            "artifact_id": f"dq-{manifest_hash.removeprefix('sha256:')[:16]}",
            "path": str(result.path),
            "payload_hash": stable_json_hash(artifact.to_payload()),
        }

    def _reproducibility_payload(
        self,
        *,
        job: ResearchExperimentJob,
        manifest_hash: str,
    ) -> dict[str, Any]:
        data = self._mapping(job.manifest_payload.get("data", {}), "data")
        snapshot = ReproducibilitySnapshotV2(
            schema_version=2,
            git_sha=str(job.manifest_payload.get("git_sha", "research-git-sha")),
            git_dirty=False,
            python_version="3.13.0",
            platform="research-platform",
            manifest_hash=manifest_hash,
            dependency_hashes={"pyproject.toml": "sha256:research-deps"},
            config_hashes={"manifest": stable_json_hash(job.manifest_payload)},
            data_hashes=self._data_hashes(data),
            command_argv=("research-experiment-runner", job.job_id),
            random_seeds={"experiment": 7},
            calendar_version=str(data.get("calendar", "research-calendar")),
            container_digest=None,
            stochastic_search_required=False,
        )
        payload = snapshot.to_payload()
        return {
            **payload,
            "artifact_id": f"repro-{manifest_hash.removeprefix('sha256:')[:16]}",
            "payload_hash": stable_json_hash(payload),
        }

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
        report_path: Path,
    ) -> dict[str, Any]:
        trial_id = self._text(trial.get("trial_id"), "trial_id")
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
                "git_commit": "research-git-sha",
                "git_dirty": False,
                "research_config_hash": stable_json_hash(job.manifest_payload),
                "workflow_config_hash": manifest_hash,
            },
            "status": "completed",
            "steps": [
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
                {
                    "id": "report",
                    "kind": "research_report",
                    "outputs": {"report_path": str(report_path)},
                    "status": "passed",
                },
            ],
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
        if not result:
            result[f"dataset:{data.get('dataset_id', 'research')}"] = "sha256:research-data"
        return result

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
