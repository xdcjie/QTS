from __future__ import annotations

from pathlib import Path

MATRIX_PATH = Path("docs/plan/qts_vs_lean_p1_module_health_review_status_matrix.md")
BACKLOG_PATH = Path("docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md")
P1_MODULE_HEALTH_IDS = tuple(f"OPT-{index:02d}" for index in range(4, 12))


def test_qts_vs_lean_p1_module_health_matrix_covers_scope() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    required_sections = (
        "## Completion Rules",
        "## P1 Module Health Correctness Invariants",
        "## Status Matrix",
        "## Verification Plan",
        "## Verification Log",
    )
    for section in required_sections:
        assert section in matrix

    for opt_id in P1_MODULE_HEALTH_IDS:
        assert f"| {opt_id}" in matrix

    assert str(BACKLOG_PATH) in matrix
    assert "no legacy" in matrix.lower()
    assert "no compatibility" in matrix.lower()
    assert "First Red Gate" in matrix
    assert "OPT-12" not in matrix


def test_qts_vs_lean_p1_module_health_backlog_links_to_matrix() -> None:
    backlog = BACKLOG_PATH.read_text(encoding="utf-8")

    for opt_id in P1_MODULE_HEALTH_IDS:
        item_start = backlog.index(f"#### {opt_id}")
        next_item_start = backlog.find("#### OPT-", item_start + 1)
        item = (
            backlog[item_start:] if next_item_start == -1 else backlog[item_start:next_item_start]
        )

        assert "- Status: DONE" in item
        assert f"- Review status matrix: `{MATRIX_PATH}`" in item
