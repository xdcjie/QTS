from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog
from qts.research.evidence_registry import EvidenceRegistry


def test_evidence_registry_create_and_verify_write_audit_chain(tmp_path: Path) -> None:
    summary_path = _write_workflow_summary(tmp_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")

    bundle = registry.create_from_workflow_summary(summary_path, audit_log=audit_log)
    verification = registry.verify(bundle.evidence_bundle_id, audit_log=audit_log)

    records = audit_log.list()
    assert verification.accepted is True
    assert [record.record_type for record in records] == [
        "evidence_bundle_created",
        "evidence_validated",
    ]
    assert records[0].payload["evidence_bundle_id"] == bundle.evidence_bundle_id
    assert records[1].payload["accepted"] is True
    assert records[1].payload["status"] == "accepted"
    assert audit_log.verify_hash_chain() == ()


def test_evidence_registry_failed_verify_writes_rejected_audit_record(tmp_path: Path) -> None:
    summary_path = _write_workflow_summary(tmp_path)
    registry = EvidenceRegistry(tmp_path / "evidence")
    audit_log = ResearchAuditLog(tmp_path / "audit.jsonl")
    bundle = registry.create_from_workflow_summary(summary_path, audit_log=audit_log)
    (tmp_path / "metrics.json").write_text('{"sharpe": "99.0"}\n', encoding="utf-8")

    verification = registry.verify(bundle.evidence_bundle_id, audit_log=audit_log)

    records = audit_log.list()
    assert verification.accepted is False
    assert any("hash mismatch" in reason for reason in verification.reasons)
    assert records[-1].record_type == "evidence_validated"
    assert records[-1].payload["accepted"] is False
    assert records[-1].payload["status"] == "rejected"
    assert audit_log.verify_hash_chain() == ()


def _write_workflow_summary(tmp_path: Path) -> Path:
    artifact_path = tmp_path / "metrics.json"
    artifact_path.write_text('{"sharpe": "1.2"}\n', encoding="utf-8")
    artifact_hash = f"sha256:{hashlib.sha256(artifact_path.read_bytes()).hexdigest()}"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "artifact_hashes": {artifact_path.name: artifact_hash},
                "artifact_paths_by_hash": {artifact_hash: str(artifact_path)},
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
                "steps": [
                    {
                        "id": "manifest",
                        "kind": "manifest",
                        "outputs": {"manifest_path": str(manifest_path)},
                        "status": "passed",
                    },
                    {
                        "id": "report",
                        "kind": "report",
                        "outputs": {"report_path": str(report_path)},
                        "status": "passed",
                    },
                ],
                "workflow_id": "evidence-audit-flow",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return summary_path
