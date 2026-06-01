"""Trial-evidence data access for the research experiment runner.

Owns repo-relative path/hash/git resolution, promotion-threshold-derived validation
metrics, and the trial manifest/data-quality/reproducibility/workflow payload builders
extracted from ResearchExperimentRunner (QTS-FINAL-011). Holds the run's repo_root and
promotion thresholds; the orchestration functions take a TrialEvidenceSupport.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.clock import ResearchClock, system_research_clock
from qts.research.data_quality import DataQualityArtifactWriter, DataQualityRunner
from qts.research.idea_spec import IdeaSpec
from qts.research.orchestrator.experiment_types import (
    ResearchExperimentJob,
    ResearchTrialResult,
)
from qts.research.orchestrator.trial_helpers import (
    _backtest_pipeline_config_from_payloads,
    _data_hashes,
    _data_quality_windows,
    _edge_type,
    _mapping,
    _merged_manifest,
    _python_hash_seed,
    _read_json_mapping,
    _sha256_path,
    _text,
    _write_json,
)
from qts.research.orchestrator.validation_artifact_reader import (
    PromotionThresholds,
    ResearchMetricsFromValidationArtifacts,
    ValidationArtifactReader,
)
from qts.research.reproducibility import ReproducibilitySnapshotV2


class TrialEvidenceSupport:
    """Owns repo-relative evidence resolution and trial payload construction."""

    def __init__(
        self,
        *,
        repo_root: Path,
        promotion_thresholds: PromotionThresholds | None = None,
        clock: ResearchClock | None = None,
    ) -> None:
        """Bind the support to the run's repo root and promotion thresholds."""
        self._repo_root = Path(repo_root)
        self._promotion_thresholds = promotion_thresholds or PromotionThresholds()
        self._clock = clock or system_research_clock()

    def _resolve_path(self, value: Any) -> Path:
        path = Path(str(value))
        return path if path.is_absolute() else self._repo_root / path

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

    def _git_output(self, args: tuple[str, ...]) -> str:
        return ReproducibilitySnapshotV2._git_output(self._repo_root, args)

    def _dependency_hashes(self) -> dict[str, str]:
        hashes: dict[str, str] = {}
        for name in ("pyproject.toml", "uv.lock"):
            path = self._repo_root / name
            if path.exists():
                hashes[name] = _sha256_path(path)
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
                    hashes[str(path)] = _sha256_path(path)
        return hashes

    def _reproducibility_payload(
        self,
        *,
        job: ResearchExperimentJob,
        manifest_hash: str,
    ) -> dict[str, Any]:
        data = _mapping(job.manifest_payload.get("data", {}), "data")
        snapshot = ReproducibilitySnapshotV2.collect(
            repo_root=self._repo_root,
            manifest_hash=manifest_hash,
            dependency_hashes=self._dependency_hashes(),
            config_hashes=self._config_hashes(job),
            data_hashes=_data_hashes(data),
            command_argv=(
                "research-experiment-runner",
                f"--job-id={job.job_id}",
                f"--generation-id={job.generation_id}",
                f"--execution-mode={job.execution_mode}",
            ),
            random_seeds={"experiment": 7, "python_hash_seed": _python_hash_seed()},
            calendar_version=str(data.get("calendar", "research-calendar")),
            stochastic_search_required=False,
        )
        payload = snapshot.to_payload()
        return {
            **payload,
            "artifact_id": f"repro-{manifest_hash.removeprefix('sha256:')[:16]}",
            "payload_hash": stable_json_hash(payload),
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
                workflow_summary = _read_json_mapping(workflow_summary_path)
            except (ValueError, OSError):
                workflow_summary = {}
        return ResearchMetricsFromValidationArtifacts(self._promotion_thresholds).derive(
            reader,
            workflow_summary,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
        )

    def _idea(self, job: ResearchExperimentJob, trial: Mapping[str, Any]) -> IdeaSpec:
        family = str(trial.get("family", "experiment"))
        return IdeaSpec(
            idea_id=f"idea-{job.generation_id}-{family}",
            title=f"{family} research trial",
            hypothesis=f"{family} evidence remains research-only until human approval.",
            edge_type=_edge_type(family),
            source="research_experiment_runner",
            created_at=self._clock.now(),
        )

    def _strategy_id(self, job: ResearchExperimentJob) -> str:
        strategy = _mapping(job.manifest_payload.get("strategy", {}), "strategy")
        return str(strategy.get("id", job.job_id))

    def _trial_manifest_payload(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        manifest_patch = trial.get("manifest_patch")
        if manifest_patch is not None and not isinstance(manifest_patch, Mapping):
            raise ValueError("trial manifest_patch must be a mapping")
        resolved_manifest = _merged_manifest(
            job.manifest_payload,
            {} if manifest_patch is None else manifest_patch,
        )
        payload: dict[str, Any] = {
            "attempt": job.attempt,
            "generation_id": job.generation_id,
            "job_id": job.job_id,
            "manifest": resolved_manifest,
            "parameters": dict(_mapping(trial.get("parameters", {}), "parameters")),
            "trial_id": _text(trial.get("trial_id"), "trial_id"),
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

    def _data_quality_payload(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
        trial_dir: Path,
        manifest_hash: str,
    ) -> dict[str, Any]:
        data = _mapping(job.manifest_payload.get("data", {}), "data")
        checked_paths = self._data_quality_checked_paths(job, trial)
        artifact = DataQualityRunner(
            dataset_id=str(data.get("dataset_id", job.job_id)),
            timeframe=str(data.get("timeframe", "1m")),
            start=None if data.get("start") is None else str(data["start"]),
            end=None if data.get("end") is None else str(data["end"]),
            calendar=None if data.get("calendar") is None else str(data["calendar"]),
            windows=_data_quality_windows(data.get("windows", ())),
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
        data = _mapping(job.manifest_payload.get("data", {}), "data")
        return tuple(str(path) for path in data.get("checked_paths", ()))

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

    def _backtest_pipeline_config(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        return _backtest_pipeline_config_from_payloads(job.manifest_payload, trial)

    def _sorted_trials(self, job: ResearchExperimentJob) -> tuple[Mapping[str, Any], ...]:
        return tuple(sorted(job.trials, key=lambda trial: _text(trial.get("trial_id"), "trial_id")))

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
            source_path = self._trial_payload_path(trial, path_attribute)
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            rows.append({"payload": payload, "trial_id": trial.trial_id})
        _write_json(path, {"trials": rows})
        return path

    @staticmethod
    def _trial_payload_path(trial: ResearchTrialResult, path_attribute: str) -> Path:
        if path_attribute == "metrics_path":
            return trial.metrics_path
        if path_attribute == "data_quality_path":
            return trial.data_quality_path
        if path_attribute == "reproducibility_path":
            return trial.reproducibility_path
        raise ValueError(f"unsupported trial aggregate path: {path_attribute}")


__all__ = ["TrialEvidenceSupport"]
