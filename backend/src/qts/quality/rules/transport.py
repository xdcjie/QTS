"""Transport guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    GuardrailViolation,
    _iter_imports,
)


class TransportCanonicalPathRule:
    """Reject transport class definitions from adapter packages."""

    code = "TRANSPORT_CANONICAL_PATH"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag Transport-suffixed class definitions inside adapter packages."""
        if qts_relative_path.parts[:2] not in {
            ("data", "adapters"),
            ("execution", "adapters"),
        }:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not node.name.endswith("Transport"):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=node.lineno,
                    message=(
                        "transport class canonical definitions belong under transports: "
                        f"{node.name}"
                    ),
                )
            )
        return violations


class TransportAdapterImportRule:
    """Reject transport modules importing adapter implementations."""

    code = "TRANSPORT_ADAPTER_IMPORT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag transport modules importing adapter implementation modules."""
        if len(qts_relative_path.parts) < 3 or qts_relative_path.parts[1] != "transports":
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            imported_parts = imported_module.split(".")
            if len(imported_parts) < 4:
                continue
            if imported_parts[0] != "qts" or imported_parts[2] != "adapters":
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=(
                        "transport modules must not import adapter implementations: "
                        f"{imported_module}"
                    ),
                )
            )
        return violations


__all__ = ["TransportCanonicalPathRule", "TransportAdapterImportRule"]
