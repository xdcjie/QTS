"""QTS-FINAL-014 guardrail: domain order side fields must be typed OrderSide."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import OrderDomainTypingRule


def _check(source: str) -> list[str]:
    tree = ast.parse(source)
    violations = OrderDomainTypingRule().check(
        relative_path=Path("backend/src/qts/domain/orders/sample.py"),
        qts_relative_path=Path("domain/orders/sample.py"),
        tree=tree,
    )
    return [v.message for v in violations]


def test_flags_str_side_field_in_domain_orders() -> None:
    source = "class Leg:\n    side: str\n    quantity: int\n"
    messages = _check(source)
    assert any("must be typed OrderSide" in message for message in messages)


def test_flags_optional_str_side_field() -> None:
    source = "class Leg:\n    side: str | None = None\n"
    assert _check(source)


def test_allows_order_side_typed_field() -> None:
    source = "class Leg:\n    side: OrderSide\n    quantity: int\n"
    assert _check(source) == []


def test_does_not_apply_outside_domain_orders() -> None:
    tree = ast.parse("class Leg:\n    side: str\n")
    violations = OrderDomainTypingRule().check(
        relative_path=Path("backend/src/qts/execution/sample.py"),
        qts_relative_path=Path("execution/sample.py"),
        tree=tree,
    )
    assert violations == []


def test_production_bracket_leg_passes_the_rule() -> None:
    path = Path("backend/src/qts/domain/orders/order_spec.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations = OrderDomainTypingRule().check(
        relative_path=path,
        qts_relative_path=Path("domain/orders/order_spec.py"),
        tree=tree,
    )
    assert violations == []
