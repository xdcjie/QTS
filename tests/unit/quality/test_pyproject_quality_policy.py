"""The ruff quality policy in pyproject.toml cannot silently weaken.

QTS-FINAL-010 mandates a baseline set of ruff rule families. These tests lock:
1. the live ``pyproject.toml`` actually selects every required family; and
2. ``PyprojectQualityRule`` fails when a required family is dropped.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from qts.quality.rules.pyproject_quality import REQUIRED_RUFF_FAMILIES, PyprojectQualityRule

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_live_pyproject_selects_all_required_ruff_families() -> None:
    data = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    select = set(data["tool"]["ruff"]["lint"]["select"])
    missing = [family for family in REQUIRED_RUFF_FAMILIES if family not in select]
    assert missing == [], f"pyproject ruff select is missing required families: {missing}"


def test_rule_passes_for_live_repository() -> None:
    assert PyprojectQualityRule().check_repository(_REPO_ROOT) == []


def test_rule_flags_missing_required_family(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.ruff.lint]\nselect = ["E", "F", "I", "B", "UP"]\n',
        encoding="utf-8",
    )

    violations = PyprojectQualityRule().check_repository(tmp_path)

    assert len(violations) == 1
    assert violations[0].code == "PYPROJECT_QUALITY"
    # The families added by QTS-FINAL-010 are reported as missing.
    assert "TRY" in violations[0].message
    assert "DTZ" in violations[0].message
