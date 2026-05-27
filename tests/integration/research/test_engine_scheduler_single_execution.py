from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from qts.research.orchestrator.queue import ExperimentScheduler, ExperimentWorker

from tests.integration.research._autonomous_engine_plan_helpers import run_engine


def test_engine_executes_generation_job_once_through_scheduler(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_worker_run = ExperimentWorker.run
    runner_calls: list[str] = []
    scheduler_calls: list[str] = []

    class CountingScheduler(ExperimentScheduler):
        def run(self, *, audit_log: Any = None) -> Any:
            scheduler_calls.append("run")
            return super().run(audit_log=audit_log)

    def counting_worker_run(self: ExperimentWorker, job: Any) -> Any:
        runner_calls.append(job.job_id)
        return original_worker_run(self, job)

    monkeypatch.setattr(ExperimentWorker, "run", counting_worker_run)
    monkeypatch.setattr(
        "qts.research.engine.autonomous_research_engine.ExperimentScheduler",
        CountingScheduler,
    )

    run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=2,
        max_total_trials=2,
    )

    assert scheduler_calls == ["run"]
    assert runner_calls == ["engine_campaign-generation-000"]
