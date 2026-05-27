"""Unit tests for human approval gates on next-generation proposals."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.research.audit_log import ResearchAuditLog
from qts.research.planner import (
    GenerationApprovalPolicy,
    GenerationApprovalRecord,
    NextGenerationProposal,
    SearchSpaceMutation,
)


def test_generation_proposal_cannot_execute_without_matching_approval() -> None:
    proposal = _proposal()
    policy = GenerationApprovalPolicy()

    assert policy.can_execute(proposal, None) is False
    assert policy.execution_payload(proposal, None)["accepted"] is False

    mismatched = GenerationApprovalRecord(
        proposal_id=proposal.proposal_id,
        proposal_hash="sha256:not-the-proposal",
        decision="approved",
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 1, tzinfo=UTC),
        reason="approved wrong artifact",
        evidence_refs=("review-ticket-1",),
    )

    assert policy.can_execute(proposal, mismatched) is False
    assert policy.execution_payload(proposal, mismatched)["reasons"] == (
        "approval proposal_hash does not match proposal artifact",
    )


def test_generation_approval_writes_audit_record_and_authorizes_execution(
    tmp_path: Path,
) -> None:
    proposal = _proposal()
    audit_log = ResearchAuditLog(tmp_path / "audit")

    record = GenerationApprovalPolicy().approve(
        proposal,
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 1, tzinfo=UTC),
        reason="evidence supports the bounded next generation",
        evidence_refs=("review-ticket-1",),
        audit_log=audit_log,
    )

    assert record.decision == "approved"
    assert record.proposal_hash == proposal.proposal_hash
    assert GenerationApprovalPolicy().can_execute(proposal, record) is True
    records = audit_log.list()
    assert len(records) == 1
    assert records[0].record_type == "human_review_decided"
    assert records[0].payload["proposal_hash"] == proposal.proposal_hash
    assert record.audit_record_id == records[0].record_id


def test_generation_rejection_writes_audit_record_and_blocks_execution(
    tmp_path: Path,
) -> None:
    proposal = _proposal()
    audit_log = ResearchAuditLog(tmp_path / "audit")

    record = GenerationApprovalPolicy().reject(
        proposal,
        reviewer="research-lead",
        decided_at=datetime(2026, 5, 1, tzinfo=UTC),
        reason="drawdown evidence is insufficient",
        evidence_refs=("review-ticket-2",),
        audit_log=audit_log,
    )

    assert record.decision == "rejected"
    assert GenerationApprovalPolicy().can_execute(proposal, record) is False
    assert GenerationApprovalPolicy().execution_payload(proposal, record)["reasons"] == (
        "proposal approval decision is rejected",
    )
    assert audit_log.list()[0].payload["decision"] == "rejected"


def _proposal() -> NextGenerationProposal:
    return NextGenerationProposal(
        proposal_id="proposal-001",
        campaign_id="campaign-001",
        previous_generation_id="generation-000",
        next_generation_id="generation-001",
        previous_data_window={"start": "2025-01-01", "end": "2025-12-31"},
        proposed_data_window={"start": "2025-01-01", "end": "2025-12-31"},
        trial_budget=4,
        max_trial_budget=6,
        mutations=(
            SearchSpaceMutation(
                mutation_id="search-space-001",
                target="momentum.alpha",
                action="narrow_range",
                payload={"min": 0.2, "max": 0.5},
                reason="stable accepted parameter region",
                evidence_refs=("sha256:analytics",),
            ),
        ),
    )
