"""Anchor: CallerPresenceRule catches anchor-only production symbols.

Domain fact: a baseline-listed production symbol must have at least one
non-test caller, or be explicitly deferred via
``docs/plan/wiring_deferrals.md``. This closes the recurring "shipped but
unwired" anti-pattern surfaced by OPT-15, 17, 25, 26, 29.

Owner: ``qts.quality.rules.caller_presence.CallerPresenceRule`` +
``docs/plan/wiring_deferrals.md`` (deferrals registry).

Forbidden shortcut: skipping the rule for non-Protocol symbols without a
deferral entry; treating Protocol exemption as an unconditional wildcard.
"""

from __future__ import annotations

from pathlib import Path

from qts.quality.rules.caller_presence import CallerPresenceRule


def test_rule_passes_on_current_repository() -> None:
    """The current repo must satisfy CallerPresenceRule (or have deferrals)."""
    rule = CallerPresenceRule(repo_root=Path("."))
    violations = rule.check_repository(Path("."))
    assert violations == [], (
        "CallerPresenceRule flagged production symbols without callers; "
        "either add a non-test caller or add to wiring_deferrals.md.\n"
        + "\n".join(f"- {v.symbol or v.path}: {v.message}" for v in violations[:5])
    )


def test_protocol_is_recognized() -> None:
    """Protocol-decorated classes are auto-detected from the AST."""
    import ast

    source = """
from typing import Protocol

class MyProtocol(Protocol):
    def do_thing(self) -> int: ...

class RegularClass:
    pass
"""
    tree = ast.parse(source)
    classes_by_name = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert CallerPresenceRule._is_protocol_class(classes_by_name["MyProtocol"]) is True
    assert CallerPresenceRule._is_protocol_class(classes_by_name["RegularClass"]) is False
