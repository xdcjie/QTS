"""Public-boundary exception guardrail.

Public methods at the order-lifecycle execution boundary must signal business
failures with the domain exception taxonomy (``qts.execution.errors`` /
``qts.core.errors``), not raw ``ValueError`` / ``KeyError`` / ``RuntimeError``,
so callers and operators can react to the failure *kind*. Raw built-ins remain
acceptable inside immutable value-object field validation (``__post_init__``),
which this rule does not inspect because it only scans public (non-underscore)
methods.

Scope note: this rule currently enforces the canonical order-lifecycle boundary
(``execution/order_manager.py``). Extending it to the rest of
execution/runtime/application requires converting their public-method raises
(~100 sites, many of them straightforward argument validation) to the taxonomy;
that broader rollout is tracked separately.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

_RAW_BOUNDARY_ERRORS = frozenset({"ValueError", "KeyError", "RuntimeError"})

# Modules whose public methods must use the domain exception taxonomy.
_GUARDED_MODULES: frozenset[tuple[str, ...]] = frozenset(
    {
        ("execution", "order_manager.py"),
    }
)


class PublicBoundaryExceptionRule:
    """Reject raw built-in error raises in public order-lifecycle boundary methods."""

    code = "PUBLIC_BOUNDARY_EXCEPTION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag raw ValueError/KeyError/RuntimeError raises in public methods."""
        if qts_relative_path.parts not in _GUARDED_MODULES:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if node.name.startswith("_"):
                continue
            for raised in self._raw_raises_directly_in(node):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=raised.lineno,
                        message=(
                            f"public method {node.name} raises raw {raised.name}; use the domain "
                            "exception taxonomy (qts.execution.errors / qts.core.errors)"
                        ),
                    )
                )
        return violations

    @classmethod
    def _raw_raises_directly_in(
        cls, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Iterator[_RawRaise]:
        for statement in func.body:
            yield from cls._raw_raises(statement)

    @classmethod
    def _raw_raises(cls, node: ast.AST) -> Iterator[_RawRaise]:
        # Do not descend into nested function/class scopes; they are evaluated
        # under their own public/private classification.
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda):
            return
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
            func = node.exc.func
            name = func.id if isinstance(func, ast.Name) else ""
            if isinstance(func, ast.Attribute):
                name = func.attr
            if name in _RAW_BOUNDARY_ERRORS:
                yield _RawRaise(name=name, lineno=node.lineno)
        for child in ast.iter_child_nodes(node):
            yield from cls._raw_raises(child)


class _RawRaise:
    __slots__ = ("lineno", "name")

    def __init__(self, *, name: str, lineno: int) -> None:
        self.name = name
        self.lineno = lineno


__all__ = ["PublicBoundaryExceptionRule"]
