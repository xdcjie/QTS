"""Pyproject quality-policy guardrail.

The project standard mandates a baseline set of ruff rule families (correctness,
naming, simplification, comprehensions, no-print, timezone-aware datetimes,
exception style, and Ruff-native checks). This rule fails when ``pyproject.toml``
drops any required family from ``tool.ruff.lint.select``, so the linting policy
cannot silently weaken (QTS-FINAL-010).
"""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

REQUIRED_RUFF_FAMILIES: tuple[str, ...] = (
    "E",
    "F",
    "I",
    "B",
    "UP",
    "N",
    "SIM",
    "C4",
    "T20",
    "DTZ",
    "TRY",
    "RUF",
)


class PyprojectQualityRule:
    """Require the mandated ruff rule families in ``tool.ruff.lint.select``."""

    code = "PYPROJECT_QUALITY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return no per-file violations; this rule inspects the repository root."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Flag any required ruff family missing from the pyproject select list."""
        pyproject = repo_root / "pyproject.toml"
        if not pyproject.exists():
            return []
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        select = data.get("tool", {}).get("ruff", {}).get("lint", {}).get("select", [])
        selected = set(select) if isinstance(select, list) else set()
        missing = [family for family in REQUIRED_RUFF_FAMILIES if family not in selected]
        if not missing:
            return []
        return [
            GuardrailViolation(
                code=self.code,
                path="pyproject.toml",
                line=1,
                message=(
                    "tool.ruff.lint.select must include the required quality families: "
                    + ", ".join(missing)
                ),
            )
        ]


__all__ = ["REQUIRED_RUFF_FAMILIES", "PyprojectQualityRule"]
