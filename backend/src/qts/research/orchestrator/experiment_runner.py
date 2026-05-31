"""Deterministic research experiment runner artifacts."""

from __future__ import annotations

import json
import shutil
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.data_quality import DataQualityArtifactWriter, DataQualityRunner
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.orchestrator.experiment_types import (
    ResearchExperimentJob,
    ResearchExperimentResult,
    ResearchTrialResult,
    _TrialExecutionArtifacts,
)
from qts.research.orchestrator.trial_helpers import (
    _artifact_row_count,
    _attach_validation_artifacts_to_workflow_summary,
    _audit_time,
    _backtest_manifest_from_metrics,
    _backtest_pipeline_config_from_payloads,
    _cost_stress_config_path,
    _data_hashes,
    _data_quality_windows,
    _decimal,
    _edge_type,
    _mapping,
    _merged_manifest,
    _oos_returns_from_manifest,
    _optional_metric_float,
    _optional_metric_int,
    _pipeline_parameters,
    _python_hash_seed,
    _read_json_mapping,
    _refresh_manifest_artifact_hash,
    _run_validation_backtest,
    _run_walk_forward_reruns,
    _sha256_path,
    _text,
    _trial_status,
    _write_json,
    _write_jsonl,
    _write_report,
    _write_strategy_variant_artifact,
)
from qts.research.orchestrator.validation_artifact_reader import (
    PromotionThresholds,
    ResearchMetricsFromValidationArtifacts,
    ValidationArtifactReader,
)
from qts.research.orchestrator.validation_artifact_writer import (
    ValidationArtifactWriter,
)
from qts.research.reproducibility import ReproducibilitySnapshotV2


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
                    "parameters": dict(_mapping(trial.get("parameters", {}), "parameters")),
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
        _write_jsonl(candidate_results_path, candidate_rows)
        _write_jsonl(failures_path, failure_rows)

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
        _write_json(workflow_summary_path, workflow_summary)

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
        metrics_payload = _read_json_mapping(trial_result.metrics_path)
        backtest_manifest = _backtest_manifest_from_metrics(metrics_payload)
        trial_manifest = _read_json_mapping(trial_result.manifest_path)
        resolved_manifest = _mapping(trial_manifest.get("manifest", {}), "manifest")
        pipeline_config = _backtest_pipeline_config_from_payloads(resolved_manifest, trial)
        parameters = _pipeline_parameters(
            _mapping(trial.get("parameters", {}), "parameters"),
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

        _replay_result, replay_manifest = _run_validation_backtest(
            base_config_path=base_config_path,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "deterministic_replay",
            materialized_replay_cache_dir=materialized_cache_path,
        )
        train_result, train_manifest, test_result, test_manifest = _run_walk_forward_reruns(
            base_config_path=base_config_path,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "walk_forward",
            materialized_replay_cache_dir=materialized_cache_path,
        )
        failure_result, failure_manifest = _run_validation_backtest(
            base_config_path=base_config_path,
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "failure_window_veto",
            materialized_replay_cache_dir=materialized_cache_path,
        )
        stress_result, stress_manifest = _run_validation_backtest(
            base_config_path=_cost_stress_config_path(
                base_config_path=base_config_path,
                output_dir=trial_dir / "validation_configs",
            ),
            parameters=parameters,
            objective_metric=objective_metric,
            output_root=trial_dir / "validation_runs" / "cost_stress",
            materialized_replay_cache_dir=materialized_cache_path,
        )

        validation_artifact_paths = ValidationArtifactWriter().write(
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
        _attach_validation_artifacts_to_workflow_summary(
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
            _refresh_manifest_artifact_hash(
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
        trial_id = _text(trial.get("trial_id"), "trial_id")
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
        strategy_variant_path = _write_strategy_variant_artifact(
            trial_dir=trial_dir,
            trial=trial,
            manifest_payload=manifest_payload,
        )
        _write_json(metrics_path, metrics_payload)
        _write_json(data_quality_path, data_quality_payload)
        _write_json(reproducibility_path, reproducibility_payload)
        validation_artifact_paths: dict[str, Path] = {}
        _write_report(report_path, trial_id=trial_id, status=_trial_status(trial))
        artifact_paths = {
            "data_quality": data_quality_path,
            "metrics": metrics_path,
            "reproducibility": reproducibility_path,
            **dict(validation_artifact_paths.items()),
            **dict(execution_artifacts.artifact_paths or {}),
        }
        if strategy_variant_path is not None:
            artifact_paths["strategy_variant"] = strategy_variant_path
        manifest_payload = {
            **manifest_payload,
            "artifact_hashes": {
                name: _sha256_path(path) for name, path in sorted(artifact_paths.items())
            },
            "artifact_paths_by_hash": {
                _sha256_path(path): str(path) for path in artifact_paths.values()
            },
        }
        _write_json(manifest_path, manifest_payload)
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
            created_at=_audit_time(trial_index, 0),
        )

        status = _trial_status(trial)
        failure_path = None
        evidence_bundle_id = None
        if status == "failed":
            failure_path = trial_dir / "failures.jsonl"
            _write_jsonl(
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
            _write_json(
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
            created_at=_audit_time(trial_index, 1),
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
        if _trial_status(trial) == "failed":
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
        parameters = _pipeline_parameters(
            _mapping(trial.get("parameters", {}), "parameters"),
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
        backtest_manifest = _read_json_mapping(backtest_manifest_path)
        manifest_hash = str(
            result.manifest_hash
            or backtest_manifest.get("manifest_hash")
            or _sha256_path(backtest_manifest_path)
        )
        metrics_block = _mapping(backtest_manifest.get("metrics", {}), "metrics")
        raw_statistics = backtest_manifest.get("statistics", {})
        statistics_block = {
            **metrics_block,
            **_mapping(raw_statistics, "statistics"),
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
        sharpe = _decimal(statistics.get("sharpe_ratio", objective_value))
        # Per-observation statistics consumed by the multiple-testing /
        # deflated-Sharpe correction. None/empty when an older manifest predates
        # their emission; the selector then falls back to its documented defaults.
        observed_sharpe = _optional_metric_float(statistics.get("observed_sharpe"))
        return_observation_count = _optional_metric_int(statistics.get("return_observation_count"))
        return_skewness = _optional_metric_float(statistics.get("return_skewness"))
        return_kurtosis = _optional_metric_float(statistics.get("return_kurtosis"))
        oos_returns = _oos_returns_from_manifest(backtest_manifest)
        total_return = _decimal(statistics.get("total_return", 0))
        max_drawdown = abs(_decimal(statistics.get("max_drawdown", 0)))
        profit_factor = _decimal(statistics.get("profit_factor", 0))
        trade_count = _artifact_row_count(backtest_manifest, "trade_ledger")
        if trade_count <= 0:
            trade_count = _artifact_row_count(backtest_manifest, "fills")
        total_commission = abs(_decimal(statistics.get("total_commission", 0)))
        total_slippage = abs(_decimal(statistics.get("total_slippage", 0)))
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
        fill_timing_promotion_grade: bool | None = (
            derivation.fill_timing_promotion_grade if derivation else None
        )
        fill_timing_optimistic: bool | None = (
            derivation.fill_timing_optimistic if derivation else None
        )
        train_sharpe: float | None = derivation.sharpe_sources.train_sharpe if derivation else None
        oos_sharpe: float | None = derivation.sharpe_sources.oos_sharpe if derivation else None

        return {
            "costs": {"cost_sensitivity": float(cost_impact)},
            "execution": {
                "cost_impact": float(cost_impact),
                "slippage_sensitivity": float(
                    abs(_decimal(statistics.get("slippage_per_trade", 0)))
                ),
            },
            "performance": {
                "max_drawdown": float(max_drawdown),
                "observed_sharpe": observed_sharpe,
                "oos_returns": oos_returns,
                "oos_sharpe": oos_sharpe,
                "return_kurtosis": return_kurtosis,
                "return_observation_count": return_observation_count,
                "return_skewness": return_skewness,
                "total_return": float(total_return),
                "train_sharpe": train_sharpe,
            },
            "portfolio": {"correlation_to_active": 0.0},
            "quality": {"profit_factor": float(profit_factor), "sharpe": float(sharpe)},
            "research": {
                "deterministic_replay_passed": deterministic_replay_passed,
                "fill_timing_optimistic": fill_timing_optimistic,
                "fill_timing_promotion_grade": fill_timing_promotion_grade,
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
                workflow_summary = _read_json_mapping(workflow_summary_path)
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
        current_payload = _read_json_mapping(metrics_path)
        updated = dict(current_payload)

        # Patch research section with artifact-derived values
        research = dict(_mapping(updated.get("research", {}), "research"))
        research["deterministic_replay_passed"] = derivation.deterministic_replay_passed
        research["fill_timing_optimistic"] = derivation.fill_timing_optimistic
        research["fill_timing_promotion_grade"] = derivation.fill_timing_promotion_grade
        research["no_lookahead_passed"] = derivation.no_lookahead_passed
        research["promotion_eligible"] = derivation.promotion_eligible
        updated["research"] = research

        # Patch stability section
        stability = dict(_mapping(updated.get("stability", {}), "stability"))
        stability["parameter_sensitivity"] = derivation.parameter_sensitivity
        stability["walk_forward_consistency"] = derivation.walk_forward_consistency
        updated["stability"] = stability

        # Patch trading section
        trading = dict(_mapping(updated.get("trading", {}), "trading"))
        trading["oos_months"] = derivation.oos_months
        updated["trading"] = trading

        # Patch performance section with separate train/oos sharpe
        performance = dict(_mapping(updated.get("performance", {}), "performance"))
        performance["train_sharpe"] = derivation.sharpe_sources.train_sharpe
        performance["oos_sharpe"] = derivation.sharpe_sources.oos_sharpe
        updated["performance"] = performance

        _write_json(metrics_path, updated)
        return True

    def _backtest_pipeline_config(
        self,
        job: ResearchExperimentJob,
        trial: Mapping[str, Any],
    ) -> dict[str, Any]:
        return _backtest_pipeline_config_from_payloads(job.manifest_payload, trial)

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
        trial_id = _text(trial.get("trial_id"), "trial_id")
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
                    "end": str(_mapping(job.manifest_payload["data"], "data").get("end")),
                    "name": "research_selection",
                    "role": "selection",
                    "start": str(_mapping(job.manifest_payload["data"], "data").get("start")),
                }
            ],
            "run_context": {
                "dataset_ids": [str(_mapping(job.manifest_payload["data"], "data")["dataset_id"])],
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
        _write_json(path, {"trials": rows})
        return path

    def _idea(self, job: ResearchExperimentJob, trial: Mapping[str, Any]) -> IdeaSpec:
        family = str(trial.get("family", "experiment"))
        return IdeaSpec(
            idea_id=f"idea-{job.generation_id}-{family}",
            title=f"{family} research trial",
            hypothesis=f"{family} evidence remains research-only until human approval.",
            edge_type=_edge_type(family),
            source="research_experiment_runner",
            created_at=datetime(2026, 5, 26, tzinfo=UTC),
        )

    def _strategy_id(self, job: ResearchExperimentJob) -> str:
        strategy = _mapping(job.manifest_payload.get("strategy", {}), "strategy")
        return str(strategy.get("id", job.job_id))

    def _sorted_trials(self, job: ResearchExperimentJob) -> tuple[Mapping[str, Any], ...]:
        return tuple(sorted(job.trials, key=lambda trial: _text(trial.get("trial_id"), "trial_id")))

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

    def _git_output(self, args: tuple[str, ...]) -> str:
        return ReproducibilitySnapshotV2._git_output(self._repo_root, args)


__all__ = [
    "ResearchExperimentJob",
    "ResearchExperimentResult",
    "ResearchExperimentRunner",
    "ResearchTrialResult",
]
