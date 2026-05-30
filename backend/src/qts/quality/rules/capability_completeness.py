"""Capability-completeness guardrail for runtime order commands.

A public runtime order-command (SubmitOrder / CancelOrder / ReplaceOrder) is only
honest if the execution boundary can actually carry it out: the
``ExecutionAdapter`` protocol must declare a corresponding method. Exporting a
command whose adapter method does not exist reproduces the QTS-FINAL-007 defect
where ``ReplaceOrder`` was a public command with no execution path. This rule
fails when a known command's required ``ExecutionAdapter`` method is missing from
the protocol contract.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

_EXECUTION_ADAPTER_MODULE = ("execution", "execution_adapter.py")
_ADAPTER_PROTOCOL = "ExecutionAdapter"

# Runtime order command -> the ExecutionAdapter method that carries it out.
RUNTIME_COMMAND_ADAPTER_METHODS: dict[str, str] = {
    "SubmitOrder": "execute_market_order",
    "CancelOrder": "cancel_order",
    "ReplaceOrder": "replace_order",
}


class CapabilityCompletenessRule:
    """Require an ExecutionAdapter method for every public runtime order command."""

    code = "CAPABILITY_COMPLETENESS"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag runtime order commands whose ExecutionAdapter method is missing."""
        if qts_relative_path.parts != _EXECUTION_ADAPTER_MODULE:
            return []
        protocol = self._find_class(tree, _ADAPTER_PROTOCOL)
        if protocol is None:
            return [
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=1,
                    message=(
                        f"{_ADAPTER_PROTOCOL} protocol is missing; runtime order commands "
                        "have no execution boundary contract"
                    ),
                )
            ]
        methods = {
            node.name
            for node in protocol.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        }
        violations: list[GuardrailViolation] = []
        for command, method in sorted(RUNTIME_COMMAND_ADAPTER_METHODS.items()):
            if method not in methods:
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=protocol.lineno,
                        message=(
                            f"runtime command {command!r} requires ExecutionAdapter.{method}; "
                            "add the method or remove the command from the public surface"
                        ),
                    )
                )
        return violations

    @staticmethod
    def _find_class(tree: ast.AST, name: str) -> ast.ClassDef | None:
        module = tree if isinstance(tree, ast.Module) else None
        if module is None:
            return None
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == name:
                return node
        return None


__all__ = ["RUNTIME_COMMAND_ADAPTER_METHODS", "CapabilityCompletenessRule"]
