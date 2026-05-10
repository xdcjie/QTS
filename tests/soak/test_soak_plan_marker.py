from __future__ import annotations

from pathlib import Path


def test_soak_plan_documents_duration_metrics_and_drift_gate() -> None:
    plan = Path("docs/operations/production_soak_plan.md").read_text()

    assert "duration" in plan.lower()
    assert "event lag" in plan.lower()
    assert "state drift" in plan.lower()
