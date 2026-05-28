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


def test_engine_writes_candidate_selector_artifacts_and_selector_rejections(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    force_clean_reproducibility(monkeypatch)
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
    )
    run = AutonomousResearchRun.from_yaml(
        campaign_path,
        data_paths=write_data_paths(tmp_path),
        output_root=tmp_path / "run",
    )

    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(run)

    selection_path = result.output_root / "generation-000" / "selection" / "selection_result.json"
    payload = json.loads(selection_path.read_text(encoding="utf-8"))
    assert payload["selection_hash"].startswith("sha256:")
    assert payload["selected_count"] == 1
    assert payload["rejected_count"] >= 1
    rejected_rows = read_jsonl(result.rejected_candidates_path)
    assert any(
        "selection_budget" in " ".join(str(reason) for reason in row["reasons"])
        for row in rejected_rows
    )
