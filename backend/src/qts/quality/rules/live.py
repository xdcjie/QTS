"""Live guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    SHARED_DATA_LIVE_CONTRACT_CLASSES,
    GuardrailViolation,
    _iter_docstrings,
)


class LivePackageNoReplayClassRule:
    """Reject replay concepts in the live market-data package."""

    code = "LIVE_PACKAGE_REPLAY_CLASS"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag Replay-prefixed classes defined under the data/live package."""
        if qts_relative_path.parts[:2] != ("data", "live"):
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Replay"):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=node.lineno,
                        message=(
                            "replay market-data classes belong under data/sources or historical"
                        ),
                    )
                )
        return violations


class DataLiveNoSharedContractRule:
    """Reject shared market-data contracts from the live package."""

    code = "DATA_LIVE_SHARED_CONTRACT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag shared market-data contract classes defined under the data/live package."""
        if qts_relative_path.parts[:2] != ("data", "live"):
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if node.name not in SHARED_DATA_LIVE_CONTRACT_CLASSES:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=node.lineno,
                    message=(
                        "shared market-data contract class must live outside qts.data.live: "
                        f"{node.name}"
                    ),
                )
            )
        return violations


class SharedRuntimeWordingRule:
    """Reject mode-specific wording in shared runtime docstrings."""

    code = "SHARED_RUNTIME_WORDING"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag mode-specific wording in shared runtime docstrings."""
        if qts_relative_path.parts[:1] != ("runtime",):
            return []
        violations: list[GuardrailViolation] = []
        forbidden = (
            "backtest intent processing",
            "backtest orders",
            "beta only",
            "fake-adapter",
        )
        for node, docstring in _iter_docstrings(tree):
            normalized = docstring.lower()
            if not any(text in normalized for text in forbidden):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=self._node_line(node),
                    message="shared runtime docstrings must be mode-neutral",
                )
            )
        return violations

    @staticmethod
    def _node_line(node: ast.AST) -> int:
        try:
            return int(object.__getattribute__(node, "lineno"))
        except AttributeError:
            return 1


__all__ = [
    "DataLiveNoSharedContractRule",
    "LivePackageNoReplayClassRule",
    "SharedRuntimeWordingRule",
]
