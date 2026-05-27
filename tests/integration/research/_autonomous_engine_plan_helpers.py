from __future__ import annotations

from pathlib import Path
from typing import Any

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchResult,
    AutonomousResearchRun,
)

from tests.unit.research.engine.test_autonomous_engine_trial_generation import (
    read_jsonl,
    write_campaign,
    write_data_paths,
)


def run_engine(
    tmp_path: Path,
    **campaign_kwargs: Any,
) -> tuple[Path, AutonomousResearchResult]:
    campaign_path = write_campaign(tmp_path, **campaign_kwargs)
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )
    return campaign_path, AutonomousResearchEngine(repo_root=Path.cwd()).run(run)


__all__ = ["read_jsonl", "run_engine", "write_campaign", "write_data_paths"]
