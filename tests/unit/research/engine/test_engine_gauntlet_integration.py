from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from .test_autonomous_engine_trial_generation import (
    force_clean_reproducibility,
    read_jsonl,
    write_campaign,
    write_data_paths,
)


def test_engine_requires_artifact_backed_gauntlet_before_promotion_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    force_clean_reproducibility(monkeypatch)
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

    # WIRING invariant: the validation gauntlet runs end-to-end and emits an
    # artifact-backed, hash-anchored, audit-linked decision for the trial.
    gauntlet_path = result.output_root / "generation-000" / "validation_gauntlet.json"
    payload = json.loads(gauntlet_path.read_text(encoding="utf-8"))
    assert payload["results"]
    assert payload["results"][0]["audit_record_id"]
    for decision in payload["results"][0]["gate_decisions"]:
        assert decision["evidence"]["artifact_path"]
        assert str(decision["evidence"]["payload_hash"]).startswith("sha256:")

    # HONESTY invariant: a toy fixture cannot clear the promotion bar, so the
    # candidate is honestly rejected (no promotion packet) with a recorded reason
    # rather than silently promoted.
    assert result.status == "rejected"
    selected_rows = read_jsonl(result.selected_candidates_path)
    assert selected_rows == []
    rejected_rows = read_jsonl(result.rejected_candidates_path)
    assert rejected_rows
    assert all(row["reasons"] for row in rejected_rows)
