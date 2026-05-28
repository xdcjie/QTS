from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import qts.research.engine.autonomous_research_engine as engine_module
from qts.research.audit_log import ResearchAuditLog
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from scripts import run_research
from tests.integration.research._autonomous_engine_plan_helpers import (
    read_jsonl,
    run_engine,
    write_campaign,
    write_data_paths,
)


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


def test_engine_selector_applies_metrics_schema_before_promotion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = engine_module.AutonomousResearchEngine._metrics_from_trial_result

    def metrics_without_promotion_flag(
        self: engine_module.AutonomousResearchEngine,
        result: Any,
    ) -> dict[str, Any]:
        payload = dict(original(self, result))
        research = dict(payload["research"])
        research.pop("promotion_eligible")
        payload["research"] = research
        return payload

    monkeypatch.setattr(
        engine_module.AutonomousResearchEngine,
        "_metrics_from_trial_result",
        metrics_without_promotion_flag,
    )
    campaign_path = write_campaign(
        tmp_path,
        families=("momentum",),
        max_trials_per_generation=1,
        max_total_trials=1,
    )
    result = AutonomousResearchEngine(repo_root=Path.cwd()).run(
        AutonomousResearchRun.from_yaml(
            campaign_path,
            data_paths=write_data_paths(tmp_path),
            output_root=tmp_path / "run",
        )
    )

    rejected_rows = read_jsonl(result.rejected_candidates_path)
    assert result.status == "rejected"
    assert not (result.output_root / "packets").exists()
    assert any(
        "metrics_schema: research.promotion_eligible missing for promotion" in reason
        for row in rejected_rows
        for reason in row["reasons"]
    )
