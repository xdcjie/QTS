"""Experiment campaign + trial orchestration for the research runner.

Stateless orchestration functions (campaign loop, per-trial execution, backtest-pipeline
trial run, workflow-summary assembly, metrics derivation, and survivor-validation artifact
writing) extracted from ResearchExperimentRunner (QTS-FINAL-011). Each takes a
TrialEvidenceSupport for repo-relative evidence resolution and trial payload construction.
"""

from __future__ import annotations

import shutil
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.optimizer.parameter_space import ParameterGrid, ParameterSpace
from qts.research.optimizer.pipeline import BacktestPipelineJob, BacktestPipelineRunner
from qts.research.orchestrator.experiment_types import (
    ResearchExperimentJob,
    ResearchExperimentResult,
    ResearchTrialResult,
    _TrialExecutionArtifacts,
)
from qts.research.orchestrator.trial_evidence_support import TrialEvidenceSupport
from qts.research.orchestrator.trial_helpers import (
    _artifact_row_count,
    _attach_validation_artifacts_to_workflow_summary,
    _audit_time,
    _backtest_manifest_from_metrics,
    _backtest_pipeline_config_from_payloads,
    _cost_stress_config_path,
    _decimal,
    _mapping,
    _oos_returns_from_manifest,
    _optional_metric_float,
    _optional_metric_int,
    _pipeline_parameters,
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
from qts.research.orchestrator.validation_artifact_writer import (
    ValidationArtifactWriter,
)


def run(support: TrialEvidenceSupport, job: ResearchExperimentJob) -> ResearchExperimentResult:
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

    for trial_index, trial in enumerate(support._sorted_trials(job), start=1):
        trial_result = _run_trial(
            support,
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

    metrics_path = support._write_aggregate_json(output_dir, "metrics.json", trial_results)
    data_quality_path = support._write_aggregate_json(
        output_dir,
        "data_quality.json",
        trial_results,
        path_attribute="data_quality_path",
    )
    reproducibility_path = support._write_aggregate_json(
        output_dir,
        "reproducibility_v2.json",
        trial_results,
        path_attribute="reproducibility_path",
    )
    workflow_summary_path = output_dir / "workflow_summary.json"
    status = "completed" if not failure_rows else "completed_with_failures"
    workflow_summary = support._workflow_summary_payload(
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
    support: TrialEvidenceSupport,
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
    base_config_path = support._required_path(
        pipeline_config,
        ("backtest_config_path", "base_config_path"),
        "backtest_pipeline backtest_config_path",
    )
    objective_metric = str(pipeline_config.get("objective_metric", "sharpe_ratio"))
    materialized_cache_dir = pipeline_config.get("materialized_replay_cache_dir")
    materialized_cache_path = (
        None if materialized_cache_dir is None else support._resolve_path(materialized_cache_dir)
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
    metrics_rewritten = _rewrite_metrics_with_validation_derivation(
        support,
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
    support: TrialEvidenceSupport,
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
    manifest_payload = support._trial_manifest_payload(job, trial)
    execution_artifacts = _execute_trial(
        support,
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
    data_quality_payload = support._data_quality_payload(job, trial, trial_dir, manifest_hash)
    reproducibility_payload = support._reproducibility_payload(
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
        created_at=_audit_time(trial_index, 0, support._clock),
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
            _trial_workflow_summary(
                support,
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
            idea=support._idea(job, trial),
            strategy_id=support._strategy_id(job),
            audit_log=audit_log,
            artifact_graph_writer=ResearchArtifactGraphWriter(job.output_root / "artifact_graph"),
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
        created_at=_audit_time(trial_index, 1, support._clock),
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


def _execute_trial(
    support: TrialEvidenceSupport,
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
    return _execute_backtest_pipeline_trial(support, job=job, trial=trial, trial_dir=trial_dir)


def _execute_backtest_pipeline_trial(
    support: TrialEvidenceSupport,
    *,
    job: ResearchExperimentJob,
    trial: Mapping[str, Any],
    trial_dir: Path,
) -> _TrialExecutionArtifacts:
    pipeline_config = support._backtest_pipeline_config(job, trial)
    parameters = _pipeline_parameters(
        _mapping(trial.get("parameters", {}), "parameters"),
        pipeline_config,
    )
    if not parameters:
        raise ValueError("backtest_pipeline trials require at least one strategy parameter")
    base_config_path = support._required_path(
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
                else support._resolve_path(materialized_cache_dir)
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
    research_metrics = _research_metrics_payload(
        support,
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


def _trial_workflow_summary(
    support: TrialEvidenceSupport,
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
        "idea_metadata": support._idea(job, trial).to_payload(),
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
            "git_commit": support._git_output(("rev-parse", "HEAD")),
            "git_dirty": bool(support._git_output(("status", "--short"))),
            "research_config_hash": stable_json_hash(job.manifest_payload),
            "workflow_config_hash": manifest_hash,
        },
        "status": "completed",
        "steps": steps,
        "workflow_id": f"{job.job_id}-{trial_id}",
    }


def _research_metrics_payload(
    support: TrialEvidenceSupport,
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
    derivation = support._derive_validation_metrics(
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
    parameter_sensitivity: float | None = derivation.parameter_sensitivity if derivation else None
    oos_months: float | None = derivation.oos_months if derivation else None
    promotion_eligible: bool = derivation.promotion_eligible if derivation else False
    fill_timing_promotion_grade: bool | None = (
        derivation.fill_timing_promotion_grade if derivation else None
    )
    fill_timing_optimistic: bool | None = derivation.fill_timing_optimistic if derivation else None
    train_sharpe: float | None = derivation.sharpe_sources.train_sharpe if derivation else None
    oos_sharpe: float | None = derivation.sharpe_sources.oos_sharpe if derivation else None

    return {
        "costs": {"cost_sensitivity": float(cost_impact)},
        "execution": {
            "cost_impact": float(cost_impact),
            "slippage_sensitivity": float(abs(_decimal(statistics.get("slippage_per_trade", 0)))),
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


def _rewrite_metrics_with_validation_derivation(
    support: TrialEvidenceSupport,
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
    derivation = support._derive_validation_metrics(
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


__all__ = [
    "run",
    "write_validation_artifacts_for_trial",
]
