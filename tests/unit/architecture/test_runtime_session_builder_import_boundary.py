"""Runtime session assembly must not depend on the backtest package."""

from __future__ import annotations

import ast
from pathlib import Path


def test_runtime_session_builder_does_not_import_backtest() -> None:
    path = Path("backend/src/qts/application/services/runtime_session_builder.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offenders.extend(
                alias.name for alias in node.names if alias.name.startswith("qts.backtest")
            )
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            if node.module == "qts.backtest" or node.module.startswith("qts.backtest."):
                offenders.append(node.module)

    assert offenders == []
