from __future__ import annotations

import json
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from .test_autonomous_engine_trial_generation import write_campaign, write_data_paths


def test_engine_creates_next_generation_proposal_from_fitness_analytics(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum", "breakout"),
        max_trials_per_generation=4,
        max_total_trials=4,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    payload = json.loads(result.next_generation_proposal_path.read_text(encoding="utf-8"))
    assert payload["proposal_hash"].startswith("sha256:")
    assert payload["previous_generation_id"] == "generation-000"
    assert payload["next_generation_id"] == "generation-001"
    assert payload["trial_budget"] <= payload["max_trial_budget"]
    assert payload["mutations"]
    assert all(mutation["reason"] for mutation in payload["mutations"])
    assert all(mutation["evidence_refs"] for mutation in payload["mutations"])
