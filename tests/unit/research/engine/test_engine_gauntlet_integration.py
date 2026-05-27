from __future__ import annotations

import json
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from .test_autonomous_engine_trial_generation import read_jsonl, write_campaign, write_data_paths


def test_engine_requires_validation_gauntlet_before_promotion_packet(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=1,
        max_total_trials=1,
        active_correlation=0.60,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    gauntlet_path = result.output_root / "generation-000" / "validation_gauntlet.json"
    payload = json.loads(gauntlet_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["accepted"] is False
    assert any("correlation" in reason for reason in payload["results"][0]["reasons"])
    assert not (result.output_root / "packets").exists()
    rejected_rows = read_jsonl(result.rejected_candidates_path)
    assert any("correlation" in " ".join(row["reasons"]) for row in rejected_rows)
