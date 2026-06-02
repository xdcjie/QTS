"""Documentation gate: final-state wiring deferrals cannot target production."""

from __future__ import annotations

from pathlib import Path


def test_wiring_deferrals_have_no_production_exceptions() -> None:
    text = Path("docs/plan/wiring_deferrals.md").read_text(encoding="utf-8")

    production_entries = [
        line for line in text.splitlines() if line.strip().endswith("target=production")
    ]
    assert production_entries == []
