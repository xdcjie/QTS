"""Gate tests for the StrategyContext state-boundary guardrail (QTS-FINAL-005).

StrategyContext is a compatibility facade after QTS-FINAL-005: it may expose
wrapper methods/properties but must not directly own the SDK state that now
belongs to its focused subcontexts. This rule keeps that boundary enforced so a
future edit cannot quietly re-grow the god object.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation
from qts.quality.rules.strategy_context_boundary import StrategyContextStateBoundaryRule

_REL = "strategy_sdk/context.py"


def _check(source: str) -> list[GuardrailViolation]:
    rule = StrategyContextStateBoundaryRule()
    return rule.check(
        relative_path=Path("backend/src/qts") / _REL,
        qts_relative_path=Path(_REL),
        tree=ast.parse(source),
    )


def test_facade_owning_forbidden_state_in_method_is_flagged() -> None:
    source = """
class StrategyContext:
    def __init__(self):
        self._signals = []
        self._cancel_intents = []
"""
    violations = _check(source)
    assert {v.code for v in violations} == {"STRATEGY_CONTEXT_STATE_BOUNDARY"}
    flagged = {v.message.split("'")[1] for v in violations}
    assert flagged == {"_signals", "_cancel_intents"}


def test_facade_owning_forbidden_state_as_class_attr_is_flagged() -> None:
    source = """
class StrategyContext:
    _timer_subscriptions: list = []
    _intent_emitter = None
"""
    flagged = {v.message.split("'")[1] for v in _check(source)}
    assert flagged == {"_timer_subscriptions", "_intent_emitter"}


def test_wrapper_only_facade_passes() -> None:
    # Delegating to subcontexts (no forbidden owned state) is allowed.
    source = """
class StrategyContext:
    def __init__(self):
        self.target = object()
        self.signal = object()

    def drain_intents(self):
        return self.target.drain_intents()
"""
    assert _check(source) == []


def test_real_strategy_context_facade_passes() -> None:
    path = Path("backend/src/qts/strategy_sdk/context.py")
    rule = StrategyContextStateBoundaryRule()
    assert (
        rule.check(
            relative_path=path,
            qts_relative_path=Path(_REL),
            tree=ast.parse(path.read_text(encoding="utf-8")),
        )
        == []
    )
