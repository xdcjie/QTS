"""Public-surface guardrail for backtest modules.

Backtest modules orchestrate runtime actors but must not leak runtime actor
types through their public ``__all__`` surface. Re-exporting actor classes/
messages from, e.g., ``qts.backtest.engine`` turns the backtest layer into an
alternate import path for runtime internals; callers must import those from
``qts.runtime.actors`` directly.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation, _iter_imported_names

_BACKTEST_PREFIX = ("backtest",)
_RUNTIME_ACTOR_PREFIX = "qts.runtime.actors"


class PublicSurfaceRule:
    """Reject runtime-actor symbols in a backtest module's ``__all__``."""

    code = "PUBLIC_SURFACE"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag ``__all__`` entries imported from runtime actor modules."""
        if qts_relative_path.parts[:1] != _BACKTEST_PREFIX:
            return []
        exported = self._exported_names(tree)
        if not exported:
            return []
        actor_imports = {
            name: (module, line)
            for module, name, line in _iter_imported_names(tree)
            if module == _RUNTIME_ACTOR_PREFIX or module.startswith(f"{_RUNTIME_ACTOR_PREFIX}.")
        }
        violations: list[GuardrailViolation] = []
        for name in sorted(exported):
            if name not in actor_imports:
                continue
            module, line = actor_imports[name]
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=(
                        f"backtest module must not re-export runtime actor symbol {name!r} "
                        f"(imported from {module}) through __all__; import it from "
                        "qts.runtime.actors directly"
                    ),
                )
            )
        return violations

    @staticmethod
    def _exported_names(tree: ast.AST) -> set[str]:
        module = tree if isinstance(tree, ast.Module) else None
        if module is None:
            return set()
        names: set[str] = set()
        for node in module.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
            ):
                continue
            if isinstance(node.value, ast.List | ast.Tuple):
                for element in node.value.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        names.add(element.value)
        return names


__all__ = ["PublicSurfaceRule"]
