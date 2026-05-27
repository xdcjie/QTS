from __future__ import annotations

from pathlib import Path
from typing import Any

from qts.research.audit_log import ResearchAuditLog
from qts.research.orchestrator.experiment_runner import ResearchExperimentJob
from qts.research.orchestrator.queue import (
    ExperimentQueue,
    ExperimentRetryPolicy,
    ExperimentScheduler,
    ExperimentWorker,
)


def test_queue_order_and_resume_state_are_deterministic(tmp_path: Path) -> None:
    queue = ExperimentQueue(jobs=(_job(tmp_path, "job-b"), _job(tmp_path, "job-a")))

    assert queue.pending_job_ids == ("job-a", "job-b")
    queue.stop()
    stopped_result = ExperimentScheduler(
        queue=queue,
        worker=_RecordingWorker(),
        retry_policy=ExperimentRetryPolicy(max_attempts=1),
    ).run()

    assert stopped_result.status == "stopped"
    assert stopped_result.completed_job_ids == ()
    assert queue.to_payload()["stopped"] is True

    resumed = ExperimentQueue.from_payload(queue.to_payload())
    resumed.resume()
    result = ExperimentScheduler(
        queue=resumed,
        worker=_RecordingWorker(),
        retry_policy=ExperimentRetryPolicy(max_attempts=1),
    ).run()

    assert result.status == "completed"
    assert result.completed_job_ids == ("job-a", "job-b")
    assert resumed.to_payload()["pending"] == []


def test_failed_jobs_are_retried_with_audit_payload(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    queue = ExperimentQueue(jobs=(_job(tmp_path, "job-a"),))
    worker = _RecordingWorker(fail_once={"job-a"})

    result = ExperimentScheduler(
        queue=queue,
        worker=worker,
        retry_policy=ExperimentRetryPolicy(max_attempts=2),
    ).run(audit_log=audit_log)

    assert result.status == "completed_with_retries"
    assert result.completed_job_ids == ("job-a-retry-002",)
    assert result.failed_job_ids == ("job-a",)
    assert worker.seen_job_ids == ("job-a", "job-a-retry-002")
    records = audit_log.list()
    assert len(records) == 1
    assert records[0].record_type == "research_run_completed"
    assert records[0].payload == {
        "attempt": 2,
        "event": "experiment_retry_scheduled",
        "failure_reason": "planned failure",
        "job_id": "job-a-retry-002",
        "parent_job_id": "job-a",
    }
    assert audit_log.verify_hash_chain() == ()


def test_experiment_worker_runs_job_through_runner(tmp_path: Path) -> None:
    job = _job(tmp_path, "job-worker")
    result = ExperimentWorker(repo_root=Path.cwd()).run(job)

    assert result.job_id == "job-worker"
    assert result.status == "completed"
    assert result.trials[0].status == "succeeded"


class _RecordingWorker:
    def __init__(self, *, fail_once: set[str] | None = None) -> None:
        self._fail_once = set(fail_once or ())
        self._seen: list[str] = []

    @property
    def seen_job_ids(self) -> tuple[str, ...]:
        return tuple(self._seen)

    def run(self, job: ResearchExperimentJob) -> dict[str, Any]:
        self._seen.append(job.job_id)
        parent = job.parent_job_id or job.job_id
        if parent in self._fail_once and job.attempt == 1:
            raise RuntimeError("planned failure")
        return {"job_id": job.job_id, "status": "completed"}


def _job(tmp_path: Path, job_id: str) -> ResearchExperimentJob:
    data_path = tmp_path / f"{job_id}-bars.csv"
    data_path.write_text(
        "timestamp,close\n2026-01-02T00:00:00+00:00,100\n",
        encoding="utf-8",
    )
    return ResearchExperimentJob(
        job_id=job_id,
        generation_id="generation-000",
        manifest_payload={
            "data": {
                "calendar": "fixture-calendar",
                "checked_paths": [str(data_path)],
                "dataset_id": "fixture-metals",
                "end": "2026-01-02T00:01:00+00:00",
                "start": "2026-01-02T00:00:00+00:00",
                "timeframe": "1m",
            },
            "run": {"id": job_id, "question": "fixture"},
            "strategy": {
                "id": "metals_fixture",
                "source_module": "strategies.research.metals_fixture",
                "target_module": "strategies.production.metals_fixture",
            },
        },
        output_root=tmp_path / "runs",
        trials=(
            {
                "family": "momentum",
                "metrics": _metrics(),
                "parameters": {"lookback": 3},
                "trial_id": f"{job_id}-trial",
            },
        ),
    )


def _metrics() -> dict[str, dict[str, object]]:
    return {
        "execution": {"cost_impact": 0.01, "slippage_sensitivity": 0.02},
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {"profit_factor": 1.4, "sharpe": 1.1},
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {"parameter_sensitivity": 0.8, "walk_forward_consistency": 0.75},
        "trading": {"oos_months": 12.0, "oos_trade_count": 40},
    }
