from __future__ import annotations

import json
from pathlib import Path

from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from .test_autonomous_engine_trial_generation import read_jsonl, write_campaign, write_data_paths


def test_engine_requires_artifact_backed_gauntlet_before_promotion_packet(
    tmp_path: Path,
) -> None:
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=1,
        max_total_trials=1,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    gauntlet_path = result.output_root / "generation-000" / "validation_gauntlet.json"
    payload = json.loads(gauntlet_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["accepted"] is True
    assert payload["results"][0]["audit_record_id"]
    for decision in payload["results"][0]["gate_decisions"]:
        assert decision["evidence"]["artifact_path"]
        assert str(decision["evidence"]["payload_hash"]).startswith("sha256:")

    selected_rows = read_jsonl(result.selected_candidates_path)
    assert selected_rows
    assert (
        selected_rows[0]["validation_audit_record_id"] == payload["results"][0]["audit_record_id"]
    )
    assert Path(selected_rows[0]["promotion_packet_path"]).exists()
