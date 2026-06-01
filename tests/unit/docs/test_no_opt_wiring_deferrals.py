"""Final-state wiring deferrals cannot target OPT roadmap work."""

from __future__ import annotations

from pathlib import Path


def test_wiring_deferrals_have_no_opt_targets() -> None:
    text = Path("docs/plan/wiring_deferrals.md").read_text(encoding="utf-8")

    assert "target=OPT-" not in text
