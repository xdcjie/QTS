from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import qts.research.orchestrator.experiment_runner as experiment_runner_module
from qts.core.hashing import stable_json_hash
from qts.research.engine.autonomous_research_engine import (
    AutonomousResearchEngine,
    AutonomousResearchRun,
)
from qts.research.reproducibility import ReproducibilitySnapshotV2

from tests.integration.research._autonomous_engine_plan_helpers import (
    read_jsonl,
    write_campaign,
    write_data_paths,
)


def test_engine_blocks_promotion_when_gauntlet_rejects_all_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_write_validation_artifacts = (
        experiment_runner_module.ResearchExperimentRunner._write_validation_artifacts
    )
    original_git_output = experiment_runner_module.ResearchExperimentRunner._git_output
    original_repro_git_output = ReproducibilitySnapshotV2._git_output

    def failing_validation_artifacts(
        self: Any,
        *args: Any,
        **kwargs: Any,
    ) -> dict[str, Path]:
        paths = original_write_validation_artifacts(self, *args, **kwargs)
        failing_payloads: dict[str, dict[str, Any]] = {
            "capacity_report": {
                "estimated_capacity": 100,
                "required_capital": 1000,
                "turnover": 2.0,
            },
            "correlation_report": {"max_active_correlation": 0.95},
            "cost_stress": {
                "degradation": 0.50,
                "slippage_sensitivity": 0.50,
                "stressed_score": 0.1,
            },
            "deterministic_replay": {"passed": False},
            "failure_window_veto": {
                "failure_windows": [
                    {
                        "breached": True,
                        "max_drawdown": 0.50,
                        "name": "stress",
                        "report_only": False,
                    }
                ]
            },
            "no_lookahead": {"passed": False},
            "walk_forward_validation": {
                "consistent": False,
                "max_train_test_gap": 0.5,
                "test_windows": [{"accepted": False, "name": "oos"}],
            },
        }
        for artifact_name, artifact_path in paths.items():
            wrapper = json.loads(artifact_path.read_text(encoding="utf-8"))
            payload = failing_payloads[artifact_name]
            wrapper["payload"] = payload
            wrapper["payload_hash"] = stable_json_hash(payload)
            artifact_path.write_text(
                json.dumps(wrapper, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        return paths

    monkeypatch.setattr(
        experiment_runner_module.ResearchExperimentRunner,
        "_write_validation_artifacts",
        failing_validation_artifacts,
    )

    def clean_git_status(self: Any, args: tuple[str, ...]) -> str:
        if args == ("status", "--short"):
            return ""
        return original_git_output(self, args)

    monkeypatch.setattr(
        experiment_runner_module.ResearchExperimentRunner,
        "_git_output",
        clean_git_status,
    )

    def clean_repro_git_status(repo_root: Path, args: tuple[str, ...]) -> str:
        if args == ("status", "--short"):
            return ""
        return original_repro_git_output(repo_root, args)

    monkeypatch.setattr(ReproducibilitySnapshotV2, "_git_output", clean_repro_git_status)
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
