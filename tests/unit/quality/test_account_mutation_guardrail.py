"""Gate tests for the account-fill mutation guardrail (DR-021)."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules.account_mutation import AccountFillMutationRule

_SOURCE = """
from qts.runtime.actors.account_actor import ApplyFill


def route(fill):
    return ApplyFill(fill=fill, currency="USD", multiplier=1)
"""


def _check(source: str, qts_rel: str) -> list:
    rule = AccountFillMutationRule()
    return rule.check(
        relative_path=Path("backend/src/qts") / qts_rel,
        qts_relative_path=Path(qts_rel),
        tree=ast.parse(source),
    )


def test_non_actor_module_constructing_apply_fill_is_flagged() -> None:
    violations = _check(_SOURCE, "runtime/execution_report_handler.py")
    assert violations
    assert all(v.code == "ACCOUNT_FILL_MUTATION" for v in violations)
    # Both the import and the construction are flagged.
    assert len(violations) >= 2


def test_actor_module_may_apply_fills() -> None:
    assert _check(_SOURCE, "runtime/actors/order_manager_actor.py") == []


def test_real_execution_report_handler_has_no_account_mutation() -> None:
    path = Path("backend/src/qts/runtime/execution_report_handler.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rule = AccountFillMutationRule()
    assert (
        rule.check(
            relative_path=path,
            qts_relative_path=Path("runtime/execution_report_handler.py"),
            tree=tree,
        )
        == []
    )
