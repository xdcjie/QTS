from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.selector import ValidationGauntlet


def test_promotion_grade_gauntlet_requires_validation_artifacts(tmp_path: Path) -> None:
    result = ValidationGauntlet(require_artifacts=True).validate(
        {"candidate_id": "candidate-001", "validation": _inline_validation()}
    )

    assert result.accepted is False
    assert "validation artifacts: artifact refs missing" in result.reasons


def test_promotion_grade_gauntlet_reads_artifact_payloads_and_hashes(
    tmp_path: Path,
) -> None:
    artifacts: dict[str, dict[str, Any]] = {
        "walk_forward_validation": {
            "consistent": True,
            "max_train_test_gap": 0.0,
            "test_windows": [{"accepted": True, "name": "oos"}],
        },
        "failure_window_veto": {
            "failure_windows": [{"breached": False, "max_drawdown": 0.05, "name": "stress"}]
        },
        "cost_stress": {
            "degradation": 0.01,
            "slippage_sensitivity": 0.01,
            "stressed_score": 1.0,
        },
        "correlation_report": {
            "active_portfolio_snapshot": {
                "active_candidate_count": 0,
                "active_portfolio_status": "no_active_candidates",
                "candidate_return_count": 2,
            },
            "max_active_correlation": 0.10,
        },
        "capacity_report": {
            "estimated_capacity": 1000000,
            "required_capital": 100000,
            "turnover": 0.1,
        },
        "deterministic_replay": {"passed": True},
        "no_lookahead": {"passed": True},
    }
    refs = {
        name: _write_validation_artifact(tmp_path / f"{name}.json", name, payload)
        for name, payload in artifacts.items()
    }

    result = ValidationGauntlet(require_artifacts=True).validate(
        {"candidate_id": "candidate-001", "validation": {"artifacts": refs}}
    )

    assert result.accepted is True
    for decision in result.gate_decisions:
        assert decision.evidence["artifact_path"]
        assert str(decision.evidence["payload_hash"]).startswith("sha256:")


def test_promotion_grade_gauntlet_rejects_artifact_hash_mismatch(tmp_path: Path) -> None:
    ref = _write_validation_artifact(
        tmp_path / "walk_forward_validation.json",
        "walk_forward_validation",
        {"consistent": True, "max_train_test_gap": 0.0, "test_windows": []},
    )
    ref["payload_hash"] = "sha256:wrong"

    result = ValidationGauntlet(require_artifacts=True).validate(
        {
            "candidate_id": "candidate-001",
            "validation": {"artifacts": {"walk_forward_validation": ref}},
        }
    )

    assert result.accepted is False
    assert any("artifact ref payload_hash mismatch" in reason for reason in result.reasons)


def _write_validation_artifact(
    path: Path,
    artifact_type: str,
    payload: dict[str, Any],
) -> dict[str, str]:
    payload_hash = stable_json_hash(payload)
    wrapper = {
        "artifact_id": artifact_type,
        "artifact_type": artifact_type,
        "evidence_source": "backtest_pipeline_artifact",
        "payload": payload,
        "payload_hash": payload_hash,
        "source_artifacts": {"backtest_manifest": "sha256:manifest"},
        "trial_id": "candidate-001",
    }
    path.write_text(json.dumps(wrapper, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "payload_hash": payload_hash}


def _inline_validation() -> dict[str, Any]:
    return {
        "walk_forward": {
            "consistent": True,
            "test_windows": [{"accepted": True, "name": "oos"}],
        },
        "failure_windows": [{"breached": False, "max_drawdown": 0.05, "name": "stress"}],
        "cost_stress": {"degradation": 0.01, "slippage_sensitivity": 0.01},
        "correlation": {"max_active_correlation": 0.10},
        "capacity": {"estimated_capacity": 1000000, "required_capital": 100000},
        "deterministic_replay": {"passed": True},
        "no_lookahead": {"passed": True},
    }
