"""Docstring guardrail rules."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

_PERFORM_PLACEHOLDER = re.compile(r"^Perform\b")


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
        """Flag placeholder docstrings: ``placeholder`` text or ``Perform <name>`` stubs."""
        in_quality = qts_relative_path.parts[:1] == ("quality",)
        violations: list[GuardrailViolation] = []
        for node, docstring in self._iter_docstrings(tree):
            # Auto-generated "Perform <name>." stubs describe nothing; reject
            # everywhere, including the quality package itself.
            if _PERFORM_PLACEHOLDER.match(docstring.strip()):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=self._node_line(node),
                        message=(
                            "production docstrings must describe the artifact contract, "
                            "not a generated 'Perform <name>' stub"
                        ),
                    )
                )
                continue
            # The "placeholder" substring check skips the quality package, whose
            # rule descriptions legitimately mention the word.
            if not in_quality and "placeholder" in docstring.lower():
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=self._node_line(node),
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

    @staticmethod
    def _node_line(node: ast.AST) -> int:
        try:
            return int(object.__getattribute__(node, "lineno"))
        except AttributeError:
            return 1
