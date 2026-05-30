"""QTS-FINAL-008 guardrail: order-lifecycle public methods avoid raw built-ins.

``PublicBoundaryExceptionRule`` flags raw ValueError/KeyError/RuntimeError raised
from public methods of the order-lifecycle boundary, while leaving value-object
field validation (``__post_init__``) untouched.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import PublicBoundaryExceptionRule


def _check(qts_relative: str, source: str) -> list[str]:
    tree = ast.parse(source)
    violations = PublicBoundaryExceptionRule().check(
        relative_path=Path("backend/src/qts") / qts_relative,
        qts_relative_path=Path(qts_relative),
        tree=tree,
    )
    return [v.message for v in violations]


def test_flags_raw_value_error_in_public_method() -> None:
    source = "class OrderManager:\n    def create_order(self):\n        raise ValueError('nope')\n"
    messages = _check("execution/order_manager.py", source)
    assert any("create_order" in m and "ValueError" in m for m in messages)


def test_allows_raw_error_in_post_init_validation() -> None:
    source = (
        "class Spec:\n    def __post_init__(self):\n        raise ValueError('field invalid')\n"
    )
    assert _check("execution/order_manager.py", source) == []


def test_allows_domain_error_in_public_method() -> None:
    source = (
        "class OrderManager:\n"
        "    def create_order(self):\n"
        "        raise RiskRejectedOrder('nope')\n"
    )
    assert _check("execution/order_manager.py", source) == []


def test_does_not_apply_outside_guarded_modules() -> None:
    source = "class C:\n    def go(self):\n        raise ValueError('x')\n"
    assert _check("execution/broker.py", source) == []


def test_production_order_manager_passes_the_rule() -> None:
    path = Path("backend/src/qts/execution/order_manager.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations = PublicBoundaryExceptionRule().check(
        relative_path=path,
        qts_relative_path=Path("execution/order_manager.py"),
        tree=tree,
    )
    assert violations == []
