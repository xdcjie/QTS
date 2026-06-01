"""Deterministic experiment queue and retry orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from qts.research.audit_log import ResearchAuditLog
from qts.research.clock import ResearchClock, system_research_clock
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentJob,
    ResearchExperimentResult,
    ResearchExperimentRunner,
)


@runtime_checkable
class _PayloadConvertible(Protocol):
    def to_payload(self) -> Mapping[str, Any]: ...


@dataclass(frozen=True, slots=True)
class ExperimentScheduleResult:
    """Summary returned after scheduler execution."""

    status: str
    completed_job_ids: tuple[str, ...] = ()
    completed_results: Mapping[str, Mapping[str, Any]] | None = None
    failed_job_ids: tuple[str, ...] = ()
    retried_job_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        results = self.completed_results or {}
        object.__setattr__(
            self,
            "completed_results",
            {str(job_id): dict(payload) for job_id, payload in sorted(results.items())},
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready scheduler result."""

        return {
            "completed_job_ids": list(self.completed_job_ids),
            "completed_results": {
                job_id: dict(payload)
                for job_id, payload in sorted((self.completed_results or {}).items())
            },
            "failed_job_ids": list(self.failed_job_ids),
            "retried_job_ids": list(self.retried_job_ids),
            "status": self.status,
        }


class ExperimentQueue:
    """Own deterministic experiment job state."""

    def __init__(self, *, jobs: Sequence[ResearchExperimentJob] = ()) -> None:
        self._pending = list(self._ordered_jobs(jobs))
        self._running: dict[str, ResearchExperimentJob] = {}
        self._completed: dict[str, Mapping[str, Any]] = {}
        self._failed: dict[str, Mapping[str, Any]] = {}
        self._stopped = False

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ExperimentQueue:
        """Restore queue state from a deterministic payload."""

        queue = cls(jobs=cls._jobs(payload.get("pending", ()), "pending"))
        queue._running = {
            job.job_id: job for job in cls._jobs(payload.get("running", ()), "running")
        }
        queue._completed = cls._mapping_by_id(payload.get("completed", ()), "completed")
        queue._failed = cls._mapping_by_id(payload.get("failed", ()), "failed")
        queue._stopped = bool(payload.get("stopped", False))
        return queue

    @property
    def pending_job_ids(self) -> tuple[str, ...]:
        """Return pending job IDs in deterministic execution order."""

        return tuple(job.job_id for job in self._pending)

    @property
    def completed_job_ids(self) -> tuple[str, ...]:
        """Return completed job IDs in deterministic order."""

        return tuple(sorted(self._completed))

    @property
    def completed_results(self) -> Mapping[str, Mapping[str, Any]]:
        """Return completed job result payloads keyed by job ID."""

        return {job_id: dict(payload) for job_id, payload in sorted(self._completed.items())}

    @property
    def failed_job_ids(self) -> tuple[str, ...]:
        """Return failed job IDs in deterministic order."""

        return tuple(sorted(self._failed))

    @property
    def stopped(self) -> bool:
        """Return whether the queue is paused."""

        return self._stopped

    def stop(self) -> None:
        """Pause dispatch without losing pending state."""

        self._stopped = True

    def resume(self) -> None:
        """Resume dispatch from persisted state."""

        self._stopped = False

    def next_job(self) -> ResearchExperimentJob | None:
        """Return and mark the next pending job as running."""

        if self._stopped or not self._pending:
            return None
        job = self._pending.pop(0)
        self._running[job.job_id] = job
        return job

    def add(self, job: ResearchExperimentJob) -> None:
        """Add a pending job and restore deterministic pending order."""

        if job.job_id in self._running or job.job_id in self._completed:
            raise ValueError(f"job already active or completed: {job.job_id}")
        if any(pending.job_id == job.job_id for pending in self._pending):
            raise ValueError(f"job already pending: {job.job_id}")
        self._pending.append(job)
        self._pending = list(self._ordered_jobs(self._pending))

    def mark_completed(self, job_id: str, result_payload: Mapping[str, Any]) -> None:
        """Move a running job to completed state."""

        self._running.pop(job_id, None)
        self._completed[job_id] = dict(result_payload)

    def mark_failed(self, job_id: str, failure_reason: str) -> ResearchExperimentJob:
        """Move a running job to failed state and return the failed job."""

        job = self._running.pop(job_id, None)
        if job is None:
            raise ValueError(f"job is not running: {job_id}")
        self._failed[job_id] = {
            "failure_reason": failure_reason,
            "job": job.to_payload(),
            "job_id": job_id,
        }
        return job

    def to_payload(self) -> dict[str, Any]:
        """Return deterministic queue state for persistence."""

        return {
            "completed": [
                self._state_row(job_id, payload)
                for job_id, payload in sorted(self._completed.items())
            ],
            "failed": [
                self._state_row(job_id, payload) for job_id, payload in sorted(self._failed.items())
            ],
            "pending": [job.to_payload() for job in self._pending],
            "running": [
                job.to_payload() for job in self._ordered_jobs(tuple(self._running.values()))
            ],
            "stopped": self._stopped,
        }

    def _state_row(self, job_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return {"job_id": job_id, "payload": dict(payload)}

    def _ordered_jobs(
        self,
        jobs: Iterable[ResearchExperimentJob],
    ) -> tuple[ResearchExperimentJob, ...]:
        return tuple(
            sorted(
                jobs,
                key=lambda job: (
                    job.generation_id,
                    job.parent_job_id or job.job_id,
                    job.attempt,
                    job.job_id,
                ),
            )
        )

    @classmethod
    def _jobs(cls, value: Any, field_name: str) -> tuple[ResearchExperimentJob, ...]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise ValueError(f"{field_name} must be a sequence")
        return tuple(ResearchExperimentJob.from_payload(item) for item in value)

    @staticmethod
    def _mapping_by_id(value: Any, field_name: str) -> dict[str, Mapping[str, Any]]:
        if not isinstance(value, Sequence) or isinstance(value, str):
            raise ValueError(f"{field_name} must be a sequence")
        result: dict[str, Mapping[str, Any]] = {}
        for item in value:
            if not isinstance(item, Mapping):
                raise ValueError(f"{field_name} rows must be mappings")
            job_id = item.get("job_id")
            payload = item.get("payload")
            if not isinstance(job_id, str) or not job_id.strip():
                raise ValueError(f"{field_name}.job_id is required")
            if not isinstance(payload, Mapping):
                raise ValueError(f"{field_name}.payload must be a mapping")
            result[job_id] = dict(payload)
        return result


@dataclass(frozen=True, slots=True)
class ExperimentRetryPolicy:
    """Own retry eligibility and deterministic retry job construction."""

    max_attempts: int = 1
    clock: ResearchClock = field(default_factory=system_research_clock)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")

    def can_retry(self, job: ResearchExperimentJob) -> bool:
        """Return whether this job may be retried."""

        return job.attempt < self.max_attempts

    def retry(
        self,
        job: ResearchExperimentJob,
        *,
        failure_reason: str,
        audit_log: ResearchAuditLog | None = None,
    ) -> ResearchExperimentJob:
        """Return the next-attempt retry job and append audit evidence."""

        if not self.can_retry(job):
            raise ValueError(f"retry budget exhausted for job: {job.job_id}")
        attempt = job.attempt + 1
        parent_job_id = job.parent_job_id or job.job_id
        retry_job = ResearchExperimentJob(
            job_id=f"{parent_job_id}-retry-{attempt:03d}",
            generation_id=job.generation_id,
            manifest_payload=job.manifest_payload,
            output_root=job.output_root,
            trials=job.trials,
            attempt=attempt,
            execution_mode=job.execution_mode,
            parent_job_id=parent_job_id,
        )
        if audit_log is not None:
            audit_log.append(
                "research_run_completed",
                {
                    "attempt": attempt,
                    "event": "experiment_retry_scheduled",
                    "failure_reason": failure_reason,
                    "job_id": retry_job.job_id,
                    "parent_job_id": parent_job_id,
                },
                created_at=self.clock.now(offset_seconds=attempt),
            )
        return retry_job


class ExperimentWorker:
    """Run queued experiment jobs through ``ResearchExperimentRunner``."""

    def __init__(
        self,
        *,
        repo_root: Path,
        runner: ResearchExperimentRunner | None = None,
        clock: ResearchClock | None = None,
    ) -> None:
        self._runner = runner or ResearchExperimentRunner(repo_root=repo_root, clock=clock)

    def run(self, job: ResearchExperimentJob) -> ResearchExperimentResult:
        """Run one experiment job."""

        return self._runner.run(job)


class ExperimentScheduler:
    """Drain an experiment queue through a worker with bounded retries."""

    def __init__(
        self,
        *,
        queue: ExperimentQueue,
        worker: Any,
        retry_policy: ExperimentRetryPolicy,
    ) -> None:
        self._queue = queue
        self._worker = worker
        self._retry_policy = retry_policy

    def run(self, *, audit_log: ResearchAuditLog | None = None) -> ExperimentScheduleResult:
        """Run until the queue is empty, stopped, or no retry budget remains."""

        retried_job_ids: list[str] = []
        while True:
            job = self._queue.next_job()
            if job is None:
                break
            try:
                result = self._worker.run(job)
            except Exception as exc:
                failed_job = self._queue.mark_failed(job.job_id, str(exc))
                if self._retry_policy.can_retry(failed_job):
                    retry_job = self._retry_policy.retry(
                        failed_job,
                        failure_reason=str(exc),
                        audit_log=audit_log,
                    )
                    retried_job_ids.append(retry_job.job_id)
                    self._queue.add(retry_job)
                continue
            self._queue.mark_completed(job.job_id, self._result_payload(result))

        if self._queue.stopped:
            status = "stopped"
        elif retried_job_ids and not self._unretriable_failures():
            status = "completed_with_retries"
        elif self._unretriable_failures():
            status = "failed"
        else:
            status = "completed"
        return ExperimentScheduleResult(
            status=status,
            completed_job_ids=self._queue.completed_job_ids,
            completed_results=self._queue.completed_results,
            failed_job_ids=self._queue.failed_job_ids,
            retried_job_ids=tuple(retried_job_ids),
        )

    def _unretriable_failures(self) -> bool:
        for failed_job_id in self._queue.failed_job_ids:
            failed_payload = self._queue.to_payload()["failed"]
            for row in failed_payload:
                if row["job_id"] != failed_job_id:
                    continue
                job_payload = row["payload"].get("job")
                if not isinstance(job_payload, Mapping):
                    return True
                job = ResearchExperimentJob.from_payload(job_payload)
                if not self._retry_policy.can_retry(job):
                    return True
        return False

    def _result_payload(self, result: Any) -> Mapping[str, Any]:
        if isinstance(result, _PayloadConvertible):
            payload = result.to_payload()
            if isinstance(payload, Mapping):
                return payload
        if isinstance(result, Mapping):
            return dict(result)
        return {"result": str(result)}


__all__ = [
    "ExperimentQueue",
    "ExperimentRetryPolicy",
    "ExperimentScheduleResult",
    "ExperimentScheduler",
    "ExperimentWorker",
]
