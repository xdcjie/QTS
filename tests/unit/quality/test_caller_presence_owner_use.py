"""Gate tests for the corrected caller-presence rule (C5a).

Two behaviours are locked:

1. A bare re-export (an ``import`` of a symbol, or its name in ``__all__``) must
   NOT count as a caller -- otherwise a symbol satisfies the gate purely by being
   forwarded from a package ``__init__``.
2. A symbol used by a co-located owner in its own module (a reference outside the
   symbol's own class body) DOES count -- the owner is the wiring signal
   (CLAUDE.md §11) -- while a self-reference inside the class body does not.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules.caller_presence import CallerPresenceRule


def _class_node(source: str, name: str) -> ast.ClassDef:
    tree = ast.parse(source)
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)


def test_caller_reference_source_strips_imports_and_all() -> None:
    source = 'from pkg import Foo\n__all__ = ["Foo"]\nbar = Foo()\n'
    scannable = CallerPresenceRule._caller_reference_source(source)
    assert "Foo()" in scannable  # the real use site is preserved
    assert "import" not in scannable  # the import line is stripped
    assert "__all__" not in scannable  # the re-export list is stripped


def test_owner_use_outside_class_body_counts(tmp_path: Path) -> None:
    source = (
        "class Helper:\n"
        "    pass\n"
        "\n"
        "class Owner:\n"
        "    def run(self) -> object:\n"
        "        return Helper()\n"  # co-located owner constructs Helper
    )
    module = tmp_path / "m.py"
    module.write_text(source, encoding="utf-8")
    node = _class_node(source, "Helper")
    assert CallerPresenceRule._defining_module_uses_symbol(module, node, "Helper") is True


def test_self_reference_inside_class_body_does_not_count(tmp_path: Path) -> None:
    source = (
        "class Helper:\n"
        "    @classmethod\n"
        "    def make(cls) -> object:\n"
        "        return Helper()\n"  # reference is inside Helper's own body
    )
    module = tmp_path / "m.py"
    module.write_text(source, encoding="utf-8")
    node = _class_node(source, "Helper")
    assert CallerPresenceRule._defining_module_uses_symbol(module, node, "Helper") is False


def test_import_and_all_in_defining_module_do_not_count_as_owner_use(tmp_path: Path) -> None:
    source = (
        'from elsewhere import Helper as _Helper\n__all__ = ["Helper"]\nclass Helper:\n    pass\n'
    )
    module = tmp_path / "m.py"
    module.write_text(source, encoding="utf-8")
    node = _class_node(source, "Helper")
    assert CallerPresenceRule._defining_module_uses_symbol(module, node, "Helper") is False
