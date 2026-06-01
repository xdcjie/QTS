"""Deterministic research experiment runner artifacts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from qts.research.clock import ResearchClock
from qts.research.orchestrator import experiment_orchestration
from qts.research.orchestrator.experiment_types import (
    ResearchExperimentJob,
    ResearchExperimentResult,
    ResearchTrialResult,
)
from qts.research.orchestrator.trial_evidence_support import TrialEvidenceSupport
from qts.research.orchestrator.validation_artifact_reader import (
    PromotionThresholds,
)


class ResearchExperimentRunner:
    """Owns deterministic research experiment artifact production."""

    def __init__(
        self,
        *,
        repo_root: Path,
        promotion_thresholds: PromotionThresholds | None = None,
        clock: ResearchClock | None = None,
    ) -> None:
        self._support = TrialEvidenceSupport(
            repo_root=repo_root, promotion_thresholds=promotion_thresholds, clock=clock
        )

    def run(self, job: ResearchExperimentJob) -> ResearchExperimentResult:
        """Run an experiment job through the trial campaign and return its result."""
        return experiment_orchestration.run(self._support, job)

    def write_validation_artifacts_for_trial(
        self,
        *,
        trial: Mapping[str, Any],
        trial_result: ResearchTrialResult,
        active_correlation_context: Sequence[Mapping[str, Any]] = (),
    ) -> Mapping[str, str]:
        """Run survivor validation and attach promotion-grade artifacts to the trial summary."""
        return experiment_orchestration.write_validation_artifacts_for_trial(
            self._support,
            trial=trial,
            trial_result=trial_result,
            active_correlation_context=active_correlation_context,
        )


__all__ = [
    "ResearchExperimentJob",
    "ResearchExperimentResult",
    "ResearchExperimentRunner",
    "ResearchTrialResult",
]
