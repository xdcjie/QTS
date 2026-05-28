from __future__ import annotations

from pathlib import Path

from qts.research.audit_log import ResearchAuditLog

from tests.integration.research._autonomous_engine_plan_helpers import run_engine


def test_autonomous_engine_audits_selected_evidence_lifecycle(tmp_path: Path) -> None:
    _campaign_path, result = run_engine(tmp_path)

    selected_count = len(result.generations[0].experiment_result.trials)
    records = ResearchAuditLog(result.audit_log_path).list()
    created = [
        record
        for record in records
        if record.record_type == "evidence_bundle_created"
        and record.payload.get("evidence_bundle_id")
    ]
    validated = [
        record
        for record in records
        if record.record_type == "evidence_validated" and record.payload.get("evidence_bundle_id")
    ]

    assert len(created) >= selected_count
    assert len(validated) >= selected_count
