from __future__ import annotations

from pathlib import Path

MATRIX_PATH = Path("docs/plan/qts_vs_lean_p0_review_status_matrix.md")
BACKLOG_PATH = Path("docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md")


def test_qts_vs_lean_p0_review_status_matrix_covers_all_p0_work() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    required_sections = (
        "## Completion Rules",
        "## P0 Correctness Invariants",
        "## Status Matrix",
        "## Verification Plan",
        "## Verification Log",
    )
    for section in required_sections:
        assert section in matrix

    for opt_id in ("OPT-01", "OPT-02", "OPT-03"):
        assert f"| {opt_id}" in matrix

    assert str(BACKLOG_PATH) in matrix
    assert "no legacy" in matrix.lower()
    assert "no compatibility" in matrix.lower()
    assert "First Red Gate" in matrix


def test_qts_vs_lean_p0_backlog_links_to_review_status_matrix() -> None:
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")
    expected_status = {
        "OPT-01": "DONE",
        "OPT-02": "IN-PROGRESS",
        "OPT-03": "IN-PROGRESS",
    }

    for opt_id, status in expected_status.items():
        item_start = backlog.index(f"#### {opt_id}")
        next_item_start = backlog.find("#### OPT-", item_start + 1)
        item = (
            backlog[item_start:] if next_item_start == -1 else backlog[item_start:next_item_start]
        )

        assert f"- Status: {status}" in item
        assert f"- Review status matrix: `{MATRIX_PATH}`" in item
