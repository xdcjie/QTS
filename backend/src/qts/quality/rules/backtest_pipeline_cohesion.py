"""Backtest pipeline cohesion guardrail.

``BacktestPipeline`` is an orchestration facade; dynamic strategy-module loading
belongs to ``StrategyLoader``. The pipeline module must therefore not import
``importlib`` / ``sys`` (the dynamic-import machinery), keeping that concern in
its owning loader.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation, _iter_imports

_PIPELINE_MODULE = ("backtest", "pipeline.py")
_FORBIDDEN_IMPORT_ROOTS = frozenset({"importlib", "sys"})


class BacktestPipelineCohesionRule:
    """Reject dynamic-import machinery (importlib/sys) in qts.backtest.pipeline."""

    code = "BACKTEST_PIPELINE_COHESION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag importlib/sys imports in the backtest pipeline facade."""
        if qts_relative_path.parts != _PIPELINE_MODULE:
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            root = imported_module.split(".", 1)[0]
            if root in _FORBIDDEN_IMPORT_ROOTS:
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=(
                            "BacktestPipeline must orchestrate, not load strategy modules; "
                            f"move dynamic-import use of {imported_module} into StrategyLoader"
                        ),
                    )
                )
        return violations


__all__ = ["BacktestPipelineCohesionRule"]
