"""Operations control-plane reality guardrail.

Operator commands must affect a real runtime, never shadow state (QTS-FINAL-001):

1. ``OperationsCommandHandler`` must route command effects through a
   ``RuntimeCommandExecutor`` and fail with ``RuntimeCommandNotBound`` when no
   runtime is bound, so a COMPLETED result reflects a real runtime effect.
2. ``api/routes/operations.py`` must not hold a module-global ``OperationsService``
   / idempotency-store singleton; routes resolve them through dependency injection
   so the service can be bound to a runtime at app construction.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation, _iter_imported_names

_HANDLER_MODULE = ("application", "services", "operations_command_handler.py")
_ROUTE_MODULE = ("api", "routes", "operations.py")
_FORBIDDEN_ROUTE_GLOBALS = frozenset({"_operations", "_idempotency"})
_REQUIRED_HANDLER_SYMBOLS = ("RuntimeCommandExecutor", "RuntimeCommandNotBound")


class OperationsCommandRealityRule:
    """Operator commands must hit a real runtime, not module-local shadow state."""

    code = "OPERATIONS_COMMAND_REALITY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Enforce executor routing in the handler and no module-global route state."""
        parts = qts_relative_path.parts
        if parts == _HANDLER_MODULE:
            return self._check_handler(relative_path, tree)
        if parts == _ROUTE_MODULE:
            return self._check_route(relative_path, tree)
        return []

    def _check_handler(self, relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]:
        imported = {name for _module, name, _line in _iter_imported_names(tree)}
        missing = [symbol for symbol in _REQUIRED_HANDLER_SYMBOLS if symbol not in imported]
        if not missing:
            return []
        return [
            GuardrailViolation(
                code=self.code,
                path=str(relative_path),
                line=1,
                message=(
                    "OperationsCommandHandler must route command effects through a real runtime: "
                    f"missing {', '.join(missing)}. A COMPLETED operator command must reflect a "
                    "RuntimeSession effect (or raise RuntimeCommandNotBound), not shadow state."
                ),
            )
        ]

    def _check_route(self, relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]:
        module = tree if isinstance(tree, ast.Module) else None
        if module is None:
            return []
        violations: list[GuardrailViolation] = []
        for node in module.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in _FORBIDDEN_ROUTE_GLOBALS:
                    violations.append(
                        GuardrailViolation(
                            code=self.code,
                            path=str(relative_path),
                            line=node.lineno,
                            message=(
                                f"operations routes must not hold a module-global {target.id!r}; "
                                "resolve OperationsService / idempotency via FastAPI dependency "
                                "injection so the control plane can be bound to a real runtime"
                            ),
                        )
                    )
        return violations


__all__ = ["OperationsCommandRealityRule"]
