"""Unit tests for research metrics value honesty (DR-001).

Verifies that validation-gated metrics fields are derived from real
validation artifacts rather than hardcoded defaults, and that hollow
verdict patterns are rejected.
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
    ResearchMetricsDerivation,
    ResearchMetricsFromValidationArtifacts,
    SharpeSources,
    ValidationArtifactReader,
)
from qts.research.promotion_packet import PromotionPacketV2

# ---------------------------------------------------------------------------
# ValidationArtifactReader tests
# ---------------------------------------------------------------------------


class TestValidationArtifactReader:
    def test_returns_none_for_missing_artifact(self, tmp_path: Path) -> None:
        reader = ValidationArtifactReader(tmp_path)
        assert reader.read("deterministic_replay") is None

    def test_reads_artifact_payload(self, tmp_path: Path) -> None:
        validation_dir = tmp_path / "validation"
        validation_dir.mkdir(parents=True)
        payload = {"passed": True, "manifest_hash": "sha256:abc"}
        wrapper = {
            "artifact_id": "deterministic_replay",
            "artifact_type": "deterministic_replay",
            "payload": payload,
            "payload_hash": stable_json_hash(payload),
        }
        (validation_dir / "deterministic_replay.json").write_text(
            json.dumps(wrapper, sort_keys=True), encoding="utf-8"
        )

        reader = ValidationArtifactReader(tmp_path)
        result = reader.read("deterministic_replay")

        assert result is not None
        assert result.artifact_name == "deterministic_replay"
        assert result.payload.get("passed") is True

    def test_returns_none_for_malformed_json(self, tmp_path: Path) -> None:
        validation_dir = tmp_path / "validation"
        validation_dir.mkdir(parents=True)
        (validation_dir / "deterministic_replay.json").write_text("not json", encoding="utf-8")

        reader = ValidationArtifactReader(tmp_path)
        assert reader.read("deterministic_replay") is None

    def test_returns_none_when_payload_is_not_mapping(self, tmp_path: Path) -> None:
        validation_dir = tmp_path / "validation"
        validation_dir.mkdir(parents=True)
        wrapper = {"payload": [1, 2, 3]}
        (validation_dir / "deterministic_replay.json").write_text(
            json.dumps(wrapper, sort_keys=True), encoding="utf-8"
        )

        reader = ValidationArtifactReader(tmp_path)
        assert reader.read("deterministic_replay") is None

    def test_read_all_returns_none_for_missing(self, tmp_path: Path) -> None:
        reader = ValidationArtifactReader(tmp_path)
        results = reader.read_all(("deterministic_replay", "no_lookahead"))
        assert results["deterministic_replay"] is None
        assert results["no_lookahead"] is None


# ---------------------------------------------------------------------------
# ResearchMetricsFromValidationArtifacts tests
# ---------------------------------------------------------------------------


class TestResearchMetricsFromValidationArtifacts:
    def test_missing_deterministic_replay_yields_none(self, tmp_path: Path) -> None:
        """If deterministic_replay.json is missing, field is None and promotion rejected."""
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, _workflow_summary())
        assert derivation.deterministic_replay_passed is None
        assert derivation.promotion_eligible is False

    def test_missing_no_lookahead_yields_none(self, tmp_path: Path) -> None:
        """If no_lookahead.json is missing, field is None and promotion rejected."""
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, _workflow_summary())
        assert derivation.no_lookahead_passed is None
        assert derivation.promotion_eligible is False

    def test_deterministic_replay_passed_derives_from_artifact(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.2,
                        "score": 1.0,
                        "train_manifest_hash": "sha256:train",
                        "manifest_hash": "sha256:test",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(
            reader,
            _workflow_summary(),
        )
        assert derivation.deterministic_replay_passed is True

    def test_no_lookahead_passed_derives_from_artifact(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.2,
                        "score": 1.0,
                        "train_manifest_hash": "sha256:train",
                        "manifest_hash": "sha256:test",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(
            reader,
            _workflow_summary(),
        )
        assert derivation.no_lookahead_passed is True

    def test_failed_deterministic_replay_rejects_promotion(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": False})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.2,
                        "score": 1.0,
                        "train_manifest_hash": "sha256:train",
                        "manifest_hash": "sha256:test",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(
            reader,
            _workflow_summary(),
        )
        assert derivation.deterministic_replay_passed is False
        assert derivation.promotion_eligible is False

    def test_walk_forward_consistency_derives_from_artifact(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.5,
                        "score": 1.2,
                        "train_manifest_hash": "sha256:train",
                        "manifest_hash": "sha256:test",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(
            reader,
            _workflow_summary(),
        )
        assert derivation.walk_forward_consistency == pytest.approx(0.8)

    def test_parameter_sensitivity_derives_from_cost_stress(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.2,
                        "score": 1.0,
                        "train_manifest_hash": "sha256:train",
                        "manifest_hash": "sha256:test",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.2})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(
            reader,
            _workflow_summary(),
        )
        assert derivation.parameter_sensitivity == pytest.approx(0.8)

    def test_oos_months_computed_from_workflow_summary(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.2,
                        "score": 1.0,
                        "train_manifest_hash": "sha256:train",
                        "manifest_hash": "sha256:test",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})
        reader = ValidationArtifactReader(tmp_path)
        summary = {
            "periods": [
                {
                    "start": "2022-01-01T00:00:00+00:00",
                    "end": "2023-01-01T00:00:00+00:00",
                    "name": "oos",
                    "role": "oos",
                }
            ]
        }
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, summary)
        assert derivation.oos_months is not None
        assert derivation.oos_months > 0

    def test_train_sharpe_and_oos_sharpe_from_separate_manifests(self, tmp_path: Path) -> None:
        _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
        _write_artifact(tmp_path, "no_lookahead", {"passed": True})
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.5,
                        "score": 1.2,
                        "train_manifest_hash": "sha256:train-manifest-diff",
                        "manifest_hash": "sha256:test-manifest-diff",
                    }
                ],
            },
        )
        _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, _workflow_summary())
        assert derivation.sharpe_sources.train_sharpe == 1.5
        assert derivation.sharpe_sources.oos_sharpe == 1.2
        assert derivation.sharpe_sources.train_manifest_hash == "sha256:train-manifest-diff"
        assert derivation.sharpe_sources.oos_manifest_hash == "sha256:test-manifest-diff"
        assert not derivation.sharpe_sources.same_source

    def test_same_source_sharpe_detected_as_overfit(self, tmp_path: Path) -> None:
        _write_artifact(
            tmp_path,
            "walk_forward_validation",
            {
                "consistent": True,
                "test_windows": [
                    {
                        "accepted": True,
                        "train_score": 1.5,
                        "score": 1.5,
                        "train_manifest_hash": "sha256:same-manifest",
                        "manifest_hash": "sha256:same-manifest",
                    }
                ],
            },
        )
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, _workflow_summary())
        assert derivation.sharpe_sources.same_source is True
        assert derivation.is_overfit_candidate is True

    def test_derivation_has_hollow_verdict_when_artifacts_missing(self, tmp_path: Path) -> None:
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, _workflow_summary())
        assert derivation.has_hollow_verdict is True

    def test_derivation_no_hollow_verdict_when_artifacts_present(self, tmp_path: Path) -> None:
        _write_all_passing_artifacts(tmp_path)
        reader = ValidationArtifactReader(tmp_path)
        derivation = ResearchMetricsFromValidationArtifacts().derive(reader, _workflow_summary())
        assert derivation.has_hollow_verdict is False


# ---------------------------------------------------------------------------
# PromotionPacketV2 rejection tests
# ---------------------------------------------------------------------------


class TestPromotionPacketHollowVerdictRejection:
    def test_missing_deterministic_replay_rejected(self, tmp_path: Path) -> None:
        """deterministic_replay_passed=None triggers rejection."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["research"]["deterministic_replay_passed"] = None

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("deterministic_replay_passed is missing" in r for r in result.reasons)

    def test_missing_no_lookahead_rejected(self, tmp_path: Path) -> None:
        """no_lookahead_passed=None triggers rejection."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["research"]["no_lookahead_passed"] = None

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("no_lookahead_passed is missing" in r for r in result.reasons)

    def test_missing_promotion_eligible_rejected(self, tmp_path: Path) -> None:
        """promotion_eligible=None triggers rejection."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["research"]["promotion_eligible"] = None

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("promotion_eligible is missing" in r for r in result.reasons)

    def test_hollow_verdict_sentinel_rejected(self, tmp_path: Path) -> None:
        """All-True booleans + parameter_sensitivity=1.0 + walk_forward=1.0 + oos_months=12.0."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["research"]["deterministic_replay_passed"] = True
        metrics["research"]["no_lookahead_passed"] = True
        metrics["research"]["promotion_eligible"] = True
        metrics["stability"]["parameter_sensitivity"] = 1.0
        metrics["stability"]["walk_forward_consistency"] = 1.0
        metrics["trading"]["oos_months"] = 12.0

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("hollow verdict sentinel" in r for r in result.reasons)

    def test_same_source_train_oos_sharpe_rejected(self, tmp_path: Path) -> None:
        """train_sharpe == oos_sharpe from same manifest hash is rejected."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["performance"]["train_sharpe"] = 1.2
        metrics["performance"]["oos_sharpe"] = 1.2
        metrics["performance"]["train_manifest_hash"] = "sha256:same"
        metrics["performance"]["oos_manifest_hash"] = "sha256:same"

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("known overfit candidate" in r for r in result.reasons)

    def test_identical_sharpe_without_provenance_rejected(self, tmp_path: Path) -> None:
        """train_sharpe == oos_sharpe without manifest hashes is suspicious."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["performance"]["train_sharpe"] = 1.2
        metrics["performance"]["oos_sharpe"] = 1.2
        # No manifest hash fields -> suspicious
        metrics["performance"].pop("train_manifest_hash", None)
        metrics["performance"].pop("oos_manifest_hash", None)

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("without separate source manifest provenance" in r for r in result.reasons)

    def test_different_sharpe_from_different_manifests_accepted(self, tmp_path: Path) -> None:
        """train_sharpe != oos_sharpe from different manifests passes."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is True

    def test_missing_train_sharpe_rejected(self, tmp_path: Path) -> None:
        """Missing train_sharpe triggers rejection."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["performance"].pop("train_sharpe")

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("train_sharpe is missing" in r for r in result.reasons)

    def test_missing_oos_sharpe_rejected(self, tmp_path: Path) -> None:
        """Missing oos_sharpe triggers rejection."""
        registry, bundle_id = _write_verifiable_bundle(tmp_path)
        metrics = _honest_metrics()
        metrics["performance"].pop("oos_sharpe")

        result = PromotionPacketV2.from_payload(
            _packet_payload(bundle_id, metrics_payload=metrics)
        ).validate(
            evidence_registry=registry,
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
        )

        assert result.accepted is False
        assert any("oos_sharpe is missing" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# SharpeSources tests
# ---------------------------------------------------------------------------


class TestSharpeSources:
    def test_same_source_detected(self) -> None:
        sources = SharpeSources(
            train_sharpe=1.0,
            oos_sharpe=1.0,
            train_manifest_hash="sha256:same",
            oos_manifest_hash="sha256:same",
        )
        assert sources.same_source is True

    def test_different_source_not_flagged(self) -> None:
        sources = SharpeSources(
            train_sharpe=1.0,
            oos_sharpe=1.0,
            train_manifest_hash="sha256:train",
            oos_manifest_hash="sha256:test",
        )
        assert sources.same_source is False

    def test_none_manifest_not_same_source(self) -> None:
        sources = SharpeSources(
            train_sharpe=1.0,
            oos_sharpe=1.0,
            train_manifest_hash=None,
            oos_manifest_hash="sha256:test",
        )
        assert sources.same_source is False


# ---------------------------------------------------------------------------
# ResearchMetricsDerivation tests
# ---------------------------------------------------------------------------


class TestResearchMetricsDerivation:
    def test_overfit_candidate_detected(self) -> None:
        derivation = ResearchMetricsDerivation(
            deterministic_replay_passed=True,
            no_lookahead_passed=True,
            walk_forward_consistency=0.8,
            parameter_sensitivity=0.9,
            oos_months=12.0,
            sharpe_sources=SharpeSources(
                train_sharpe=1.5,
                oos_sharpe=1.5,
                train_manifest_hash="sha256:same",
                oos_manifest_hash="sha256:same",
            ),
            promotion_eligible=False,
        )
        assert derivation.is_overfit_candidate is True

    def test_different_sharpe_not_overfit(self) -> None:
        derivation = ResearchMetricsDerivation(
            deterministic_replay_passed=True,
            no_lookahead_passed=True,
            walk_forward_consistency=0.8,
            parameter_sensitivity=0.9,
            oos_months=12.0,
            sharpe_sources=SharpeSources(
                train_sharpe=1.5,
                oos_sharpe=1.2,
                train_manifest_hash="sha256:train",
                oos_manifest_hash="sha256:test",
            ),
            promotion_eligible=True,
        )
        assert derivation.is_overfit_candidate is False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_artifact(
    artifact_dir: Path,
    artifact_name: str,
    payload: dict[str, Any],
) -> None:
    """Write a validation artifact JSON file."""
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


def _write_all_passing_artifacts(tmp_path: Path) -> None:
    """Write all required validation artifacts with passing results."""
    _write_artifact(tmp_path, "deterministic_replay", {"passed": True})
    _write_artifact(tmp_path, "no_lookahead", {"passed": True})
    _write_artifact(
        tmp_path,
        "walk_forward_validation",
        {
            "consistent": True,
            "test_windows": [
                {
                    "accepted": True,
                    "train_score": 1.2,
                    "score": 1.0,
                    "train_manifest_hash": "sha256:train-hash",
                    "manifest_hash": "sha256:test-hash",
                }
            ],
        },
    )
    _write_artifact(tmp_path, "cost_stress", {"degradation": 0.1})


def _workflow_summary() -> dict[str, Any]:
    return {
        "periods": [
            {
                "start": "2021-01-01T00:00:00+00:00",
                "end": "2022-01-01T00:00:00+00:00",
                "name": "selection",
                "role": "selection",
            },
            {
                "start": "2021-07-01T00:00:00+00:00",
                "end": "2022-01-01T00:00:00+00:00",
                "name": "oos",
                "role": "oos",
            },
        ]
    }


def _honest_metrics() -> dict[str, dict[str, object]]:
    """Metrics payload with honest, artifact-derived values."""
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
        },
        "performance": {
            "max_drawdown": 0.2,
            "oos_manifest_hash": "sha256:oos-manifest",
            "oos_sharpe": 1.0,
            "total_return": 0.15,
            "train_manifest_hash": "sha256:train-manifest",
            "train_sharpe": 1.2,
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


def _packet_payload(
    bundle_id: str,
    *,
    target_mode: str = "paper_simulated",
    metrics_payload: dict[str, dict[str, object]] | None = None,
) -> dict[str, Any]:
    metrics = metrics_payload or _honest_metrics()
    return {
        "schema_version": 2,
        "promotion_candidate_id": "pc-test",
        "target_mode": target_mode,
        "strategy_id": "test",
        "source_module": "strategies.research.test",
        "target_module": "strategies.production.test",
        "idea_id": "idea-test",
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
    from datetime import UTC, datetime

    idea = IdeaSpec(
        idea_id="idea-test",
        title="Test strategy",
        hypothesis="Test hypothesis.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(
        summary_path,
        idea=idea,
        strategy_id="test",
    )
    return registry, bundle.evidence_bundle_id
