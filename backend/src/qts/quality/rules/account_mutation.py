"""Account-fill mutation guardrail: only actors may apply fills to account state."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

# ``ApplyFill`` is the message that mutates AccountActor cash/holdings. Only the
# actor layer (the account actor that owns the state, and the order-manager actor
# that routes fills to it) may import or construct it. Any non-actor collaborator
# -- e.g. ExecutionReportHandler -- constructing ApplyFill reintroduces the
# cross-boundary account mutation the actor model forbids.
_APPLY_FILL = "ApplyFill"
_ACTOR_PACKAGE_PREFIX = ("runtime", "actors")


class AccountFillMutationRule:
    """Forbid non-actor modules from importing or constructing ``ApplyFill``."""

    code = "ACCOUNT_FILL_MUTATION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag ApplyFill import/construction outside the actor package."""
        if qts_relative_path.parts[: len(_ACTOR_PACKAGE_PREFIX)] == _ACTOR_PACKAGE_PREFIX:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            line = self._apply_fill_line(node)
            if line is not None:
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=(
                            "only actors may apply fills to account state; non-actor module "
                            "must not import or construct ApplyFill"
                        ),
                    )
                )
        return violations

    @staticmethod
    def _apply_fill_line(node: ast.AST) -> int | None:
        """Return the line of an ApplyFill import or construction, if any."""
        if isinstance(node, ast.ImportFrom):
            if any(alias.name == _APPLY_FILL for alias in node.names):
                return node.lineno
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == _APPLY_FILL:
                return node.lineno
            if isinstance(func, ast.Attribute) and func.attr == _APPLY_FILL:
                return node.lineno
        return None


__all__ = ["AccountFillMutationRule"]
