"""Stale guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    STALE_ARCHITECTURE_TEXT,
    GuardrailViolation,
    _iter_architecture_text_paths,
    _line_number_containing,
)


class ProductionNoFakeClassRule:
    """Reject fake classes from production packages."""

    code = "PRODUCTION_FAKE_CLASS"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag ``Fake``-prefixed classes defined in production packages."""
        if qts_relative_path.parts[:1] in {("testing",), ("quality",)}:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Fake"):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=node.lineno,
                        message="test fakes belong under qts.testing or tests/support",
                    )
                )
        return violations


class StaleArchitectureTextRule:
    """Reject stale architecture wording from M0 guarded documents."""

    code = "STALE_ARCHITECTURE_TEXT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Skip per-file analysis; this rule runs only repository-wide."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Flag stale architecture wording in guarded documents."""
        violations: list[GuardrailViolation] = []
        for relative_path in _iter_architecture_text_paths(repo_root):
            path = repo_root / relative_path
            source = path.read_text(encoding="utf-8")
            for token, guidance in STALE_ARCHITECTURE_TEXT.items():
                line = _line_number_containing(source, token)
                if line is None:
                    continue
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=f"stale architecture text is not allowed: {token}",
                        remediation=guidance,
                        symbol=token,
                    )
                )
        return violations


__all__ = ["ProductionNoFakeClassRule", "StaleArchitectureTextRule"]
