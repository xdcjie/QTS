"""Strategy SDK context state-boundary guardrail (QTS-FINAL-005)."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

# State that must live in the focused subcontexts, not the StrategyContext facade.
_FORBIDDEN_OWNED_ATTRS = frozenset(
    {
        "_signals",
        "_cancel_intents",
        "_timer_subscriptions",
        "_subscription_registry",
        "_intent_emitter",
    }
)


class StrategyContextStateBoundaryRule:
    """Reject StrategyContext owning emission/state that belongs to its subcontexts.

    QTS-FINAL-005: StrategyContext is a compatibility facade. It may expose wrapper
    methods/properties but must not directly own ``_signals`` / ``_cancel_intents`` /
    ``_timer_subscriptions`` / ``_subscription_registry`` / ``_intent_emitter`` --
    those belong to SignalContext / TargetContext / TimerContext / SubscriptionContext.
    """

    code = "STRATEGY_CONTEXT_STATE_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag StrategyContext directly owning a subcontext-owned state attribute."""
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef) and node.name == "StrategyContext"):
                continue
            for owned in sorted(self._owned_attrs(node) & _FORBIDDEN_OWNED_ATTRS):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=node.lineno,
                        message=(
                            f"StrategyContext must not own '{owned}' directly; delegate it "
                            "to its subcontext (QTS-FINAL-005)"
                        ),
                    )
                )
        return violations

    @staticmethod
    def _owned_attrs(class_node: ast.ClassDef) -> set[str]:
        owned: set[str] = set()
        for statement in class_node.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                owned.add(statement.target.id)
            if isinstance(statement, ast.Assign):
                owned.update(t.id for t in statement.targets if isinstance(t, ast.Name))
            if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
                for inner in ast.walk(statement):
                    if not isinstance(inner, ast.Assign):
                        continue
                    for target in inner.targets:
                        if (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == "self"
                        ):
                            owned.add(target.attr)
        return owned


__all__ = ["StrategyContextStateBoundaryRule"]
