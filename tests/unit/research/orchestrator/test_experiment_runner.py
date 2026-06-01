from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import qts.research.orchestrator.experiment_orchestration as experiment_orchestration
import qts.research.orchestrator.trial_helpers as trial_helpers
from qts.research.audit_log import ResearchAuditLog
from qts.research.clock import DeterministicResearchClock
from qts.research.optimizer.result import OptimizationResult
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentRunner,
)


def test_experiment_runner_writes_required_trial_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_backtest_pipeline_runner(monkeypatch)
    data_path = _write_bars(tmp_path)
    job = _job(tmp_path, data_path)
    runner = ResearchExperimentRunner(
        repo_root=Path.cwd(),
        clock=DeterministicResearchClock(datetime(2026, 5, 26, tzinfo=UTC)),
    )

    result = runner.run(job)

    assert result.status == "completed_with_failures"
    assert result.workflow_summary_path.exists()
    assert result.candidate_results_path.exists()
    assert result.failures_path.exists()
    assert [trial.trial_id for trial in result.trials] == ["trial-accepted", "trial-rejected"]

    accepted = result.trials[0]
    assert accepted.status == "succeeded"
    assert accepted.manifest_hash.startswith("sha256:")
    assert accepted.evidence_bundle_id is not None
    assert accepted.failures_path is None
    assert accepted.manifest_path.exists()
    assert accepted.data_quality_path.exists()
    assert accepted.reproducibility_path.exists()
    assert accepted.metrics_path.exists()
    assert accepted.validation_artifact_paths == {}

    data_quality = json.loads(accepted.data_quality_path.read_text(encoding="utf-8"))
    reproducibility = json.loads(accepted.reproducibility_path.read_text(encoding="utf-8"))
    assert data_quality["schema_version"] == 2
    assert data_quality["accepted"] is True
    assert reproducibility["schema_version"] == 2
    assert reproducibility["manifest_hash"] == accepted.manifest_hash

    validation_artifact_paths = runner.write_validation_artifacts_for_trial(
        trial=job.trials[0],
        trial_result=accepted,
    )
    validation_artifact = json.loads(
        Path(validation_artifact_paths["walk_forward_validation"]).read_text(encoding="utf-8")
    )
    assert validation_artifact["evidence_source"] == "backtest_pipeline_artifact"
    assert validation_artifact["source_artifacts"]["backtest_manifest"].startswith("sha256:")
    assert validation_artifact["source_artifacts"]["test_manifest"].startswith("sha256:")
    workflow_summary = json.loads(
        (accepted.metrics_path.parent / "workflow_summary.json").read_text(encoding="utf-8")
    )
    assert "walk_forward_validation" in {step["id"] for step in workflow_summary["steps"]}

    rejected = result.trials[1]
    assert rejected.status == "failed"
    assert rejected.failures_path is not None
    assert rejected.failures_path.exists()
    failure_rows = _jsonl(result.failures_path)
    assert failure_rows == [
        {
            "failure_reason": "research candidate rejected before execution",
            "generation_id": "generation-000",
            "job_id": "experiment-job",
            "manifest_hash": rejected.manifest_hash,
            "trial_id": "trial-rejected",
        }
    ]

    candidate_rows = _jsonl(result.candidate_results_path)
    assert [row["trial_id"] for row in candidate_rows] == ["trial-accepted", "trial-rejected"]
    assert all(str(row["manifest_hash"]).startswith("sha256:") for row in candidate_rows)

    audit_records = ResearchAuditLog(result.audit_log_path).list()
    assert [record.record_type for record in audit_records] == [
        "manifest_loaded",
        "evidence_bundle_created",
        "artifact_graph_written",
        "research_run_completed",
        "manifest_loaded",
        "research_run_completed",
    ]
    assert audit_records[0].payload["trial_id"] == "trial-accepted"
    assert audit_records[3].payload["status"] == "succeeded"
    assert audit_records[5].payload["status"] == "failed"
    assert ResearchAuditLog(result.audit_log_path).verify_hash_chain() == ()


def test_experiment_runner_outputs_are_deterministic_for_same_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_backtest_pipeline_runner(monkeypatch)
    data_path = _write_bars(tmp_path)
    runner = ResearchExperimentRunner(
        repo_root=Path.cwd(),
        clock=DeterministicResearchClock(datetime(2026, 5, 26, tzinfo=UTC)),
    )
    job = _job(tmp_path, data_path)

    first = runner.run(job)
    first_summary = first.workflow_summary_path.read_text(encoding="utf-8")
    first_rows = first.candidate_results_path.read_text(encoding="utf-8")
    second = runner.run(job)

    assert second.to_payload() == first.to_payload()
    assert second.workflow_summary_path.read_text(encoding="utf-8") == first_summary
    assert second.candidate_results_path.read_text(encoding="utf-8") == first_rows


def _job(tmp_path: Path, data_path: Path) -> ResearchExperimentJob:
    return ResearchExperimentJob(
        job_id="experiment-job",
        generation_id="generation-000",
        manifest_payload={
            "campaign_id": "campaign-real",
            "data": {
                "calendar": "research-calendar",
                "checked_paths": [str(data_path)],
                "dataset_id": "research-metals-1m",
                "end": "2026-01-02T00:03:00+00:00",
                "start": "2026-01-02T00:00:00+00:00",
                "timeframe": "1m",
            },
            "run": {
                "created_at": "2026-05-26T00:00:00+00:00",
                "id": "experiment-job",
                "owner": "research",
                "question": "research experiment acceptance",
            },
            "strategy": {
                "id": "metals_research_momentum",
                "source_module": "strategies.research.metals_research_momentum",
                "target_module": "strategies.production.metals_research_momentum",
            },
            "backtest_pipeline": {"backtest_config_path": str(data_path.with_suffix(".yaml"))},
        },
        output_root=tmp_path / "runner-output",
        trials=(
            {
                "family": "momentum",
                "parameters": {"lookback": 4, "threshold": 0.1},
                "trial_id": "trial-accepted",
            },
            {
                "failure_reason": "research candidate rejected before execution",
                "family": "spread",
                "parameters": {"lookback": 8, "threshold": 0.5},
                "status": "failed",
                "trial_id": "trial-rejected",
            },
        ),
    )


def _write_bars(tmp_path: Path) -> Path:
    path = tmp_path / "research-bars.csv"
    path.write_text(
        "\n".join(
            [
                "timestamp,close",
                "2026-01-02T00:00:00+00:00,100.0",
                "2026-01-02T00:01:00+00:00,100.5",
                "2026-01-02T00:02:00+00:00,101.0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.with_suffix(".yaml").write_text(
        "\n".join(
            [
                "mode: backtest",
                "start: '2026-01-02T00:00:00+00:00'",
                "end: '2026-01-02T00:03:00+00:00'",
                "cost_model:",
                "  fixed_commission_per_contract: '0'",
                "  slippage_bps: '0'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _patch_backtest_pipeline_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeBacktestPipelineRunner:
        def run(self, job: Any) -> tuple[OptimizationResult, ...]:
            run_dir = job.output_root / "run-0000"
            run_dir.mkdir(parents=True)
            manifest_path = run_dir / "manifest.json"
            artifacts = {
                "equity_curve": {"rows": 3, "sha256": "sha256:equity"},
                "fills": {"rows": 42, "sha256": "sha256:fills"},
                "statistics": {"rows": 1, "sha256": "sha256:statistics"},
                "trade_ledger": {"rows": 42, "sha256": "sha256:trade-ledger"},
            }
            manifest_path.write_text(
                json.dumps(
                    {
                        "artifacts": artifacts,
                        "dataset_metadata": [{"dataset_id": "test"}],
                        "initial_cash": "1000000",
                        "manifest_hash": "sha256:research-backtest-manifest",
                        "metrics": {},
                        "statistics": {
                            "avg_gross_exposure": "0.5",
                            "max_drawdown": "0.10",
                            "profit_factor": "1.40",
                            "sharpe_ratio": "1.25",
                            "total_commission": "0",
                            "total_return": "0.12",
                            "total_slippage": "0",
                        },
                        "statistics_hash": "sha256:statistics",
                    }
                ),
                encoding="utf-8",
            )
            return (
                OptimizationResult(
                    parameters=dict(next(iter(job.parameter_grid))),
                    manifest_path=manifest_path,
                    manifest_hash="sha256:research-backtest-manifest",
                    objective_value=Decimal("1.25"),
                ),
            )

    monkeypatch.setattr(
        experiment_orchestration, "BacktestPipelineRunner", FakeBacktestPipelineRunner
    )
    # QTS-FINAL-011 moved the validation-rerun invocation into trial_helpers
    monkeypatch.setattr(trial_helpers, "BacktestPipelineRunner", FakeBacktestPipelineRunner)


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
