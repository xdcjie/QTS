from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from qts.core.hashing import stable_json_hash
from qts.research.artifact_graph import ResearchArtifactGraph, ResearchArtifactGraphWriter
from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry
from qts.research.idea_spec import IdeaSpec
from qts.research.promotion_packet import PromotionPacketV2


def test_complete_paper_packet_accepted(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate(
        evidence_registry=registry,
        audit_log=audit_log,
    )

    assert result.accepted is True
    assert result.status == "accepted"
    assert result.reasons == ()
    assert result.audit_record_id
    assert result.packet_hash == stable_json_hash(_packet_payload(bundle_id))


def test_promotion_packet_v2_is_public_package_export() -> None:
    import qts.research as research

    assert research.PromotionPacketV2 is PromotionPacketV2


def test_target_module_prefix_must_be_production_package(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id)
    payload["target_module"] = "strategies.production_evil.vwap"

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "target_module must start with strategies.production." in result.reasons


def test_review_fields_are_required(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id)
    payload["review"] = {"reviewer": "risk", "decision": "go"}

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "review.reviewed_at is required" in result.reasons


def test_evidence_bundle_hash_path_mismatch_rejected_via_registry_verify(
    tmp_path: Path,
) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    (tmp_path / "metrics.json").write_text('{"sharpe": "99.0"}\n', encoding="utf-8")

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert result.status == "rejected"
    assert any("hash mismatch" in reason for reason in result.reasons)


def test_metrics_missing_required_field_rejected(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _valid_metrics()
    del metrics["quality"]["sharpe"]

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "quality.sharpe missing for promotion" in result.reasons


def test_metrics_schema_id_mismatch_rejected(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id)
    payload["metrics"]["metrics_schema_id"] = "schema_v1"

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "metrics.metrics_schema_id mismatch: schema_v1 != schema_v2" in result.reasons


def test_failed_research_safety_metric_rejected(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    metrics = _valid_metrics()
    metrics["research"]["no_lookahead_passed"] = False

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, metrics_payload=metrics)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "research.no_lookahead_passed must be true" in result.reasons


def test_default_metrics_schema_path_is_not_cwd_dependent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    monkeypatch.chdir(tmp_path)

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate(
        evidence_registry=registry,
        audit_log=audit_log,
    )

    assert result.accepted is True


def test_dirty_git_rejected(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, reproducibility_payload=_repro_payload(git_dirty=True))
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "git working tree is dirty" in result.reasons


def test_failed_data_quality_rejected(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    data_quality = _data_quality_payload()
    data_quality["missing_bars"] = 3

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, data_quality_payload=data_quality)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert any("missing bars detected: 3" in reason for reason in result.reasons)


def test_payload_hash_required_for_payload_sections(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id)
    del payload["metrics"]["payload_hash"]
    del payload["data_quality"]["payload_hash"]
    del payload["reproducibility"]["payload_hash"]

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "metrics.payload_hash is required" in result.reasons
    assert "data_quality.payload_hash is required" in result.reasons
    assert "reproducibility.payload_hash is required" in result.reasons


def test_complete_live_packet_requires_hashed_artifact_refs_and_is_accepted(
    tmp_path: Path,
) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)

    result = PromotionPacketV2.from_payload(
        _packet_payload(bundle_id, target_mode="live_canary", artifact_root=tmp_path)
    ).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is True
    assert result.reasons == ()


def test_live_packet_rejects_plain_runtime_and_operations_fields(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id, target_mode="live", artifact_root=tmp_path)
    payload["runtime"]["risk_profile_id"] = "risk-live"
    payload["operations"]["rollback_plan"] = "disable live strategy"

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "runtime.risk_profile_id must be an artifact ref for live" in result.reasons
    assert "operations.rollback_plan must be an artifact ref for live" in result.reasons


def test_live_packet_rejects_artifact_ref_hash_mismatch(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id, target_mode="live_observation", artifact_root=tmp_path)
    payload["runtime"]["kill_switch_profile"]["payload_hash"] = "sha256:wrong"

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert any(
        reason.startswith("runtime.kill_switch_profile.payload_hash mismatch:")
        for reason in result.reasons
    )


def test_live_packet_rejects_missing_artifact_ref_path(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id, target_mode="live_observation", artifact_root=tmp_path)
    payload["runtime"]["risk_profile_id"]["path"] = str(tmp_path / "missing-risk.json")

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "runtime.risk_profile_id.path does not exist" in result.reasons


def test_live_packet_requires_operations_evidence_artifact_refs(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id, target_mode="live_canary", artifact_root=tmp_path)
    payload["operations"].pop("paper_soak_evidence")

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "operations.paper_soak_evidence is required for live_canary" in result.reasons


def test_live_packet_missing_kill_switch_rejected(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    payload = _packet_payload(bundle_id, target_mode="live_canary", artifact_root=tmp_path)
    payload["runtime"].pop("kill_switch_profile")

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
    )

    assert result.accepted is False
    assert "runtime.kill_switch_profile is required for live_canary" in result.reasons


def test_tampered_audit_chain_rejects_without_appending_record(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    audit_log.append("promotion_packet_validated", {"status": "original"})
    audit_log.path.write_text(
        audit_log.path.read_text(encoding="utf-8").replace("original", "tampered"),
        encoding="utf-8",
    )

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate(
        evidence_registry=registry,
        audit_log=audit_log,
    )

    assert result.accepted is False
    assert result.status == "rejected"
    assert result.audit_record_id == ""
    assert any(reason.startswith("audit hash chain invalid:") for reason in result.reasons)
    assert len(audit_log.path.read_text(encoding="utf-8").splitlines()) == 1


def test_validation_writes_audit_record_and_chain_verifies(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate(
        evidence_registry=registry,
        audit_log=audit_log,
    )

    records = audit_log.list()
    assert len(records) == 2
    assert records[0].record_type == "human_review_decided"
    assert records[0].payload["reviewer"] == "risk"
    assert records[0].payload["decision"] == "go"
    assert records[0].payload["reviewed_at"] == "2026-05-26T00:00:00+00:00"
    assert records[0].payload["evidence_bundle_id"] == bundle_id
    assert records[0].payload["promotion_candidate_id"] == "pc-vwap"
    assert records[1].record_id == result.audit_record_id
    assert records[1].record_type == "promotion_packet_validated"
    assert records[1].payload["packet_hash"] == result.packet_hash
    assert records[1].payload["accepted"] is True
    assert records[1].payload["human_review_record_id"] == records[0].record_id
    assert audit_log.verify_hash_chain() == ()


def test_validation_rejects_reviewed_at_without_timezone(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    payload = _packet_payload(bundle_id)
    payload["review"]["reviewed_at"] = "2026-05-26T00:00:00"

    result = PromotionPacketV2.from_payload(payload).validate(
        evidence_registry=registry,
        audit_log=audit_log,
    )

    assert result.accepted is False
    assert "review.reviewed_at must be timezone-aware" in result.reasons
    assert [record.record_type for record in audit_log.list()] == ["promotion_packet_validated"]


def test_validation_writes_artifact_graph_when_writer_is_supplied(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    graph_writer = ResearchArtifactGraphWriter(tmp_path / "graphs")

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate(
        evidence_registry=registry,
        audit_log=audit_log,
        artifact_graph_writer=graph_writer,
    )

    assert result.accepted is True
    graph_path = tmp_path / "graphs" / "promotion-packet-pc-vwap-artifact-graph.json"
    graph = ResearchArtifactGraph.from_payload(json.loads(graph_path.read_text(encoding="utf-8")))
    graph.validate()
    assert ("pc-vwap", bundle_id, "references") in {
        (edge.source_id, edge.target_id, edge.relation) for edge in graph.edges
    }
    assert result.audit_record_id in {node.node_id for node in graph.nodes}


def _packet_payload(
    bundle_id: str,
    *,
    target_mode: str = "paper_simulated",
    metrics_payload: dict[str, dict[str, object]] | None = None,
    data_quality_payload: dict[str, Any] | None = None,
    reproducibility_payload: dict[str, Any] | None = None,
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    metrics = metrics_payload or _valid_metrics()
    data_quality = data_quality_payload or _data_quality_payload()
    reproducibility = reproducibility_payload or _repro_payload()
    runtime: dict[str, Any] = {
        "account_id": "paper-account",
        "risk_profile_id": "risk-paper",
        "capital_limit": 100000,
        "runtime_mode": target_mode,
        "kill_switch_profile": "paper-kill-switch",
    }
    operations: dict[str, Any] = {
        "rollback_plan": "disable promoted strategy module",
        "monitoring_plan": "watch fills and reconciliation",
        "alert_policy": "page operator on kill-switch trigger",
    }
    if target_mode in {"live_observation", "live_canary", "live"}:
        runtime["risk_profile_id"] = _artifact_ref(
            "risk-live",
            {"limits": {"max_position_notional": 100000}, "profile": "live"},
            artifact_root,
        )
        runtime["kill_switch_profile"] = _artifact_ref(
            "kill-switch-live",
            {"actions": ["cancel_open_orders", "disable_strategy"], "profile": "live"},
            artifact_root,
        )
        operations["rollback_plan"] = _artifact_ref(
            "rollback-live",
            {"owner": "ops", "steps": ["disable strategy", "flatten positions"]},
            artifact_root,
        )
        operations["monitoring_plan"] = _artifact_ref(
            "monitoring-live",
            {"checks": ["fills", "reconciliation", "latency"], "owner": "ops"},
            artifact_root,
        )
        operations["paper_soak_evidence"] = _artifact_ref(
            "paper-soak-evidence",
            {"duration_hours": 72, "status": "passed"},
            artifact_root,
        )
        operations["reconciliation_evidence"] = _artifact_ref(
            "reconciliation-evidence",
            {"max_unexplained_drift": 0, "status": "passed"},
            artifact_root,
        )
        operations["kill_switch_drill_evidence"] = _artifact_ref(
            "kill-switch-drill-evidence",
            {"drill_completed": True, "status": "passed"},
            artifact_root,
        )
        operations["capital_signoff"] = _artifact_ref(
            "capital-signoff",
            {"approved_by": "risk", "capital_limit": 100000},
            artifact_root,
        )
    return {
        "schema_version": 2,
        "promotion_candidate_id": "pc-vwap",
        "target_mode": target_mode,
        "strategy_id": "vwap",
        "source_module": "strategies.research.vwap",
        "target_module": "strategies.production.vwap",
        "idea_id": "idea-vwap",
        "evidence_bundle_id": bundle_id,
        "metrics": {
            "metrics_schema_id": "schema_v2",
            "payload_hash": stable_json_hash(metrics),
            "payload": metrics,
        },
        "data_quality": {
            "artifact_id": "dq-dataset-001",
            "payload_hash": stable_json_hash(data_quality),
            "payload": data_quality,
        },
        "reproducibility": {
            "snapshot_id": "repro-001",
            "payload_hash": stable_json_hash(reproducibility),
            "payload": reproducibility,
        },
        "runtime": runtime,
        "operations": operations,
        "review": {
            "reviewer": "risk",
            "decision": "go",
            "reviewed_at": "2026-05-26T00:00:00+00:00",
        },
    }


def _artifact_ref(
    artifact_id: str,
    payload: dict[str, Any],
    artifact_root: Path | None = None,
) -> dict[str, Any]:
    ref = {
        "artifact_id": artifact_id,
        "payload_hash": stable_json_hash(payload),
        "payload": payload,
    }
    if artifact_root is not None:
        path = artifact_root / f"{artifact_id}.json"
        path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        ref["path"] = str(path)
    return ref


def _valid_metrics() -> dict[str, dict[str, object]]:
    return {
        "execution": {
            "cost_impact": 0.01,
            "slippage_sensitivity": 0.02,
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
            "oos_months": 12.0,
            "oos_trade_count": 40,
        },
    }


def _data_quality_payload() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "dataset_id": "dataset-001",
        "accepted": True,
        "checked_paths": [],
        "issues": [],
        "duplicate_timestamps": 0,
        "missing_bars": 0,
        "session_alignment": True,
        "stale_prices": 0,
        "halted_sessions": 0,
        "label_visibility": True,
    }


def _repro_payload(*, git_dirty: bool = False) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "git_sha": "abc123",
        "git_dirty": git_dirty,
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


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _write_verifiable_bundle(tmp_path: Path) -> tuple[EvidenceRegistry, str]:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = _sha256(artifact_path)

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
        idea_id="idea-vwap",
        title="VWAP pullback",
        hypothesis="VWAP pullback persists after costs.",
        edge_type="mean_reversion",
        source="fixture",
        created_at=datetime(2026, 5, 25, tzinfo=UTC),
    )
    registry = EvidenceRegistry(tmp_path / "evidence")
    bundle = registry.create_from_workflow_summary(
        summary_path,
        idea=idea,
        strategy_id="vwap",
    )
    return registry, bundle.evidence_bundle_id
