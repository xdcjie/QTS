"""Imports guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    PROVIDER_SDK_ALLOWED_PREFIXES,
    REMOVED_IMPORT_MODULES,
    REMOVED_IMPORT_SYMBOLS,
    REMOVED_IMPORT_WILDCARD_MODULES,
    GuardrailViolation,
    _check_import,
    _has_allowed_prefix,
    _is_provider_sdk_module,
    _iter_imported_names,
    _iter_imports,
)


class ImportBoundaryRule:
    """Validate package import boundary direction and adapter constraints."""

    code = "IMPORT_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for imports that cross package boundaries in the wrong direction."""
        if qts_relative_path.parts[:1] == ("quality",):
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            violations.extend(
                _check_import(relative_path, qts_relative_path, imported_module, line)
            )
        return violations


class ProviderSdkImportRule:
    """Reject provider SDK imports outside adapter and transport boundaries."""

    code = "PROVIDER_SDK_IMPORT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for provider SDK imports outside adapter/transport boundaries."""
        if _has_allowed_prefix(qts_relative_path, PROVIDER_SDK_ALLOWED_PREFIXES):
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            if not _is_provider_sdk_module(imported_module):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=(
                        "provider SDK imports must stay inside adapter or transport boundaries: "
                        f"{imported_module}"
                    ),
                )
            )
        return violations


class ProductionNoTestingImportRule:
    """Reject production imports from qts.testing."""

    code = "PRODUCTION_TESTING_IMPORT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for production code importing from qts.testing."""
        if qts_relative_path.parts[:1] in {("testing",), ("quality",)}:
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            if not imported_module.startswith("qts.testing"):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=f"production code must not import qts.testing: {imported_module}",
                )
            )
        return violations


class RemovedImportNoNewUsageRule:
    """Reject imports from removed module paths."""

    code = "REMOVED_IMPORT_USAGE"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Return violations for imports referencing removed module paths or symbols."""
        violations: list[GuardrailViolation] = []
        imported_name_lines: set[tuple[str, int]] = set()
        for imported_module, imported_name, line in _iter_imported_names(tree):
            if (
                imported_module not in REMOVED_IMPORT_WILDCARD_MODULES
                and (
                    imported_module,
                    imported_name,
                )
                not in REMOVED_IMPORT_SYMBOLS
            ):
                continue
            imported_name_lines.add((imported_module, line))
            symbol = f"{imported_module}.{imported_name}"
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=f"removed import name is not allowed: {symbol}",
                    symbol=symbol,
                )
            )
        for imported_module, line in _iter_imports(tree):
            if imported_module not in REMOVED_IMPORT_MODULES:
                continue
            if (imported_module, line) in imported_name_lines:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=f"removed import path is not allowed: {imported_module}",
                    symbol=imported_module,
                )
            )
        return violations


__all__ = [
    "ImportBoundaryRule",
    "ProviderSdkImportRule",
    "ProductionNoTestingImportRule",
    "RemovedImportNoNewUsageRule",
]
