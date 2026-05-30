"""Oop guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import cast

from qts.quality.guardrails import (
    GuardrailViolation,
    _check_backtest_actor_loop_cohesion,
    _check_backtest_engine_cohesion,
    _check_backtest_input_cohesion,
    _check_backtest_runner_cohesion,
)

OOP_FACTORY_FUNCTION_PREFIXES = ("build_", "create_", "load_", "make_")
OOP_CLASS_OWNED_HELPER_PREFIXES = (
    "_apply",
    "_map",
    "_normalize",
    "_parse",
    "_render",
    "_require",
    "_select",
    "_validate",
)
OOP_PUBLIC_FACTORY_ALLOWED = frozenset(
    {
        ("api/app.py", "create_app"),  # FastAPI framework entrypoint.
        ("observability/logging.py", "build_log_record"),  # pure DTO transformation.
    }
)
OOP_HELPER_OWNERSHIP_ALLOWED_FILES = frozenset(
    {
        "config/ibkr.py",
        "data/bars/alignment.py",
        "data/sessions/filter.py",
        "observability/logging.py",
    }
)


class OOPPublicFactoryRule:
    """Reject module-level public factory names on stable concepts."""

    code = "OOP_PUBLIC_FACTORY_FUNCTION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for module-level public factory functions on stable concepts."""
        return _check_oop_public_factory_functions(relative_path, qts_relative_path, tree)


class OOPHelperOwnershipRule:
    """Reject helper ownership violations that should stay private."""

    code = "OOP_HELPER_OWNERSHIP"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for module-private helpers that a public class should own."""
        return _check_oop_helper_ownership(relative_path, qts_relative_path, tree)


def _check_oop_public_factory_functions(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    module_path = qts_relative_path.as_posix()
    violations: list[GuardrailViolation] = []
    module = cast(ast.Module, tree)
    for node in module.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        if not node.name.startswith(OOP_FACTORY_FUNCTION_PREFIXES):
            continue
        if (module_path, node.name) in OOP_PUBLIC_FACTORY_ALLOWED:
            continue
        violations.append(
            GuardrailViolation(
                code="OOP_PUBLIC_FACTORY_FUNCTION",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "stable concept construction belongs on the owning class or config object, "
                    f"not module-level factory function {node.name}"
                ),
            )
        )
    return violations


def _check_oop_helper_ownership(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    module_path = qts_relative_path.as_posix()
    if module_path in OOP_HELPER_OWNERSHIP_ALLOWED_FILES:
        return []
    module = cast(ast.Module, tree)
    public_classes = [
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    ]
    public_functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    ]
    private_functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("_")
    ]
    if public_functions or not private_functions:
        return []
    if len(public_classes) == 1:
        return [
            GuardrailViolation(
                code="OOP_HELPER_OWNERSHIP",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "module-private helper next to a single public class should be owned by "
                    f"{public_classes[0].name}: {node.name}"
                ),
            )
            for node in private_functions
        ]
    if len(public_classes) < 2:
        return []
    violations: list[GuardrailViolation] = []
    for node in private_functions:
        if not node.name.startswith(OOP_CLASS_OWNED_HELPER_PREFIXES):
            continue
        owner_classes = [
            class_node.name
            for class_node in public_classes
            if _node_references_name(class_node, node.name)
        ]
        if len(owner_classes) != 1:
            continue
        violations.append(
            GuardrailViolation(
                code="OOP_HELPER_OWNERSHIP",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "module-private helper used by one public class should be owned by "
                    f"{owner_classes[0]}: {node.name}"
                ),
            )
        )
    return violations


def _node_references_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id == name
        for child in ast.walk(node)
    )


class BacktestRunnerCohesionRule:
    """Reject replay input assembly inside backtest runner."""

    code = "BACKTEST_RUNNER_COHESION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for replay input assembly leaking into the backtest runner."""
        return _check_backtest_runner_cohesion(relative_path, qts_relative_path, tree)


class BacktestInputCohesionRule:
    """Reject catalog/data construction inside backtest input builder."""

    code = "BACKTEST_INPUT_COHESION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for catalog/data construction inside the backtest input builder."""
        return _check_backtest_input_cohesion(relative_path, qts_relative_path, tree)


class BacktestEngineCohesionRule:
    """Reject historical replay assembly inside backtest engine."""

    code = "BACKTEST_ENGINE_COHESION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for historical replay assembly inside the backtest engine."""
        return _check_backtest_engine_cohesion(relative_path, qts_relative_path, tree)


class BacktestActorLoopCohesionRule:
    """Reject input assembly and report ownership inside the backtest actor loop."""

    code = "BACKTEST_ACTOR_LOOP_COHESION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for input assembly or report ownership in the backtest actor loop."""
        return _check_backtest_actor_loop_cohesion(relative_path, qts_relative_path, tree)


__all__ = [
    "OOPPublicFactoryRule",
    "OOPHelperOwnershipRule",
    "BacktestRunnerCohesionRule",
    "BacktestInputCohesionRule",
    "BacktestEngineCohesionRule",
    "BacktestActorLoopCohesionRule",
]
