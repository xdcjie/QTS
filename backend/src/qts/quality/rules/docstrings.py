"""Docstring guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation


class ProductionPlaceholderDocstringRule:
    """Reject placeholder docstrings in production code."""

    code = "PLACEHOLDER_DOCSTRING"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if qts_relative_path.parts[:1] == ("quality",):
            return []
        violations: list[GuardrailViolation] = []
        for node, docstring in self._iter_docstrings(tree):
            if "placeholder" not in docstring.lower():
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=getattr(node, "lineno", 1),
                    message="production docstrings must describe the artifact contract",
                )
            )
        return violations

    @staticmethod
    def _iter_docstrings(tree: ast.AST) -> list[tuple[ast.AST, str]]:
        docstrings: list[tuple[ast.AST, str]] = []
        for node in ast.walk(tree):
            if not isinstance(
                node,
                ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
            ):
                continue
            docstring = ast.get_docstring(node)
            if docstring is not None:
                docstrings.append((node, docstring))
        return docstrings
