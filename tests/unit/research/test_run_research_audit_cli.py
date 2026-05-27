from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research.audit_log import ResearchAuditLog

from scripts import run_research


def test_run_research_audit_verify_accepts_valid_chain(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit")
    audit_log.append_human_review_decision(
        reviewer="risk",
        decision="go",
        reviewed_at=datetime(2026, 5, 26, tzinfo=UTC),
        evidence_bundle_id="evb_001",
    )

    exit_code = run_research.main(["audit", "verify", "--audit-log-root", str(tmp_path / "audit")])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {"accepted": True, "reasons": []}


def test_run_research_audit_verify_rejects_tampered_chain(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    audit_log = ResearchAuditLog(tmp_path / "audit")
    audit_log.append_human_review_decision(
        reviewer="risk",
        decision="go",
        reviewed_at=datetime(2026, 5, 26, tzinfo=UTC),
        evidence_bundle_id="evb_001",
    )
    audit_log.path.write_text(
        audit_log.path.read_text(encoding="utf-8").replace("go", "no_go"),
        encoding="utf-8",
    )

    exit_code = run_research.main(["audit", "verify", "--audit-log-root", str(tmp_path / "audit")])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reasons"]
