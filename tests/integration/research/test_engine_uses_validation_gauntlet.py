from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import qts.research.engine.autonomous_research_engine as engine_module
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)

from tests.integration.research._autonomous_engine_plan_helpers import (
    read_jsonl,
    write_campaign,
    write_data_paths,
)


def test_engine_blocks_promotion_when_gauntlet_rejects_all_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_validation(self: Any, parameters: Any) -> dict[str, Any]:
        return {
            "capacity": {
                "estimated_capacity": 100,
                "required_capital": 1000,
                "turnover": 2.0,
            },
            "correlation": {"max_active_correlation": 0.95},
            "cost_stress": {
                "degradation": 0.50,
                "slippage_sensitivity": 0.50,
                "stressed_score": 0.1,
            },
            "deterministic_replay": {"passed": False},
            "failure_windows": [
                {
                    "breached": True,
                    "max_drawdown": 0.50,
                    "name": "stress",
                    "report_only": False,
                }
            ],
            "no_lookahead": {"passed": False},
            "walk_forward": {
                "consistent": False,
                "max_train_test_gap": 0.5,
                "test_windows": [{"accepted": False, "name": "oos"}],
            },
        }

    monkeypatch.setattr(
        engine_module.AutonomousResearchEngine, "_validation_evidence", failing_validation
    )
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

    payload = json.loads(
        (result.output_root / "generation-000" / "validation_gauntlet.json").read_text(
            encoding="utf-8"
        )
    )
    reasons = " ".join(payload["results"][0]["reasons"])
    for expected in (
        "walk_forward",
        "failure_window_veto",
        "cost_stress",
        "correlation",
        "capacity",
        "deterministic_replay",
        "no_lookahead",
    ):
        assert expected in reasons
    assert not (result.output_root / "packets").exists()
    assert read_jsonl(result.rejected_candidates_path)
