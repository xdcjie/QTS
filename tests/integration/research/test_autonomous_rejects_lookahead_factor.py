"""Integration test: autonomous research rejects lookahead factors.

Validates that the full gauntlet pipeline rejects candidates with
lookahead factors, and that string-only scan is insufficient for
promotion-grade validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.selector import (
    CorrelationGate,
    CostStressGate,
    FailureWindowVetoGate,
    NoLookaheadGate,
    ValidationGauntlet,
    WalkForwardGate,
)


def _passing_candidate_with_timing_validation() -> dict[str, Any]:
    """Return a candidate that passes all gates including timing-protocol no_lookahead."""

    return {
        "candidate_id": "candidate-ok",
        "validation": {
            "walk_forward": {
                "consistent": True,
                "test_windows": (
                    {"name": "split-001", "accepted": True, "score": 1.10},
                    {"name": "split-002", "accepted": True, "score": 0.90},
                ),
                "max_train_test_gap": 0.30,
            },
            "failure_windows": (
                {"name": "crisis", "max_drawdown": 0.12},
                {"name": "rebound", "max_drawdown": 0.08, "report_only": True},
            ),
            "cost_stress": {
                "degradation": 0.12,
                "slippage_sensitivity": 0.05,
                "stressed_score": 0.84,
            },
            "correlation": {
                "active_portfolio_snapshot": {
                    "active_candidate_count": 1,
                    "active_portfolio_status": "computed",
                    "candidate_return_count": 2,
                },
                "max_active_correlation": 0.42,
            },
            "capacity": {
                "estimated_capacity": 1_000_000,
                "required_capital": 500_000,
                "turnover": 1.8,
            },
            "deterministic_replay": {"passed": True},
            "no_lookahead": {
                "passed": True,
                "string_scan_only": False,
                "string_scan_violations": [],
                "violations": [],
                "timing_validation": {
                    "passed": True,
                    "checked_features": ["momentum_10"],
                    "label_horizon": 5,
                    "max_feature_timestamp": "2025-12-01",
                    "min_label_cutoff": "2026-06-01",
                    "violations": [],
                    "window_overlaps": [],
                },
            },
        },
    }


def _string_only_lookahead_candidate() -> dict[str, Any]:
    """Return a candidate that passes the old string-only scan but has no timing proof."""

    return {
        "candidate_id": "candidate-string-only",
        "validation": {
            "walk_forward": {
                "consistent": True,
                "test_windows": ({"name": "split-001", "accepted": True, "score": 1.10},),
                "max_train_test_gap": 0.30,
            },
            "failure_windows": ({"name": "crisis", "max_drawdown": 0.12},),
            "cost_stress": {
                "degradation": 0.12,
                "slippage_sensitivity": 0.05,
            },
            "correlation": {
                "active_portfolio_snapshot": {
                    "active_candidate_count": 0,
                    "active_portfolio_status": "no_active_candidates",
                    "candidate_return_count": 2,
                },
                "max_active_correlation": 0.10,
            },
            "capacity": {
                "estimated_capacity": 1_000_000,
                "required_capital": 500_000,
            },
            "deterministic_replay": {"passed": True},
            "no_lookahead": {
                "passed": True,
                "forbidden_terms": ["future_return"],
                "violations": [],
                # Key missing: no timing_validation, only string scan
            },
        },
    }


def _lookahead_factor_candidate() -> dict[str, Any]:
    """Return a candidate with a forward_return feature detected by timing validation."""

    return {
        "candidate_id": "candidate-lookahead",
        "validation": {
            "walk_forward": {
                "consistent": True,
                "test_windows": ({"name": "split-001", "accepted": True, "score": 1.10},),
                "max_train_test_gap": 0.30,
            },
            "failure_windows": ({"name": "crisis", "max_drawdown": 0.12},),
            "cost_stress": {
                "degradation": 0.12,
                "slippage_sensitivity": 0.05,
            },
            "correlation": {
                "active_portfolio_snapshot": {
                    "active_candidate_count": 0,
                    "active_portfolio_status": "no_active_candidates",
                    "candidate_return_count": 2,
                },
                "max_active_correlation": 0.10,
            },
            "capacity": {
                "estimated_capacity": 1_000_000,
                "required_capital": 500_000,
            },
            "deterministic_replay": {"passed": True},
            "no_lookahead": {
                "passed": False,
                "string_scan_only": False,
                "string_scan_violations": [],
                "violations": [
                    {
                        "code": "forward_return_feature_detected",
                        "message": "feature 'future_return_5' is a forward/lookahead feature",
                        "feature_name": "future_return_5",
                    }
                ],
                "timing_validation": {
                    "passed": False,
                    "checked_features": ["future_return_5"],
                    "label_horizon": 5,
                    "max_feature_timestamp": "2025-12-01",
                    "min_label_cutoff": "2026-06-01",
                    "violations": [
                        {
                            "code": "forward_return_feature_detected",
                            "message": "feature 'future_return_5' is a forward/lookahead feature",
                        }
                    ],
                    "window_overlaps": [],
                },
            },
        },
    }


class TestAutonomousRejectsLookaheadFactor:
    """Integration test: gauntlet rejects candidates with lookahead factors."""

    def test_candidate_with_timing_validation_passes(self) -> None:
        """Candidate with valid timing-protocol proof passes the gauntlet."""
        gauntlet = ValidationGauntlet(
            walk_forward_gate=WalkForwardGate(min_test_windows=1),
            failure_window_gate=FailureWindowVetoGate(max_drawdown=0.25),
            cost_stress_gate=CostStressGate(max_degradation=0.30, max_slippage_sensitivity=0.20),
            correlation_gate=CorrelationGate(max_active_correlation=0.80),
        )
        result = gauntlet.validate(_passing_candidate_with_timing_validation())
        assert result.accepted is True
        assert result.no_lookahead_status == "passed"

    def test_candidate_with_lookahead_factor_rejected(self) -> None:
        """Candidate with forward_return feature is rejected by the gauntlet."""
        gauntlet = ValidationGauntlet(
            walk_forward_gate=WalkForwardGate(min_test_windows=1),
            failure_window_gate=FailureWindowVetoGate(max_drawdown=0.25),
            cost_stress_gate=CostStressGate(max_degradation=0.30, max_slippage_sensitivity=0.20),
            correlation_gate=CorrelationGate(max_active_correlation=0.80),
        )
        result = gauntlet.validate(_lookahead_factor_candidate())
        assert result.accepted is False
        assert result.no_lookahead_status == "failed"
        assert any("forward_return_feature_detected" in reason for reason in result.reasons)

    def test_string_only_scan_insufficient_for_promotion(self) -> None:
        """Candidate that only has string-scan no_lookahead is rejected."""
        gauntlet = ValidationGauntlet(
            walk_forward_gate=WalkForwardGate(min_test_windows=1),
            failure_window_gate=FailureWindowVetoGate(max_drawdown=0.25),
            cost_stress_gate=CostStressGate(max_degradation=0.30, max_slippage_sensitivity=0.20),
            correlation_gate=CorrelationGate(max_active_correlation=0.80),
        )
        result = gauntlet.validate(_string_only_lookahead_candidate())
        assert result.accepted is False
        assert result.no_lookahead_status == "failed"
        # Must reject because timing_validation is missing
        assert any("timing_validation" in reason for reason in result.reasons)

    def test_no_lookahead_gate_standalone_rejects_lookahead(self) -> None:
        """NoLookaheadGate directly rejects a candidate with lookahead features."""
        gate = NoLookaheadGate()
        decision = gate.evaluate(_lookahead_factor_candidate())
        assert decision.accepted is False
        assert any("forward_return" in reason for reason in decision.reasons)

    def test_no_lookahead_gate_standalone_rejects_string_only(self) -> None:
        """NoLookaheadGate directly rejects string-only evidence."""
        gate = NoLookaheadGate()
        decision = gate.evaluate(_string_only_lookahead_candidate())
        assert decision.accepted is False
        assert any("timing_validation" in reason for reason in decision.reasons)

    def test_gauntlet_no_lookahead_gate_in_gate_decisions(self) -> None:
        """NoLookaheadGate is included in gate_decisions for the gauntlet."""
        gauntlet = ValidationGauntlet()
        result = gauntlet.validate(_passing_candidate_with_timing_validation())
        gate_names = [d.gate_name for d in result.gate_decisions]
        assert "no_lookahead" in gate_names


class TestPromotionGradeRejectsLookahead:
    """Promotion-grade gauntlet (require_artifacts=True) rejects lookahead factors."""

    def test_promotion_grade_rejects_lookahead_factor(self, tmp_path: Path) -> None:
        """Promotion-grade validation with artifact loading rejects lookahead."""
        artifacts = _write_all_validation_artifacts(tmp_path, lookahead=True)
        refs = {
            name: {"path": str(path), "payload_hash": hash_val}
            for name, (path, hash_val) in artifacts.items()
        }
        candidate = {
            "candidate_id": "candidate-lookahead-promo",
            "validation": {
                "artifacts": refs,
                **_lookahead_factor_candidate()["validation"],
            },
        }
        gauntlet = ValidationGauntlet(require_artifacts=True)
        result = gauntlet.validate(candidate)
        assert result.accepted is False

    def test_promotion_grade_accepts_timing_validated(self, tmp_path: Path) -> None:
        """Promotion-grade validation with timing proof accepts clean candidate."""
        artifacts = _write_all_validation_artifacts(tmp_path, lookahead=False)
        refs = {
            name: {"path": str(path), "payload_hash": hash_val}
            for name, (path, hash_val) in artifacts.items()
        }
        candidate = {
            "candidate_id": "candidate-clean-promo",
            "validation": {
                "artifacts": refs,
                **_passing_candidate_with_timing_validation()["validation"],
            },
        }
        gauntlet = ValidationGauntlet(require_artifacts=True)
        result = gauntlet.validate(candidate)
        assert result.accepted is True


def _write_all_validation_artifacts(
    tmp_path: Path,
    *,
    lookahead: bool,
) -> dict[str, tuple[Path, str]]:
    """Write validation artifact files and return {name: (path, payload_hash)}."""

    no_lookahead_payload: dict[str, Any]
    if lookahead:
        no_lookahead_payload = _lookahead_factor_candidate()["validation"]["no_lookahead"]
    else:
        no_lookahead_payload = _passing_candidate_with_timing_validation()["validation"][
            "no_lookahead"
        ]

    artifact_payloads: dict[str, dict[str, Any]] = {
        "walk_forward_validation": {
            "consistent": True,
            "max_train_test_gap": 0.3,
            "test_windows": [{"accepted": True, "name": "oos"}],
        },
        "failure_window_veto": {
            "failure_windows": [{"breached": False, "max_drawdown": 0.12, "name": "crisis"}]
        },
        "cost_stress": {
            "degradation": 0.12,
            "slippage_sensitivity": 0.05,
            "stressed_score": 0.84,
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
            "estimated_capacity": 1_000_000,
            "required_capital": 500_000,
            "turnover": 1.8,
        },
        "deterministic_replay": {"passed": True},
        "no_lookahead": no_lookahead_payload,
    }
    result: dict[str, tuple[Path, str]] = {}
    for artifact_name, payload in artifact_payloads.items():
        path = tmp_path / f"{artifact_name}.json"
        payload_hash = stable_json_hash(payload)
        wrapper = {
            "artifact_id": artifact_name,
            "artifact_type": artifact_name,
            "evidence_source": "backtest_pipeline_artifact",
            "payload": payload,
            "payload_hash": payload_hash,
            "source_artifacts": {"backtest_manifest": "sha256:manifest"},
            "trial_id": "test-trial",
        }
        path.write_text(json.dumps(wrapper, sort_keys=True), encoding="utf-8")
        result[artifact_name] = (path, payload_hash)
    return result
