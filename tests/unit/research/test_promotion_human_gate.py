from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.core.hashing import stable_json_hash
from qts.research.audit_log import ResearchAuditLog
from qts.research.promotion_packet import PromotionMachineValidationResult, PromotionPacketV2

from tests.unit.research.test_promotion_packet import _packet_payload, _write_verifiable_bundle


def test_machine_validation_returns_human_pending_without_human_review(
    tmp_path: Path,
) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")

    result = PromotionPacketV2.from_payload(_packet_payload(bundle_id)).validate_machine(
        evidence_registry=registry,
        audit_log=audit_log,
    )

    assert isinstance(result, PromotionMachineValidationResult)
    assert result.accepted is True
    assert result.status == "human_pending"
    assert "human_review_decided" not in {record.record_type for record in audit_log.list()}


def test_human_review_records_packet_hash_after_machine_validation(tmp_path: Path) -> None:
    registry, bundle_id = _write_verifiable_bundle(tmp_path)
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    packet = PromotionPacketV2.from_payload(_packet_payload(bundle_id))
    machine = packet.validate_machine(evidence_registry=registry, audit_log=audit_log)

    result = packet.human_review(
        audit_log=audit_log,
        decision="approved",
        reviewer="risk",
        reviewed_at=datetime(2026, 5, 28, tzinfo=UTC),
        expected_packet_hash=machine.packet_hash,
        notes="reviewed release evidence",
    )

    assert result.accepted is True
    assert result.status == "human_approved"
    records = audit_log.list()
    assert records[-1].record_type == "human_review_decided"
    assert records[-1].payload["packet_hash"] == machine.packet_hash
    assert records[-1].payload["decision"] == "approved"


def test_human_review_rejects_packet_hash_mismatch(tmp_path: Path) -> None:
    _registry, bundle_id = _write_verifiable_bundle(tmp_path)
    packet = PromotionPacketV2.from_payload(_packet_payload(bundle_id))

    with pytest.raises(ValueError, match="packet hash mismatch"):
        packet.human_review(
            audit_log=ResearchAuditLog(tmp_path / "audit.jsonl"),
            decision="approved",
            reviewer="risk",
            reviewed_at=datetime(2026, 5, 28, tzinfo=UTC),
            expected_packet_hash=stable_json_hash({"wrong": True}),
        )
