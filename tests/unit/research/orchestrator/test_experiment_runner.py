from __future__ import annotations

import json
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentRunner,
)


def test_experiment_runner_writes_required_trial_artifacts(tmp_path: Path) -> None:
    data_path = _write_bars(tmp_path)
    job = _job(tmp_path, data_path)

    result = ResearchExperimentRunner(repo_root=Path.cwd()).run(job)

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

    data_quality = json.loads(accepted.data_quality_path.read_text(encoding="utf-8"))
    reproducibility = json.loads(accepted.reproducibility_path.read_text(encoding="utf-8"))
    assert data_quality["schema_version"] == 2
    assert data_quality["accepted"] is True
    assert reproducibility["schema_version"] == 2
    assert reproducibility["manifest_hash"] == accepted.manifest_hash

    rejected = result.trials[1]
    assert rejected.status == "failed"
    assert rejected.failures_path is not None
    assert rejected.failures_path.exists()
    failure_rows = _jsonl(result.failures_path)
    assert failure_rows == [
        {
            "failure_reason": "simulated fixture rejection",
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
        "research_run_completed",
        "manifest_loaded",
        "research_run_completed",
    ]
    assert audit_records[0].payload["trial_id"] == "trial-accepted"
    assert audit_records[1].payload["status"] == "succeeded"
    assert audit_records[3].payload["status"] == "failed"
    assert ResearchAuditLog(result.audit_log_path).verify_hash_chain() == ()


def test_experiment_runner_outputs_are_deterministic_for_same_job(tmp_path: Path) -> None:
    data_path = _write_bars(tmp_path)
    runner = ResearchExperimentRunner(repo_root=Path.cwd())
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
            "campaign_id": "campaign-fixture",
            "data": {
                "calendar": "fixture-calendar",
                "checked_paths": [str(data_path)],
                "dataset_id": "fixture-metals-1m",
                "end": "2026-01-02T00:03:00+00:00",
                "start": "2026-01-02T00:00:00+00:00",
                "timeframe": "1m",
            },
            "run": {
                "created_at": "2026-05-26T00:00:00+00:00",
                "id": "experiment-job",
                "owner": "research",
                "question": "fixture acceptance",
            },
            "strategy": {
                "id": "metals_fixture_momentum",
                "source_module": "strategies.research.metals_fixture_momentum",
                "target_module": "strategies.production.metals_fixture_momentum",
            },
        },
        output_root=tmp_path / "runner-output",
        trials=(
            {
                "family": "momentum",
                "metrics": _promotion_metrics(sharpe=1.25, trade_count=42),
                "parameters": {"lookback": 4, "threshold": 0.1},
                "trial_id": "trial-accepted",
            },
            {
                "failure_reason": "simulated fixture rejection",
                "family": "spread",
                "metrics": _promotion_metrics(sharpe=0.2, trade_count=3),
                "parameters": {"lookback": 8, "threshold": 0.5},
                "status": "failed",
                "trial_id": "trial-rejected",
            },
        ),
    )


def _write_bars(tmp_path: Path) -> Path:
    path = tmp_path / "fixture-bars.csv"
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
    return path


def _promotion_metrics(*, sharpe: float, trade_count: int) -> dict[str, dict[str, object]]:
    return {
        "execution": {"cost_impact": 0.01, "slippage_sensitivity": 0.02},
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {"profit_factor": 1.4, "sharpe": sharpe},
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {"parameter_sensitivity": 0.8, "walk_forward_consistency": 0.75},
        "trading": {"oos_months": 12.0, "oos_trade_count": trade_count},
    }


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
