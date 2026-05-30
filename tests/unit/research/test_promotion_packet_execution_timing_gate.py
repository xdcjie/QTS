"""Promotion-grade execution-timing gate on the promotion packet (C1).

A backtest that fills at the decision bar's own close (``same_bar_close``) is
optimistic look-ahead and cannot, on its own, back paper/live promotion
evidence. The promotion packet's machine validation must:

* REJECT when the evidence backtest used optimistic same-bar fills with no
  waiver (``research.fill_timing_promotion_grade`` is False).
* PASS when an explicit optimistic waiver made the evidence promotion-grade,
  but surface an explicit ``optimistic`` flag so the packet is never silently
  treated as promotion-grade.
* PASS as non-optimistic for promotion-grade ``next_bar_open`` evidence.

This is the promotion-boundary gate; it complements the upstream
``ResearchMetricsFromValidationArtifacts`` derivation by enforcing the
fill-timing fact directly at the promotion packet.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.promotion_packet import PromotionPacketV2


def test_same_bar_close_without_waiver_rejected(tmp_path: Path) -> None:
    """Optimistic same-bar fills with no waiver fail machine validation."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _honest_metrics()
    # same_bar_close, no waiver: manifest records optimistic + not promotion-grade.
    metrics["research"]["fill_timing_optimistic"] = True
    metrics["research"]["fill_timing_promotion_grade"] = False
    # An honest upstream derivation would also reject eligibility.
    metrics["research"]["promotion_eligible"] = False

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate_machine(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert result.optimistic is False
    assert any("fill_timing_promotion_grade is False" in reason for reason in result.reasons)


def test_same_bar_close_with_waiver_passes_but_flagged_optimistic(tmp_path: Path) -> None:
    """An explicit optimistic waiver allows machine-pass with an optimistic flag."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _honest_metrics()
    # same_bar_close + waiver: manifest keeps optimistic True but flips
    # promotion_grade to True so the derivation can mark it eligible.
    metrics["research"]["fill_timing_optimistic"] = True
    metrics["research"]["fill_timing_promotion_grade"] = True

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate_machine(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is True
    assert result.status == "human_pending"
    # The waived packet is explicitly optimistic and never silently promoted.
    assert result.optimistic is True
    assert result.to_payload()["optimistic"] is True


def test_next_bar_open_passes_not_optimistic(tmp_path: Path) -> None:
    """Promotion-grade next_bar_open evidence passes and is not optimistic."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _honest_metrics()
    metrics["research"]["fill_timing_optimistic"] = False
    metrics["research"]["fill_timing_promotion_grade"] = True

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate_machine(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is True
    assert result.optimistic is False
    assert result.to_payload()["optimistic"] is False


def test_optimistic_flag_recorded_in_audit_payload(tmp_path: Path) -> None:
    """The waived-optimistic decision is persisted in the audit ledger."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _honest_metrics()
    metrics["research"]["fill_timing_optimistic"] = True
    metrics["research"]["fill_timing_promotion_grade"] = True

    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate_machine(evidence_registry=registry, audit_log=audit_log)

    validated = [
        record for record in audit_log.list() if record.record_type == "promotion_packet_validated"
    ]
    assert validated, "expected a promotion_packet_validated audit record"
    assert validated[-1].payload["optimistic"] is True


def test_missing_fill_timing_flag_not_gated_here(tmp_path: Path) -> None:
    """Synthetic fixtures that omit the flag are not rejected by this gate."""
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _honest_metrics()
    # No fill-timing fields at all: the upstream promotion_eligible derivation
    # owns the unverified-evidence rejection; this gate stays silent (None).
    metrics["research"].pop("fill_timing_optimistic", None)
    metrics["research"].pop("fill_timing_promotion_grade", None)

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate_machine(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is True
    assert result.optimistic is False
    assert not any("fill_timing_promotion_grade" in reason for reason in result.reasons)


# ---------------------------------------------------------------------------
# Helpers (self-contained fixtures matching the v2 packet contract)
# ---------------------------------------------------------------------------


def _honest_metrics() -> dict[str, dict[str, object]]:
    return {
        "execution": {"cost_impact": 0.01, "slippage_sensitivity": 0.02},
        "performance": {
            "max_drawdown": 0.2,
            "oos_manifest_hash": "sha256:oos-manifest",
            "oos_sharpe": 1.0,
            "total_return": 0.15,
            "train_manifest_hash": "sha256:train-manifest",
            "train_sharpe": 1.2,
        },
        "portfolio": {"correlation_to_active": 0.3},
        "quality": {"profit_factor": 1.4, "sharpe": 1.1},
        "research": {
            "deterministic_replay_passed": True,
            "no_lookahead_passed": True,
            "promotion_eligible": True,
        },
        "risk": {"max_drawdown": 0.2},
        "stability": {"parameter_sensitivity": 0.8, "walk_forward_consistency": 0.75},
        "trading": {"oos_months": 6.0, "oos_trade_count": 40},
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


def _write_verifiable_bundle(tmp_path: Path) -> tuple[EvidenceRegistry, str]:
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
