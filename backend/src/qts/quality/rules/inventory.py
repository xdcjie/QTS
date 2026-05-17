"""Inventory guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.guardrails import (
    CLASS_INVENTORY_BASELINE_PATH,
    PLATFORM_FREEZE_EXCEPTIONS_PATH,
    PLATFORM_FREEZE_RULE_KEY,
    GuardrailViolation,
    _class_inventory_baseline_optional,
    _class_inventory_parse_violations,
    _is_dto_or_value_object_name,
    _is_platform_freeze_module,
    _is_public_class,
    _iter_top_level_classes,
    _load_class_inventory_baseline,
    _load_platform_freeze_config,
    _ProductionClassEntry,
    _scan_production_classes,
)


class PlatformFreezeRule:
    """Reject new production classes in frozen platform packages without exception."""

    code = PLATFORM_FREEZE_RULE_KEY

    def __init__(self, repo_root: Path | None = None) -> None:
        self._config = _load_platform_freeze_config(repo_root or Path("."))

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if not _is_platform_freeze_module(qts_relative_path):
            return []
        if self._config.parse_violations:
            return []
        module_name = "qts." + qts_relative_path.with_suffix("").as_posix().replace("/", ".")
        violations: list[GuardrailViolation] = []
        for node in _iter_top_level_classes(tree):
            if not _is_public_class(node):
                continue
            key = (module_name, node.name)
            if key in self._config.allowed_exceptions:
                continue
            if key in self._config.expired_exceptions:
                message = (
                    f"platform freeze exception has expired for {module_name}.{node.name}; "
                    "add a fresh allowlisted exception with future expiry"
                )
            else:
                message = (
                    f"new production class is not allowed in frozen package without an "
                    f"unexpired exception entry in {PLATFORM_FREEZE_EXCEPTIONS_PATH}: "
                    f"{node.name}"
                )
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=node.lineno,
                    message=message,
                    symbol=f"{module_name}.{node.name}",
                )
            )
        return violations

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-level check."""
        del repo_root
        violations: list[GuardrailViolation] = []
        for line, message in self._config.parse_violations:
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(PLATFORM_FREEZE_EXCEPTIONS_PATH),
                    line=line,
                    message=message,
                )
            )
        return violations


class ClassInventoryBudgetRule:
    """Reject production class growth outside the platform class inventory baseline."""

    code = "CLASS_INVENTORY_BUDGET"

    def __init__(self, repo_root: Path | None = None) -> None:
        self._baseline = _load_class_inventory_baseline(repo_root or Path("."))

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        if _class_inventory_baseline_optional(repo_root) and self._baseline is None:
            return []
        if self._baseline is None:
            return [
                GuardrailViolation(
                    code=self.code,
                    path=str(CLASS_INVENTORY_BASELINE_PATH),
                    line=1,
                    message="missing class inventory baseline artifact",
                )
            ]
        parse_violations = _class_inventory_parse_violations(self.code, self._baseline)
        if parse_violations:
            return parse_violations

        classes = _scan_production_classes(repo_root)
        freeze_config = _load_platform_freeze_config(repo_root)
        violations: list[GuardrailViolation] = []
        for class_entry in classes:
            if class_entry.symbol in self._baseline.production_classes:
                continue
            module_name, class_name = class_entry.symbol.rsplit(".", 1)
            if (module_name, class_name) in freeze_config.allowed_exceptions:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(class_entry.relative_path),
                    line=class_entry.line,
                    message=(
                        "production class is outside the class inventory baseline "
                        "without an unexpired platform freeze exception"
                    ),
                    symbol=class_entry.symbol,
                )
            )
        if len(classes) <= self._baseline.production_class_count or not violations:
            return violations
        violations.append(
            GuardrailViolation(
                code=self.code,
                path=str(CLASS_INVENTORY_BASELINE_PATH),
                line=1,
                message=(
                    "production class count exceeds baseline: "
                    f"{len(classes)} > {self._baseline.production_class_count}"
                ),
            )
        )
        return violations


class SingleFieldDtoJustificationRule:
    """Require explicit boundary justification for single-field DTO/value objects."""

    code = "SINGLE_FIELD_DTO_JUSTIFICATION"

    def __init__(self, repo_root: Path | None = None) -> None:
        self._baseline = _load_class_inventory_baseline(repo_root or Path("."))

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        if _class_inventory_baseline_optional(repo_root) and self._baseline is None:
            return []
        if self._baseline is None:
            return [
                GuardrailViolation(
                    code=self.code,
                    path=str(CLASS_INVENTORY_BASELINE_PATH),
                    line=1,
                    message="missing class inventory baseline artifact",
                )
            ]
        parse_violations = _class_inventory_parse_violations(self.code, self._baseline)
        if parse_violations:
            return parse_violations

        violations: list[GuardrailViolation] = []
        for class_entry in _scan_production_classes(repo_root):
            if class_entry.field_count != 1:
                continue
            if not _is_dto_or_value_object_name(class_entry.name):
                continue
            if class_entry.symbol in self._baseline.single_field_boundary_justifications:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(class_entry.relative_path),
                    line=class_entry.line,
                    message=(
                        "single-field DTO/value object requires boundary justification "
                        f"in {CLASS_INVENTORY_BASELINE_PATH}"
                    ),
                    symbol=class_entry.symbol,
                )
            )
        return violations


class DuplicateDtoNameRule:
    """Reject duplicate DTO class names across application and runtime packages."""

    code = "DUPLICATE_DTO_NAME"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        by_name: dict[str, list[_ProductionClassEntry]] = {}
        for class_entry in _scan_production_classes(repo_root):
            if not class_entry.name.endswith("DTO"):
                continue
            if not (
                class_entry.qts_relative_path.parts[:1] == ("application",)
                or class_entry.qts_relative_path.parts[:1] == ("runtime",)
            ):
                continue
            by_name.setdefault(class_entry.name, []).append(class_entry)

        violations: list[GuardrailViolation] = []
        for name, entries in sorted(by_name.items()):
            packages = {entry.qts_relative_path.parts[0] for entry in entries}
            if not {"application", "runtime"} <= packages:
                continue
            symbols = ", ".join(sorted(entry.symbol for entry in entries))
            for entry in entries:
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(entry.relative_path),
                        line=entry.line,
                        message=(
                            f"DTO name {name} is duplicated across application and "
                            f"runtime: {symbols}"
                        ),
                        symbol=entry.symbol,
                    )
                )
        return violations


__all__ = [
    "PlatformFreezeRule",
    "ClassInventoryBudgetRule",
    "SingleFieldDtoJustificationRule",
    "DuplicateDtoNameRule",
]
