"""Layer dependency guardrail: lower layers must not import the runtime layer."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

# Layers that sit below the runtime orchestration layer. None of them may take a
# runtime-time dependency on ``qts.runtime``; doing so reintroduces the upward
# coupling (and circular-import risk) that the actor model forbids.
LOWER_LAYERS_BELOW_RUNTIME: frozenset[tuple[str, ...]] = frozenset(
    {
        ("risk",),
        ("data",),
        ("portfolio",),
        ("execution",),
    }
)
RUNTIME_IMPORT_PREFIX = "qts.runtime"


class LayerDependencyRule:
    """Forbid risk/data/portfolio/execution modules from importing qts.runtime."""

    code = "LAYER_DEPENDENCY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag runtime imports from layers that sit below the runtime layer."""
        if qts_relative_path.parts[:1] not in LOWER_LAYERS_BELOW_RUNTIME:
            return []
        source_layer = qts_relative_path.parts[0]
        type_checking_lines = self._type_checking_lines(tree)
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            modules: tuple[tuple[str, int], ...]
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
                modules = ((node.module, node.lineno),)
            elif isinstance(node, ast.Import):
                modules = tuple((alias.name, node.lineno) for alias in node.names)
            else:
                continue
            for imported_module, line in modules:
                if not self._is_runtime_import(imported_module):
                    continue
                if line in type_checking_lines:
                    continue
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=(
                            f"{source_layer} must not import the runtime layer: {imported_module}"
                        ),
                    )
                )
        return violations

    @staticmethod
    def _type_checking_lines(tree: ast.AST) -> set[int]:
        """Return line numbers contained inside ``if TYPE_CHECKING:`` blocks.

        Type-only imports are erased at runtime, create no import cycle, and do
        not constitute a runtime layering dependency, so they are excluded from
        the upward-import check.
        """
        lines: set[int] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            test = node.test
            is_type_checking = (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
                isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"
            )
            if not is_type_checking:
                continue
            for inner in ast.walk(node):
                line = getattr(inner, "lineno", None)
                if line is not None:
                    lines.add(line)
        return lines

    @staticmethod
    def _is_runtime_import(imported_module: str) -> bool:
        return imported_module == RUNTIME_IMPORT_PREFIX or imported_module.startswith(
            f"{RUNTIME_IMPORT_PREFIX}."
        )


__all__ = ["LayerDependencyRule"]
