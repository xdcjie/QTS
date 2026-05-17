"""Oop guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    GuardrailViolation,
    _check_backtest_actor_loop_cohesion,
    _check_backtest_engine_cohesion,
    _check_backtest_input_cohesion,
    _check_backtest_runner_cohesion,
    _check_oop_helper_ownership,
    _check_oop_public_factory_functions,
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
        """Perform check."""
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
        """Perform check."""
        return _check_oop_helper_ownership(relative_path, qts_relative_path, tree)


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
        """Perform check."""
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
        """Perform check."""
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
        """Perform check."""
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
        """Perform check."""
        return _check_backtest_actor_loop_cohesion(relative_path, qts_relative_path, tree)


__all__ = [
    "OOPPublicFactoryRule",
    "OOPHelperOwnershipRule",
    "BacktestRunnerCohesionRule",
    "BacktestInputCohesionRule",
    "BacktestEngineCohesionRule",
    "BacktestActorLoopCohesionRule",
]
