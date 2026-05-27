from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import qts.research.orchestrator.experiment_runner as experiment_runner
from qts.research.optimizer.result import OptimizationResult
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentRunner,
)


def test_backtest_pipeline_mode_derives_metrics_from_backtest_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_jobs: list[Any] = []

    class FakeBacktestPipelineRunner:
        def run(self, job: Any) -> tuple[OptimizationResult, ...]:
            captured_jobs.append(job)
            run_dir = job.output_root / "run-0000"
            run_dir.mkdir(parents=True)
            manifest_path = run_dir / "manifest.json"
            manifest_payload = {
                "artifacts": {
                    "fills": {"rows": 11},
                    "trade_ledger": {"rows": 11},
                },
                "manifest_hash": "sha256:real-backtest-manifest",
                "metrics": {
                    "max_drawdown": "0.04",
                    "sharpe_ratio": "1.75",
                    "total_return": "0.18",
                    "total_trades": 11,
                },
                "statistics": {"profit_factor": "1.62"},
            }
            manifest_path.write_text(json.dumps(manifest_payload), encoding="utf-8")
            return (
                OptimizationResult(
                    parameters={"lookback": 5, "threshold": "0.2"},
                    manifest_path=manifest_path,
                    manifest_hash="sha256:real-backtest-manifest",
                    objective_value=Decimal("1.75"),
                ),
            )

    monkeypatch.setattr(experiment_runner, "BacktestPipelineRunner", FakeBacktestPipelineRunner)

    backtest_config_path = tmp_path / "backtest.yaml"
    backtest_config_path.write_text("mode: backtest\n", encoding="utf-8")
    job = _job(
        tmp_path,
        execution_mode="backtest_pipeline",
        manifest_payload={
            **_manifest_payload(),
            "backtest_pipeline": {
                "backtest_config_path": str(backtest_config_path),
                "objective_metric": "sharpe_ratio",
            },
        },
        trials=(
            {
                "family": "momentum",
                "parameters": {"lookback": 5, "threshold": "0.2"},
                "trial_id": "trial-real",
            },
        ),
    )

    result = ResearchExperimentRunner(repo_root=Path.cwd()).run(job)

    assert len(captured_jobs) == 1
    pipeline_job = captured_jobs[0]
    assert pipeline_job.base_config_path == backtest_config_path
    assert list(pipeline_job.parameter_grid) == [{"lookback": 5, "threshold": "0.2"}]
    assert pipeline_job.objective_metric == "sharpe_ratio"

    trial = result.trials[0]
    backtest_manifest_path = (
        tmp_path
        / "runner-output/generation-000/job-001/trials/trial-real/backtest/run-0000/manifest.json"
    )
    assert trial.manifest_hash == "sha256:real-backtest-manifest"
    assert trial.manifest_path == backtest_manifest_path
    metrics = json.loads(trial.metrics_path.read_text(encoding="utf-8"))
    assert metrics["backtest"] == {
        "manifest_hash": "sha256:real-backtest-manifest",
        "manifest_path": str(backtest_manifest_path),
        "objective_metric": "sharpe_ratio",
        "objective_value": "1.75",
        "parameters": {"lookback": 5, "threshold": "0.2"},
    }
    assert metrics["quality"]["sharpe"] == 1.75
    assert metrics["risk"]["max_drawdown"] == 0.04
    assert metrics["trading"]["oos_trade_count"] == 11
    assert metrics["research"]["metrics_source"] == "backtest_pipeline"
    manifest = json.loads(
        (
            tmp_path / "runner-output/generation-000/job-001/trials/trial-real/manifest.json"
        ).read_text(encoding="utf-8")
    )
    backtest_hash = manifest["artifact_hashes"]["backtest_manifest"]
    assert manifest["backtest_manifest_path"] == metrics["backtest"]["manifest_path"]
    assert manifest["artifact_paths_by_hash"][backtest_hash] == metrics["backtest"]["manifest_path"]


def test_backtest_pipeline_mode_rejects_payload_supplied_metrics(tmp_path: Path) -> None:
    backtest_config_path = tmp_path / "backtest.yaml"
    backtest_config_path.write_text("mode: backtest\n", encoding="utf-8")
    job = _job(
        tmp_path,
        manifest_payload={
            **_manifest_payload(),
            "backtest_pipeline": {"backtest_config_path": str(backtest_config_path)},
        },
        trials=(
            {
                "family": "momentum",
                "metrics": {"quality": {"sharpe": 99}},
                "parameters": {"lookback": 5},
                "trial_id": "trial-payload-metrics",
            },
        ),
    )

    with pytest.raises(ValueError, match="backtest_pipeline trials must derive metrics"):
        ResearchExperimentRunner(repo_root=Path.cwd()).run(job)


def test_backtest_pipeline_is_the_only_execution_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported execution_mode"):
        _job(
            tmp_path,
            execution_mode="payload_metrics_mode",
            trials=(
                {
                    "family": "momentum",
                    "parameters": {"lookback": 5},
                    "trial_id": "trial-payload-metrics-mode",
                },
            ),
        )


def _job(
    tmp_path: Path,
    *,
    execution_mode: str | None = None,
    manifest_payload: dict[str, Any] | None = None,
    trials: tuple[dict[str, Any], ...],
) -> ResearchExperimentJob:
    kwargs: dict[str, Any] = {}
    if execution_mode is not None:
        kwargs["execution_mode"] = execution_mode
    return ResearchExperimentJob(
        job_id="job-001",
        generation_id="generation-000",
        manifest_payload=manifest_payload or _manifest_payload(),
        output_root=tmp_path / "runner-output",
        trials=trials,
        **kwargs,
    )


def _manifest_payload() -> dict[str, Any]:
    return {
        "campaign_id": "campaign-real",
        "data": {
            "calendar": "CME",
            "dataset_id": "metals-1m",
            "end": "2026-01-02T00:03:00+00:00",
            "start": "2026-01-02T00:00:00+00:00",
            "timeframe": "1m",
        },
        "run": {"id": "job-001", "owner": "research", "question": "real pipeline"},
        "strategy": {"id": "metals_momentum"},
    }
