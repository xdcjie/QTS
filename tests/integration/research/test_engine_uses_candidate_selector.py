from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from qts.research.audit_log import ResearchAuditLog

from scripts import run_research
from tests.integration.research._autonomous_engine_plan_helpers import read_jsonl, run_engine


def test_engine_writes_selector_artifacts_audit_and_replay(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    campaign_path, result = run_engine(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=3,
        max_total_trials=3,
    )
    selection_dir = result.output_root / "generation-000" / "selection"

    assert (selection_dir / "selection_result.json").exists()
    assert (selection_dir / "selected_candidates.jsonl").exists()
    assert (selection_dir / "rejected_candidates.jsonl").exists()
    assert read_jsonl(selection_dir / "candidate_results.jsonl")
    assert any(
        record.record_type == "selection_completed"
        for record in ResearchAuditLog(result.audit_log_path).list()
    )

    exit_code = run_research.main(
        [
            "selector",
            "replay",
            "--selection-result",
            str(selection_dir / "selection_result.json"),
            "--campaign",
            str(campaign_path),
            "--candidate-results",
            str(selection_dir / "candidate_results.jsonl"),
        ]
    )

    assert exit_code == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["accepted"] is True
