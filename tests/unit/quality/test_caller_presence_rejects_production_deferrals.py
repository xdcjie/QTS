"""Caller-presence deferrals cannot bypass production wiring."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from qts.quality.rules.caller_presence import CallerPresenceRule


def test_caller_presence_rule_rejects_production_deferrals(tmp_path: Path) -> None:
    (tmp_path / "artifacts/quality").mkdir(parents=True)
    (tmp_path / "docs/plan").mkdir(parents=True)
    (tmp_path / "artifacts/quality/class_inventory_baseline.json").write_text(
        json.dumps({"production_classes": ["qts.example.Example"]}),
        encoding="utf-8",
    )
    (tmp_path / "docs/plan/wiring_deferrals.md").write_text(
        """
```
qts.example.Example  expires=2026-08-30  target=production
```
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="target=production"):
        CallerPresenceRule(repo_root=tmp_path).check_repository(tmp_path)
