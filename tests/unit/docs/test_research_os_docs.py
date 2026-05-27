from __future__ import annotations

from pathlib import Path


def test_research_strategy_boundary_doc_covers_migration_path() -> None:
    doc = Path("docs/research/strategy_boundaries.md").read_text(encoding="utf-8")

    assert "strategies/research/" in doc
    assert "strategies/production/" in doc
    assert "examples/strategies/" in doc
    assert "Production strategies must not import from `strategies.research`" in doc
    assert "Research evidence is not paper/live/production approval" in doc
    assert "PromotionPacketV2" in doc
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


def test_research_os_docs_reference_cli_examples() -> None:
    doc = Path("docs/research/research_os.md").read_text(encoding="utf-8")

    assert "scripts/run_research.py" in doc
    assert "evidence --registry-root" in doc
    assert "idea --registry-root" in doc
    assert "meta --output-dir" in doc
    assert "source_summary: matrix-summary.json" in doc


def test_research_os_issue_template_links_required_docs() -> None:
    template = Path(".github/ISSUE_TEMPLATE/research_os_work_package.md").read_text(
        encoding="utf-8"
    )

    for doc_path in (
        "docs/research/evidence_registry.md",
        "docs/research/idea_registry.md",
        "docs/research/factor_protocol.md",
        "docs/research/trade_diagnostics.md",
        "docs/research/promotion.md",
    ):
        assert doc_path in template
        assert Path(doc_path).exists()
