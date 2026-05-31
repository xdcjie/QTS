"""Autonomous research campaign value records.

The campaign run/generation/result dataclasses extracted from AutonomousResearchEngine
(QTS-FINAL-011) so the records and the engine orchestration have separate owners.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qts.research.campaign import ResearchCampaignConfig
from qts.research.orchestrator.experiment_runner import (
    ResearchExperimentResult,
)
from qts.research.planner import (
    GenerationApprovalRecord,
)


@dataclass(frozen=True, slots=True)
class AutonomousResearchRun:
    """Configuration for one bounded autonomous research campaign."""

    campaign_id: str
    output_root: Path
    universe: tuple[str, ...]
    families: tuple[str, ...]
    max_generations: int
    trials_per_generation: int
    data_paths: Mapping[str, Path] | None = None
    calendar: str = "research-calendar"
    timeframe: str = "1m"
    dataset_id: str = "research-data-contract"
    approval_policy: str = "manual_gate"
    fill_policy: str = "next_bar_open"
    optimistic_fill_waiver: bool = False
    campaign_config: ResearchCampaignConfig | None = None
    approval_records: tuple[GenerationApprovalRecord, ...] = ()

    def __post_init__(self) -> None:
        if not self.campaign_id.strip():
            raise ValueError("campaign_id is required")
        if not self.universe:
            raise ValueError("universe must not be empty")
        if not self.families:
            raise ValueError("families must not be empty")
        if self.max_generations < 1:
            raise ValueError("max_generations must be positive")
        if self.trials_per_generation < 1:
            raise ValueError("trials_per_generation must be positive")
        object.__setattr__(self, "output_root", Path(self.output_root))
        object.__setattr__(self, "universe", tuple(str(item) for item in self.universe))
        object.__setattr__(self, "families", tuple(str(item) for item in self.families))
        object.__setattr__(
            self,
            "data_paths",
            None
            if self.data_paths is None
            else {str(root): Path(path) for root, path in self.data_paths.items()},
        )
        object.__setattr__(self, "approval_records", tuple(self.approval_records))
        from qts.domain.execution_timing import FillPolicy

        fill_policy = FillPolicy.from_value(self.fill_policy).value
        object.__setattr__(self, "fill_policy", fill_policy)
        if fill_policy == FillPolicy.SAME_BAR_CLOSE.value and not self.optimistic_fill_waiver:
            raise ValueError(
                "fill_policy=same_bar_close is optimistic look-ahead and requires "
                "optimistic_fill_waiver=true"
            )

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        *,
        data_paths: Mapping[str, str | Path] | None = None,
        output_root: str | Path | None = None,
        approval_records: Sequence[GenerationApprovalRecord] = (),
    ) -> AutonomousResearchRun:
        """Load a campaign run from a validated ResearchCampaignConfig YAML file."""

        config_path = Path(path)
        campaign = ResearchCampaignConfig.from_yaml(config_path)
        return cls(
            campaign_id=campaign.campaign_id,
            output_root=Path(output_root)
            if output_root is not None
            else Path("runs/research/acceptance") / campaign.campaign_id,
            universe=campaign.universe.roots,
            families=tuple(family.id for family in campaign.families),
            max_generations=campaign.budget.max_generations,
            trials_per_generation=campaign.budget.max_trials_per_generation,
            data_paths=None
            if data_paths is None
            else {str(root): Path(path) for root, path in data_paths.items()},
            calendar=campaign.universe.calendar,
            timeframe=campaign.universe.timeframe,
            dataset_id=campaign.universe.dataset_id,
            fill_policy=campaign.execution.fill_policy,
            optimistic_fill_waiver=campaign.execution.optimistic_fill_waiver,
            campaign_config=campaign,
            approval_records=tuple(approval_records),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready campaign payload."""

        return {
            "approval_policy": self.approval_policy,
            "budget": {
                "max_generations": self.max_generations,
                "trials_per_generation": self.trials_per_generation,
            },
            "campaign_id": self.campaign_id,
            "campaign_config": None
            if self.campaign_config is None
            else self.campaign_config.to_payload(),
            "calendar": self.calendar,
            "data_paths": {
                root: str(path) for root, path in sorted((self.data_paths or {}).items())
            },
            "dataset_id": self.dataset_id,
            "families": list(self.families),
            "generation_approval_hashes": [
                record.approval_hash for record in self.approval_records
            ],
            "fill_policy": self.fill_policy,
            "optimistic_fill_waiver": self.optimistic_fill_waiver,
            "output_root": str(self.output_root),
            "timeframe": self.timeframe,
            "universe": list(self.universe),
        }


@dataclass(frozen=True, slots=True)
class AutonomousResearchGeneration:
    """Artifacts produced by one autonomous generation."""

    generation_id: str
    trial_count: int
    selected_count: int
    rejected_count: int
    audit_record_count: int
    landscape_path: Path
    next_generation_proposal_path: Path
    experiment_result: ResearchExperimentResult

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready generation summary."""

        return {
            "audit_record_count": self.audit_record_count,
            "experiment_result": self.experiment_result.to_payload(),
            "generation_id": self.generation_id,
            "landscape_path": str(self.landscape_path),
            "next_generation_proposal_path": str(self.next_generation_proposal_path),
            "rejected_count": self.rejected_count,
            "selected_count": self.selected_count,
            "trial_count": self.trial_count,
        }


@dataclass(frozen=True, slots=True)
class AutonomousResearchResult:
    """Final autonomous campaign artifact index."""

    status: str
    output_root: Path
    generations: tuple[AutonomousResearchGeneration, ...]
    fitness_landscape_path: Path
    fitness_analytics_path: Path
    next_generation_proposal_path: Path
    selected_candidates_path: Path
    rejected_candidates_path: Path
    validation_summary_path: Path
    report_path: Path
    audit_log_path: Path
    artifact_graph_path: Path
    paper_live_launches: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready result payload."""

        return {
            "artifact_graph_path": str(self.artifact_graph_path),
            "audit_log_path": str(self.audit_log_path),
            "fitness_analytics_path": str(self.fitness_analytics_path),
            "fitness_landscape_path": str(self.fitness_landscape_path),
            "generations": [generation.to_payload() for generation in self.generations],
            "next_generation_proposal_path": str(self.next_generation_proposal_path),
            "output_root": str(self.output_root),
            "paper_live_launches": list(self.paper_live_launches),
            "rejected_candidates_path": str(self.rejected_candidates_path),
            "report_path": str(self.report_path),
            "selected_candidates_path": str(self.selected_candidates_path),
            "status": self.status,
            "validation_summary_path": str(self.validation_summary_path),
        }


__all__ = [
    "AutonomousResearchGeneration",
    "AutonomousResearchResult",
    "AutonomousResearchRun",
]
