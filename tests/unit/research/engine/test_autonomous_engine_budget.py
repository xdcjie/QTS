from __future__ import annotations

import json
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from .test_autonomous_engine_trial_generation import read_jsonl, write_campaign, write_data_paths


def test_engine_uses_trial_budget_manager_before_execution(tmp_path: Path) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
        max_family_trials=2,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    assert result.generations[0].trial_count == 3
    landscape_rows = read_jsonl(result.fitness_landscape_path)
    assert len(landscape_rows) == 3
    assert any(
        row["lifecycle_status"] == "budget_rejected" and row["rejection_stage"] == "trial_budget"
        for row in landscape_rows
    )
    ledger_path = result.output_root / "trial_budget_ledger.jsonl"
    records = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    assert [record["payload"]["accepted"] for record in records] == [True, True, False]
    assert records[-1]["payload"]["decision_reason"] == (
        "strategy family trial budget exceeded: 2/2 accepted"
    )
