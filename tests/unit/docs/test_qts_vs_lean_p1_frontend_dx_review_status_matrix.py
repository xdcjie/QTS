from __future__ import annotations

from pathlib import Path

MATRIX_PATH = Path("docs/plan/qts_vs_lean_p1_frontend_dx_review_status_matrix.md")
BACKLOG_PATH = Path("docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md")

P1_FRONTEND_DX_IDS = ("OPT-12", "OPT-13", "OPT-14")


def test_qts_vs_lean_p1_frontend_dx_matrix_covers_scope() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    required_sections = (
        "## Completion Rules",
        "## P1 Frontend and DX Correctness Invariants",
        "## Status Matrix",
        "## Verification Plan",
        "## Verification Log",
    )
    for section in required_sections:
        assert section in matrix

    for opt_id in P1_FRONTEND_DX_IDS:
        assert f"| {opt_id}" in matrix

    assert str(BACKLOG_PATH) in matrix
    assert "no legacy" in matrix.lower()
    assert "no compatibility" in matrix.lower()
    assert "First Red Gate" in matrix


def test_qts_vs_lean_p1_frontend_dx_backlog_links_to_matrix() -> None:
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")

    for opt_id in P1_FRONTEND_DX_IDS:
        item_start = backlog.index(f"#### {opt_id}")
        next_item_start = backlog.find("#### OPT-", item_start + 1)
        item = (
            backlog[item_start:] if next_item_start == -1 else backlog[item_start:next_item_start]
        )

        assert "- Status: DONE" in item
        assert f"- Review status matrix: `{MATRIX_PATH}`" in item
