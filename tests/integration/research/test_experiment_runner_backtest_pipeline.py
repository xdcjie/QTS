from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import qts.research.orchestrator.experiment_orchestration as experiment_orchestration
from qts.research.optimizer.result import OptimizationResult
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentRunner,
)


def test_experiment_runner_fails_when_backtest_manifest_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MissingManifestRunner:
        def run(self, job: Any) -> tuple[OptimizationResult, ...]:
            return (
                OptimizationResult(
                    parameters=dict(next(iter(job.parameter_grid))),
                    manifest_path=job.output_root / "missing" / "manifest.json",
                    manifest_hash="sha256:missing",
                    objective_value=Decimal("1.0"),
                ),
            )

    monkeypatch.setattr(experiment_orchestration, "BacktestPipelineRunner", MissingManifestRunner)
    backtest_config_path = tmp_path / "backtest.yaml"
    backtest_config_path.write_text("mode: backtest\n", encoding="utf-8")
    job = ResearchExperimentJob(
        job_id="job-001",
        generation_id="generation-000",
        manifest_payload={
            "data": {"calendar": "CME", "dataset_id": "data", "timeframe": "1m"},
            "run": {"id": "job-001", "question": "missing manifest"},
            "strategy": {"id": "strategy"},
        },
        output_root=tmp_path / "runs",
        trials=(
            {
                "backtest_pipeline": {"backtest_config_path": str(backtest_config_path)},
                "family": "momentum",
                "parameters": {"lookback": 5},
                "trial_id": "trial-001",
            },
        ),
    )

    with pytest.raises(FileNotFoundError):
        ResearchExperimentRunner(repo_root=Path.cwd()).run(job)
