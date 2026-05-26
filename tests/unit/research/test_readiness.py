from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.research.readiness import (
    HumanApprovalRecord,
    PaperLiveReadinessDecision,
    PaperLiveReadinessEvidence,
)


def test_live_readiness_decision_requires_paper_duration() -> None:
    with pytest.raises(ValueError, match="paper_trading_days must be at least 20"):
        PaperLiveReadinessDecision(
            strategy_id="vwap_pullback",
            decision_date="2026-05-26",
            target_status="live_approved",
            evidence=PaperLiveReadinessEvidence(
                paper_trading_days=19,
                reconciliation_evidence_ref="artifacts/paper/reconciliation.json",
                risk_limits_ref="configs/risk/vwap_pullback.yaml",
                kill_switch_ref="docs/runbooks/vwap_pullback_live_runbook.md#kill-switch",
                runbook_ref="docs/runbooks/vwap_pullback_live_runbook.md",
                alerting_checks_ref="artifacts/paper/alerts.json",
                monitoring_checks_ref="artifacts/paper/monitoring.json",
            ),
            approval=HumanApprovalRecord(
                approved_by="ops-lead",
                approved_at="2026-05-26T10:00:00Z",
                approval_ref="ticket-123",
            ),
        )


def test_live_readiness_decision_requires_all_evidence_refs() -> None:
    evidence = PaperLiveReadinessEvidence(
        paper_trading_days=20,
        reconciliation_evidence_ref="",
        risk_limits_ref="configs/risk/vwap_pullback.yaml",
        kill_switch_ref="docs/runbooks/vwap_pullback_live_runbook.md#kill-switch",
        runbook_ref="docs/runbooks/vwap_pullback_live_runbook.md",
        alerting_checks_ref="artifacts/paper/alerts.json",
        monitoring_checks_ref="artifacts/paper/monitoring.json",
    )

    with pytest.raises(ValueError, match="reconciliation_evidence_ref is required"):
        PaperLiveReadinessDecision(
            strategy_id="vwap_pullback",
            decision_date="2026-05-26",
            target_status="live_approved",
            evidence=evidence,
            approval=HumanApprovalRecord(
                approved_by="ops-lead",
                approved_at="2026-05-26T10:00:00Z",
                approval_ref="ticket-123",
            ),
        )


def test_live_readiness_decision_requires_human_approval_record() -> None:
    with pytest.raises(ValueError, match="approved_by is required"):
        PaperLiveReadinessDecision(
            strategy_id="vwap_pullback",
            decision_date="2026-05-26",
            target_status="live_approved",
            evidence=_complete_evidence(),
            approval=HumanApprovalRecord(
                approved_by="",
                approved_at="2026-05-26T10:00:00Z",
                approval_ref="ticket-123",
            ),
        )


def test_readiness_decision_payload_matches_artifact_contract() -> None:
    decision = PaperLiveReadinessDecision(
        strategy_id="vwap_pullback",
        decision_date="2026-05-26",
        target_status="live_approved",
        evidence=_complete_evidence(),
        approval=HumanApprovalRecord(
            approved_by="ops-lead",
            approved_at="2026-05-26T10:00:00Z",
            approval_ref="ticket-123",
        ),
    )

    payload = decision.to_payload()

    assert json.dumps(payload, sort_keys=True)
    assert payload["artifact"] == (
        "artifacts/readiness/vwap_pullback/2026-05-26/paper_live_gate_decision.json"
    )
    assert payload["paper_live_readiness_gate"] == "approved"
    assert payload["evidence"]["paper_trading_days"] == 20


def test_readiness_decision_writes_standard_artifact(tmp_path: Path) -> None:
    decision = PaperLiveReadinessDecision(
        strategy_id="vwap_pullback",
        decision_date="2026-05-26",
        target_status="live_approved",
        evidence=_complete_evidence(),
        approval=HumanApprovalRecord(
            approved_by="ops-lead",
            approved_at="2026-05-26T10:00:00Z",
            approval_ref="ticket-123",
        ),
    )

    output = decision.write(tmp_path)

    assert output == (tmp_path / "vwap_pullback" / "2026-05-26" / "paper_live_gate_decision.json")
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["strategy_id"] == "vwap_pullback"
    assert payload["paper_live_readiness_gate"] == "approved"


def test_readiness_decision_rejects_unapproved_lifecycle_target() -> None:
    with pytest.raises(ValueError, match="target_status must be one of"):
        PaperLiveReadinessDecision(
            strategy_id="vwap_pullback",
            decision_date="2026-05-26",
            target_status="research_passed",
            evidence=_complete_evidence(),
            approval=HumanApprovalRecord(
                approved_by="ops-lead",
                approved_at="2026-05-26T10:00:00Z",
                approval_ref="ticket-123",
            ),
        )


def test_checked_in_live_runbook_covers_required_readiness_sections() -> None:
    runbook = "docs/runbooks/vwap_pullback_live_runbook.md"
    text = Path(runbook).read_text(encoding="utf-8")

    assert "## Kill Switch" in text
    assert "## Reconciliation" in text
    assert "## Rollback" in text


def _complete_evidence() -> PaperLiveReadinessEvidence:
    return PaperLiveReadinessEvidence(
        paper_trading_days=20,
        reconciliation_evidence_ref="artifacts/paper/reconciliation.json",
        risk_limits_ref="configs/risk/vwap_pullback.yaml",
        kill_switch_ref="docs/runbooks/vwap_pullback_live_runbook.md#kill-switch",
        runbook_ref="docs/runbooks/vwap_pullback_live_runbook.md",
        alerting_checks_ref="artifacts/paper/alerts.json",
        monitoring_checks_ref="artifacts/paper/monitoring.json",
    )
