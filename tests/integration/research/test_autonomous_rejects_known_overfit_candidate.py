"""Integration test: autonomous research rejects known-overfit candidates (DR-001).

This test verifies that when a promotion packet contains metrics with
train_sharpe == oos_sharpe from the same source manifest, the autonomous
promotion pipeline correctly rejects the candidate.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from qts.core.hashing import stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.orchestrator.validation_artifact_reader import (
    ResearchMetricsFromValidationArtifacts,
    ValidationArtifactReader,
)
from qts.research.promotion_packet import PromotionPacketV2


def test_promotion_rejects_known_overfit_candidate_same_source_sharpe(
    tmp_path: Path,
) -> None:
    """A candidate with train_sharpe == oos_sharpe from same manifest is rejected."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _metrics_with_same_source_sharpe()

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert any("known overfit candidate" in r for r in result.reasons)


def test_promotion_rejects_hollow_verdict_metrics(tmp_path: Path) -> None:
    """A candidate with the old hardcoded sentinel metrics is rejected."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _hollow_verdict_metrics()

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert any("hollow verdict sentinel" in r for r in result.reasons)


def test_promotion_rejects_missing_validation_artifact_fields(tmp_path: Path) -> None:
    """A candidate with None validation fields (no artifacts produced) is rejected."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _metrics_with_missing_validation_fields()

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert any("deterministic_replay_passed is missing" in r for r in result.reasons)
    assert any("no_lookahead_passed is missing" in r for r in result.reasons)


def test_validation_derivation_rejects_same_source_overfit(tmp_path: Path) -> None:
    """ResearchMetricsFromValidationArtifacts flags same-source overfit."""
    _write_validation_artifact(
        tmp_path,
        "walk_forward_validation",
        {
            "consistent": True,
            "test_windows": [
                {
                    "accepted": True,
                    "train_score": 2.0,
                    "score": 2.0,
                    "train_manifest_hash": "sha256:identical-manifest",
                    "manifest_hash": "sha256:identical-manifest",
                }
            ],
        },
    )
    _write_validation_artifact(tmp_path, "deterministic_replay", {"passed": True})
    _write_validation_artifact(tmp_path, "no_lookahead", {"passed": True})
    _write_validation_artifact(tmp_path, "cost_stress", {"degradation": 0.05})

    reader = ValidationArtifactReader(tmp_path)
    derivation = ResearchMetricsFromValidationArtifacts().derive(
        reader, _workflow_summary()
    )

    assert derivation.is_overfit_candidate is True
    assert derivation.promotion_eligible is False


def test_validation_derivation_accepts_genuine_candidate(tmp_path: Path) -> None:
    """A candidate with different train/test sharpe from separate manifests is eligible."""
    _write_validation_artifact(
        tmp_path,
        "walk_forward_validation",
        {
            "consistent": True,
            "test_windows": [
                {
                    "accepted": True,
                    "train_score": 1.8,
                    "score": 1.2,
                    "train_manifest_hash": "sha256:train-manifest-unique",
                    "manifest_hash": "sha256:test-manifest-unique",
                }
            ],
        },
    )
    _write_validation_artifact(tmp_path, "deterministic_replay", {"passed": True})
    _write_validation_artifact(tmp_path, "no_lookahead", {"passed": True})
    _write_validation_artifact(tmp_path, "cost_stress", {"degradation": 0.05})

    reader = ValidationArtifactReader(tmp_path)
    derivation = ResearchMetricsFromValidationArtifacts().derive(
        reader,
        {
            "periods": [
                {
                    "start": "2021-01-01T00:00:00+00:00",
                    "end": "2022-06-01T00:00:00+00:00",
                    "name": "oos",
                    "role": "oos",
                }
            ],
        },
    )

    assert derivation.is_overfit_candidate is False
    assert derivation.deterministic_replay_passed is True
    assert derivation.no_lookahead_passed is True
    assert derivation.walk_forward_consistency == pytest.approx(1.2 / 1.8)
    assert derivation.parameter_sensitivity == pytest.approx(0.95)
    assert derivation.oos_months is not None
    assert derivation.oos_months >= 6.0
    assert derivation.promotion_eligible is True


def test_oos_months_computed_from_declared_windows(tmp_path: Path) -> None:
    """oos_months must be computed from declared OOS windows, not hardcoded."""
    _write_validation_artifact(
        tmp_path,
        "walk_forward_validation",
        {
            "consistent": True,
            "test_windows": [
                {
                    "accepted": True,
                    "train_score": 1.5,
                    "score": 1.0,
                    "train_manifest_hash": "sha256:train",
                    "manifest_hash": "sha256:test",
                }
            ],
        },
    )
    _write_validation_artifact(tmp_path, "deterministic_replay", {"passed": True})
    _write_validation_artifact(tmp_path, "no_lookahead", {"passed": True})
    _write_validation_artifact(tmp_path, "cost_stress", {"degradation": 0.1})

    reader = ValidationArtifactReader(tmp_path)
    # 18-month OOS window
    summary = {
        "periods": [
            {
                "start": "2021-01-01T00:00:00+00:00",
                "end": "2022-07-01T00:00:00+00:00",
                "name": "oos-window",
                "role": "oos",
            }
        ],
    }
    derivation = ResearchMetricsFromValidationArtifacts().derive(reader, summary)

    assert derivation.oos_months is not None
    assert derivation.oos_months != 12.0  # Not hardcoded
    assert derivation.oos_months > 12.0  # 18 months > 12


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_validation_artifact(
    artifact_dir: Path,
    artifact_name: str,
    payload: dict[str, Any],
) -> None:
    validation_dir = artifact_dir / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    wrapper = {
        "artifact_id": artifact_name,
        "artifact_type": artifact_name,
        "evidence_source": "backtest_pipeline_artifact",
        "payload": payload,
        "payload_hash": stable_json_hash(payload),
    }
    (validation_dir / f"{artifact_name}.json").write_text(
        json.dumps(wrapper, sort_keys=True), encoding="utf-8"
    )


def _workflow_summary() -> dict[str, Any]:
    return {
        "periods": [
            {
                "start": "2021-01-01T00:00:00+00:00",
                "end": "2022-01-01T00:00:00+00:00",
                "name": "selection",
                "role": "selection",
            }
        ]
    }


def _metrics_with_same_source_sharpe() -> dict[str, dict[str, object]]:
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "performance": {
            "max_drawdown": 0.2,
            "oos_manifest_hash": "sha256:same-source",
            "oos_sharpe": 1.5,
            "total_return": 0.15,
            "train_manifest_hash": "sha256:same-source",
            "train_sharpe": 1.5,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {
            "profit_factor": 1.4,
            "sharpe": 1.1,
        },
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {
            "parameter_sensitivity": 0.8,
            "walk_forward_consistency": 0.75,
        },
        "trading": {
            "oos_months": 6.0,
            "oos_trade_count": 40,
        },
    }


def _hollow_verdict_metrics() -> dict[str, dict[str, object]]:
    """The old hardcoded sentinel metrics pattern."""
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "performance": {
            "max_drawdown": 0.2,
            "oos_sharpe": 1.1,
            "total_return": 0.15,
            "train_sharpe": 1.1,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {
            "profit_factor": 1.4,
            "sharpe": 1.1,
        },
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {
            "parameter_sensitivity": 1.0,
            "walk_forward_consistency": 1.0,
        },
        "trading": {
            "oos_months": 12.0,
            "oos_trade_count": 40,
        },
    }


def _metrics_with_missing_validation_fields() -> dict[str, dict[str, object]]:
    """Metrics with None fields (no validation artifacts produced)."""
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "performance": {
            "max_drawdown": 0.2,
            "oos_sharpe": None,
            "total_return": 0.15,
            "train_sharpe": None,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {
            "profit_factor": 1.4,
            "sharpe": 1.1,
        },
        "research": {
            "deterministic_replay_passed": None,
            "no_lookahead_passed": None,
            "promotion_eligible": False,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {
            "parameter_sensitivity": None,
            "walk_forward_consistency": None,
        },
        "trading": {
            "oos_months": None,
            "oos_trade_count": 40,
        },
    }


def _packet_payload(
    bundle_id: str,
    *,
    target_mode: str = "paper_simulated",
    metrics_payload: dict[str, dict[str, object]] | None = None,
) -> dict[str, Any]:
    metrics = metrics_payload or _metrics_with_same_source_sharpe()
    return {
        "schema_version": 2,
        "promotion_candidate_id": "pc-overfit",
        "target_mode": target_mode,
        "strategy_id": "overfit-test",
        "source_module": "strategies.research.overfit",
        "target_module": "strategies.production.overfit",
        "idea_id": "idea-overfit",
        "evidence_bundle_id": bundle_id,
        "metrics": {
            "metrics_schema_id": "schema_v2",
            "payload_hash": stable_json_hash(metrics),
            "payload": metrics,
        },
        "data_quality": {
            "artifact_id": "dq-dataset-001",
            "payload_hash": stable_json_hash(_data_quality_payload()),
            "payload": _data_quality_payload(),
        },
        "reproducibility": {
            "snapshot_id": "repro-001",
            "payload_hash": stable_json_hash(_repro_payload()),
            "payload": _repro_payload(),
        },
        "runtime": {
            "account_id": "paper-account",
            "risk_profile_id": "risk-paper",
            "capital_limit": 100000,
            "runtime_mode": target_mode,
            "kill_switch_profile": "paper-kill-switch",
        },
        "operations": {
            "rollback_plan": "disable promoted strategy module",
            "monitoring_plan": "watch fills",
            "alert_policy": "page operator",
        },
        "review": {},
    }


def _data_quality_payload() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "dataset_id": "dataset-001",
        "accepted": True,
        "checked_paths": ["datasets/dataset-001/bars.csv"],
        "issues": [],
        "duplicate_timestamps": 0,
        "missing_bars": 0,
        "session_alignment": True,
        "stale_prices": 0,
        "halted_sessions": 0,
        "label_visibility": True,
    }


def _repro_payload() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "git_sha": "abc123",
        "git_dirty": False,
        "python_version": "3.13.0",
        "platform": "macOS",
        "manifest_hash": "sha256:manifest",
        "dependency_hashes": {"uv.lock": "sha256:deps"},
        "config_hashes": {"research.yaml": "sha256:config"},
        "data_hashes": {"dataset.parquet": "sha256:data"},
        "command_argv": ["--config", "research.yaml"],
        "random_seeds": {"python": 7},
        "calendar_version": "XNYS-2026a",
        "container_digest": None,
    }


def _write_verifiable_bundle(
    tmp_path: Path,
) -> tuple[EvidenceRegistry, str]:
    import hashlib
    from datetime import UTC, datetime

    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {artifact_path.name: artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: str(artifact_path)},
                "metrics": {"sharpe": "1.2"},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    report_path = tmp_path / "workflow-report.md"
    report_path.write_text("# Research Workflow Report\n", encoding="utf-8")
    summary_path = tmp_path / "workflow-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "run_context": {
                    "dataset_ids": ["fixture:GC:15m"],
                    "git_commit": "abc123",
                    "git_dirty": False,
                    "research_config_hash": "sha256:research",
                    "workflow_config_hash": "sha256:workflow",
                },
                "periods": [
                    {
                        "end": "2022-01-01T00:00:00+00:00",
                        "name": "selection",
                        "role": "selection",
                        "start": "2020-01-01T00:00:00+00:00",
                    }
                ],
                "status": "completed",
                "steps": [
                    {
                        "id": "tearsheet",
                        "kind": "factor_tearsheet",
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "research_report",
                        "outputs": {"report_path": str(report_path)},
                        "status": "passed",
                    },
                ],
                "workflow_id": "promotion-flow",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    idea = IdeaSpec(
        idea_id="idea-overfit",
        title="Overfit test strategy",
        hypothesis="Test overfit detection.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(
        summary_path,
        idea=idea,
        strategy_id="overfit-test",
    )
    return registry, bundle.evidence_bundle_id
