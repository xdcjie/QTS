"""Runtime private-attribute access guardrail.

Safety-critical ``RuntimeSession`` state must be reached only through the
``RuntimeSafetySessionPort`` / ``RuntimeSafetyState`` boundary, never poked as a
loose private attribute from another module. This rule locks the kill-switch
state encapsulation (QTS-FINAL-012): no module other than the session owner and
the safety-port owner may reference the ``_kill_switch_active`` attribute.

Scope note: the broader goal -- coordinators depending on narrow ports rather
than any ``RuntimeSession`` private attribute -- requires migrating the
remaining runtime coordinators (market data, recovery, supervision) to ports.
That migration is tracked separately; this rule enforces the safety-critical
subset that issue 012 encapsulates, and is structured so additional encapsulated
attributes can be added as those ports land.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

# RuntimeSession private attributes that are now owned behind RuntimeSafetyState
# and must only be reached through the safety port.
_ENCAPSULATED_SESSION_ATTRS = frozenset({"_kill_switch_active"})

# Modules permitted to define/own the encapsulated state.
_OWNER_MODULES: frozenset[tuple[str, ...]] = frozenset(
    {
        ("runtime", "session.py"),
        ("runtime", "safety_port.py"),
    }
)


class RuntimePrivateAccessRule:
    """Forbid external modules from referencing encapsulated RuntimeSession state."""

    code = "RUNTIME_PRIVATE_ACCESS"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag references to encapsulated RuntimeSession safety attributes."""
        if qts_relative_path.parts[:1] == ("quality",):
            return []
        if qts_relative_path.parts in _OWNER_MODULES:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            attr = self._encapsulated_attr(node)
            if attr is None:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=self._node_line(node),
                    message=(
                        f"{attr} is encapsulated RuntimeSession safety state; reach it through "
                        "RuntimeSafetySessionPort / RuntimeSafetyState, not as a private attribute"
                    ),
                )
            )
        return violations

    @staticmethod
    def _encapsulated_attr(node: ast.AST) -> str | None:
        if isinstance(node, ast.Attribute) and node.attr in _ENCAPSULATED_SESSION_ATTRS:
            return node.attr
        return None

    @staticmethod
    def _node_line(node: ast.AST) -> int:
        try:
            return int(object.__getattribute__(node, "lineno"))
        except AttributeError:
            return 1


__all__ = ["RuntimePrivateAccessRule"]
