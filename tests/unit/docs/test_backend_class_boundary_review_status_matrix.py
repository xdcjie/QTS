from __future__ import annotations

from pathlib import Path

MATRIX_PATH = Path("docs/plan/backend_class_boundary_review_status_matrix.md")
REQUIRED_COLUMNS = (
    "Class",
    "Current lines",
    "Owner",
    "Risk",
    "Decision",
    "Target",
    "Evidence",
    "Status",
)
REQUIRED_CLASSES = (
    "IbkrOrderExecutionAdapter",
    "RuntimeMarketDataCoordinator",
    "BacktestActorLoop",
    "OperationsService",
    "BacktestEngine",
    "RuntimeSession",
    "ReplayMarketDataSource",
    "IbkrTwsMarketDataTransport",
    "IbkrTwsOrderExecutionTransport",
)


def test_backend_class_boundary_review_status_matrix_covers_required_classes() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    assert "# Backend Class Boundary Review Status Matrix" in matrix
    assert "## Completion Rules" in matrix
    assert "## Status Matrix" in matrix
    assert "## Verification Plan" in matrix

    header = "| " + " | ".join(REQUIRED_COLUMNS) + " |"
    assert header in matrix

    for class_name in REQUIRED_CLASSES:
        assert f"| {class_name} |" in matrix


def test_backend_class_boundary_review_status_matrix_records_required_gates() -> None:
    matrix = MATRIX_PATH.read_text(encoding="utf-8")

    assert "production classes over 300 lines" in matrix
    assert "production classes over 500 lines" in matrix
    assert "split" in matrix.lower()
    assert "retain" in matrix.lower()
    assert "`make guardrails`" in matrix
