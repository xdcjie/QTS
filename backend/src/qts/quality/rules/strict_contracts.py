"""Strict internal-contract guardrails."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation


class StrictCoreContractRule:
    """Reject runtime attribute probing in production QTS modules."""

    code = "STRICT_CORE_CONTRACT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag ``getattr``/``hasattr`` calls that weaken typed contracts."""
        _ = qts_relative_path
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            probe_name = self._attribute_probe_name(node)
            if probe_name is None:
                continue
            attribute_name = self._attribute_probe_attribute_name(node)
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=self._node_line(node),
                    message=(
                        "production QTS modules must call typed public contracts directly; "
                        f"do not probe attribute {attribute_name!r} with {probe_name}"
                    ),
                    symbol=f"{probe_name}:{attribute_name}",
                )
            )
        return violations

    @staticmethod
    def _attribute_probe_name(node: ast.Call) -> str | None:
        if not isinstance(node.func, ast.Name):
            return None
        if node.func.id in {"getattr", "hasattr"}:
            return node.func.id
        return None

    @staticmethod
    def _attribute_probe_attribute_name(node: ast.Call) -> str:
        if len(node.args) < 2:
            return ""
        attribute = node.args[1]
        if isinstance(attribute, ast.Constant) and isinstance(attribute.value, str):
            return attribute.value
        return ast.unparse(attribute)

    @staticmethod
    def _node_line(node: ast.AST) -> int:
        try:
            return int(object.__getattribute__(node, "lineno"))
        except AttributeError:
            return 1


__all__ = ["StrictCoreContractRule"]
