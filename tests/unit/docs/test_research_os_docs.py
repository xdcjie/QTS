from __future__ import annotations

from pathlib import Path


def test_research_strategy_boundary_doc_covers_migration_path() -> None:
    doc = Path("docs/research/strategy_boundaries.md").read_text(encoding="utf-8")

    assert "strategies/research/" in doc
    assert "strategies/production/" in doc
    assert "examples/strategies/" in doc
    assert "Production strategies must not import from `strategies.research`" in doc
    assert "Research evidence is not paper/live/production approval" in doc
    assert "PromotionCandidateSpec" in doc
    assert "evidence_bundle_id" in doc
    assert "FLOW-PROMOTION" in doc


def test_research_os_issue_template_requires_evidence_and_acceptance_criteria() -> None:
    template = Path(".github/ISSUE_TEMPLATE/research_os_work_package.md").read_text(
        encoding="utf-8"
    )

    assert "## First-Principles Behavior Contract" in template
    assert "## Required Evidence" in template
    assert "## Acceptance Criteria" in template
    assert "research evidence != paper/live/production" in template
    assert "Final response reports `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, or" in template
