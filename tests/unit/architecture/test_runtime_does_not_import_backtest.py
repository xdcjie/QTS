"""QTS-FINAL-003: runtime must never import the backtest layer.

``qts.runtime`` sits below ``qts.backtest`` in the dependency order, so any
import of ``qts.backtest`` from a runtime module -- including function-local /
deferred imports -- reintroduces an upward dependency. This locks both the
live codebase and the ``ImportBoundaryRule`` guardrail that enforces it.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import ImportBoundaryRule

RUNTIME_ROOT = Path("backend/src/qts/runtime")


def _imports(tree: ast.AST) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            modules.append(node.module)
    return modules


def test_no_runtime_module_imports_backtest() -> None:
    offenders: list[str] = []
    for path in sorted(RUNTIME_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for module in _imports(tree):
            if module == "qts.backtest" or module.startswith("qts.backtest."):
                offenders.append(f"{path}: {module}")
    assert offenders == []


def test_import_boundary_rule_flags_deferred_runtime_to_backtest_import() -> None:
    source = (
        "def build():\n"
        "    from qts.backtest.engine import BacktestEngine\n"
        "    return BacktestEngine\n"
    )
    tree = ast.parse(source)
    violations = ImportBoundaryRule().check(
        relative_path=Path("backend/src/qts/runtime/sample.py"),
        qts_relative_path=Path("runtime/sample.py"),
        tree=tree,
    )
    codes = {violation.code for violation in violations}
    assert "IMPORT_BOUNDARY" in codes
