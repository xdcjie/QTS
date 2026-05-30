"""Order-domain typing guardrails.

Order direction must be modeled with the ``OrderSide`` enum, never a bare
``str``, so the domain order model cannot carry an unvalidated free-text side.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

_ORDER_DOMAIN_PREFIX = ("domain", "orders")
_SIDE_FIELD_NAMES = frozenset({"side"})


class OrderDomainTypingRule:
    """Require ``side`` fields in domain order models to be typed ``OrderSide``."""

    code = "ORDER_DOMAIN_TYPING"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag domain order ``side`` fields annotated as ``str``."""
        if qts_relative_path.parts[: len(_ORDER_DOMAIN_PREFIX)] != _ORDER_DOMAIN_PREFIX:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.AnnAssign) or not isinstance(item.target, ast.Name):
                    continue
                if item.target.id not in _SIDE_FIELD_NAMES:
                    continue
                if self._is_str_annotation(item.annotation):
                    violations.append(
                        GuardrailViolation(
                            code=self.code,
                            path=str(relative_path),
                            line=item.lineno,
                            message=(
                                f"{node.name}.{item.target.id} must be typed OrderSide, not str; "
                                "domain order direction is a closed enum, not free text"
                            ),
                        )
                    )
        return violations

    @staticmethod
    def _is_str_annotation(annotation: ast.expr) -> bool:
        if isinstance(annotation, ast.Name):
            return annotation.id == "str"
        # Optional/unioned str annotations (str | None, Optional[str]) also count.
        if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            return OrderDomainTypingRule._is_str_annotation(
                annotation.left
            ) or OrderDomainTypingRule._is_str_annotation(annotation.right)
        return False


__all__ = ["OrderDomainTypingRule"]
