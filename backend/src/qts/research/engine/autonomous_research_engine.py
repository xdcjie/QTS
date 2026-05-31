"""Bounded autonomous research loop for research-only campaign artifacts."""

from __future__ import annotations

from pathlib import Path

from qts.research.engine import autonomous_engine_orchestration
from qts.research.engine.autonomous_campaign_support import AutonomousResearchCampaignSupport
from qts.research.engine.autonomous_research_types import (
    AutonomousResearchGeneration,
    AutonomousResearchResult,
    AutonomousResearchRun,
)


class AutonomousResearchEngine:
    """Run bounded research-only generations and produce promotion evidence."""

    def __init__(self, *, repo_root: Path) -> None:
        self._support = AutonomousResearchCampaignSupport(repo_root=repo_root)

    def run(self, run: AutonomousResearchRun) -> AutonomousResearchResult:
        """Run a bounded autonomous campaign without launching runtime modes."""
        return autonomous_engine_orchestration.run(self._support, run)


__all__ = [
    "AutonomousResearchEngine",
    "AutonomousResearchGeneration",
    "AutonomousResearchResult",
    "AutonomousResearchRun",
]
