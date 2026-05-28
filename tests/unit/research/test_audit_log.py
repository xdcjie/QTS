from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from qts.research.audit_log import ResearchAuditLog, ResearchAuditRecord


def test_audit_record_round_trips_with_deterministic_hashes() -> None:
    created_at = datetime(2026, 5, 26, 12, 30, tzinfo=UTC)
    payload = {"strategy_id": "vwap-research", "checks": ["manifest", "hashes"]}

    record = ResearchAuditRecord.create(
        "evidence_bundle_created",
        payload,
        previous_record_hash="sha256:previous",
        created_at=created_at,
    )
    same_record = ResearchAuditRecord.create(
        "evidence_bundle_created",
        {"checks": ["manifest", "hashes"], "strategy_id": "vwap-research"},
        previous_record_hash="sha256:previous",
        created_at=created_at,
    )

    assert record.payload_hash == same_record.payload_hash
    assert record.record_hash == same_record.record_hash
    assert record.record_id == record.record_hash
    assert record.created_at.tzinfo is not None
    assert ResearchAuditRecord.from_payload(record.to_payload()) == record


def test_audit_log_appends_lists_and_verifies_hash_chain(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path)

    first = audit_log.append(
        "evidence_bundle_created",
        {"bundle_id": "bundle-a", "artifact_hash": "sha256:artifact"},
        created_at=datetime(2026, 5, 26, 12, 0, tzinfo=UTC),
    )
    second = audit_log.append(
        "evidence_validated",
        {"bundle_id": "bundle-a", "accepted": True},
        created_at=datetime(2026, 5, 26, 12, 5, tzinfo=UTC),
    )

    records = audit_log.list()
    assert records == (first, second)
    assert records[1].previous_record_hash == first.record_hash
    assert audit_log.verify_hash_chain() == ()


def test_audit_log_verification_passes_empty_ledger(tmp_path: Path) -> None:
    assert ResearchAuditLog(tmp_path / "audit.jsonl").verify_hash_chain() == ()


def test_audit_log_verification_reports_payload_tampering(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    audit_log.append(
        "promotion_packet_validated",
        {"packet_id": "packet-a", "accepted": False},
        created_at=datetime(2026, 5, 26, 13, 0, tzinfo=UTC),
    )

    row = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8"))
    row["payload"]["accepted"] = True
    (tmp_path / "audit.jsonl").write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

    reasons = audit_log.verify_hash_chain()
    assert reasons
    assert "payload_hash mismatch at line 1" in reasons[0]


def test_audit_log_verification_reports_previous_hash_tampering(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    audit_log.append(
        "evidence_bundle_created",
        {"bundle_id": "bundle-a"},
        created_at=datetime(2026, 5, 26, 14, 0, tzinfo=UTC),
    )
    audit_log.append(
        "human_review_decided",
        {"decision": "rejected"},
        created_at=datetime(2026, 5, 26, 14, 10, tzinfo=UTC),
    )

    rows = [
        json.loads(line)
        for line in (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    rows[1]["previous_record_hash"] = "sha256:tampered"
    (tmp_path / "audit.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )

    reasons = audit_log.verify_hash_chain()
    assert reasons
    assert "previous_record_hash mismatch at line 2" in reasons[0]


def test_audit_log_rejects_custom_record_id_that_breaks_chain(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")

    with pytest.raises(ValueError, match="record_id must match record_hash"):
        audit_log.append(
            "evidence_validated",
            {"bundle_id": "bundle-a", "accepted": True},
            created_at=datetime(2026, 5, 26, 15, 0, tzinfo=UTC),
            record_id="custom-record-id",
        )

    assert audit_log.verify_hash_chain() == ()


def test_audit_log_appends_human_review_decision(tmp_path: Path) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    reviewed_at = datetime(2026, 5, 26, 16, 30, tzinfo=UTC)

    record = audit_log.append_human_review_decision(
        reviewer=" risk ",
        decision=" approved ",
        reviewed_at=reviewed_at,
        evidence_bundle_id=" evb_001 ",
        promotion_candidate_id=" pc_001 ",
        notes=" ready for paper ",
    )

    assert record.record_type == "human_review_decided"
    assert record.payload == {
        "decision": "approved",
        "evidence_bundle_id": "evb_001",
        "notes": "ready for paper",
        "promotion_candidate_id": "pc_001",
        "reviewed_at": reviewed_at.isoformat(),
        "reviewer": "risk",
    }
    assert audit_log.list() == (record,)
    assert audit_log.verify_hash_chain() == ()


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"reviewer": ""}, "reviewer is required"),
        ({"decision": ""}, "decision is required"),
        ({"reviewed_at": datetime(2026, 5, 26, 16, 30)}, "reviewed_at must be timezone-aware"),
        (
            {"evidence_bundle_id": "", "promotion_candidate_id": None},
            "evidence_bundle_id, promotion_candidate_id, or packet_hash is required",
        ),
    ],
)
def test_audit_log_human_review_decision_validates_payload(
    tmp_path: Path,
    kwargs: dict[str, object],
    match: str,
) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    payload: dict[str, Any] = {
        "reviewer": "risk",
        "decision": "approved",
        "reviewed_at": datetime(2026, 5, 26, 16, 30, tzinfo=UTC),
        "evidence_bundle_id": "evb_001",
        "promotion_candidate_id": None,
    }
    payload.update(kwargs)

    with pytest.raises(ValueError, match=match):
        audit_log.append_human_review_decision(**payload)

    assert audit_log.verify_hash_chain() == ()


def test_audit_record_rejects_unknown_record_type() -> None:
    with pytest.raises(ValueError, match="unknown audit record_type"):
        ResearchAuditRecord.create("unknown", {"value": 1})
