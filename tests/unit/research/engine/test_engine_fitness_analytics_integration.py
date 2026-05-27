from __future__ import annotations

import json
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from .test_autonomous_engine_trial_generation import write_campaign, write_data_paths


def test_engine_writes_fitness_analytics_from_landscape_store(tmp_path: Path) -> None:
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

    payload = json.loads(result.fitness_analytics_path.read_text(encoding="utf-8"))
    assert payload["analytics_hash"].startswith("sha256:")
    assert payload["best_family"]["strategy_family"] in {"momentum", "breakout"}
    assert payload["family_summaries"]
    assert payload["parameter_regions"]
    assert "rejection_clusters" in payload
