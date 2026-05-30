"""Inventory guardrail rules."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from qts.quality.guardrails import (
    CLASS_INVENTORY_BASELINE_PATH,
    PLATFORM_FREEZE_EXCEPTIONS_PATH,
    PLATFORM_FREEZE_RULE_KEY,
    QTS_ROOT,
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

BACKEND_CLASS_BOUNDARY_MATRIX_PATH = Path(
    "docs/plan/backend_class_boundary_review_status_matrix.md"
)
BROAD_CLASS_SUFFIXES = ("Service", "Coordinator", "Manager", "Builder", "Source", "Adapter")
OWNERSHIP_DOCSTRING_VERBS = frozenset(
    {
        "own",
        "owns",
        "build",
        "builds",
        "adapt",
        "adapts",
        "resolve",
        "resolves",
        "coordinate",
        "coordinates",
        "run",
        "runs",
        "write",
        "writes",
        "load",
        "loads",
        "apply",
        "applies",
        "convert",
        "converts",
        "map",
        "maps",
        "normalize",
        "normalizes",
        "assemble",
        "assembles",
        "compute",
        "computes",
        "track",
        "tracks",
        "return",
        "returns",
        "start",
        "starts",
        "feed",
        "feeds",
    }
)
MATRIX_COLUMNS = (
    "Class",
    "Current lines",
    "Owner",
    "Risk",
    "Decision",
    "Target",
    "Evidence",
    "Status",
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
        """Flag new public classes in frozen platform modules lacking an unexpired exception."""
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
        """Surface parse errors in the platform freeze exceptions config as violations."""
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
        """Flag broad-suffix classes whose docstring first line lacks an ownership verb."""
        if qts_relative_path.parts[:1] in (("quality",), ("testing",)):
            return []
        module_name = "qts." + qts_relative_path.with_suffix("").as_posix().replace("/", ".")
        violations: list[GuardrailViolation] = []
        for node in _iter_top_level_classes(tree):
            if not _is_public_class(node):
                continue
            if not self._requires_ownership_docstring(module_name, node):
                continue
            first_line = _class_docstring_first_line(node)
            if _has_ownership_verb(first_line):
                continue
            violations.append(
                GuardrailViolation(
                    code="CLASS_OWNERSHIP_DOCSTRING",
                    path=str(relative_path),
                    line=node.lineno,
                    message=(
                        f"{node.name} uses a broad class suffix and its docstring first line "
                        "must include a clear ownership verb"
                    ),
                    symbol=f"{module_name}.{node.name}",
                )
            )
        return violations

    def _requires_ownership_docstring(self, module_name: str, node: ast.ClassDef) -> bool:
        if not node.name.endswith(BROAD_CLASS_SUFFIXES):
            return False
        if _is_protocol_class(node) or _is_small_boundary_value_class(node):
            return False
        return not (
            self._baseline is not None
            and f"{module_name}.{node.name}" in self._baseline.production_classes
        )

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Flag production classes growing beyond the inventory baseline or boundary matrix."""
        classes = _scan_production_classes(repo_root)
        violations = _class_boundary_matrix_violations(classes, repo_root)

        if _class_inventory_baseline_optional(repo_root) and self._baseline is None:
            return violations
        if self._baseline is None:
            return [
                *violations,
                GuardrailViolation(
                    code=self.code,
                    path=str(CLASS_INVENTORY_BASELINE_PATH),
                    line=1,
                    message="missing class inventory baseline artifact",
                ),
            ]
        parse_violations = _class_inventory_parse_violations(self.code, self._baseline)
        if parse_violations:
            return violations + parse_violations

        freeze_config = _load_platform_freeze_config(repo_root)
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


def _class_boundary_matrix_violations(
    classes: list[_ProductionClassEntry], repo_root: Path
) -> list[GuardrailViolation]:
    line_counts = _production_class_line_counts(repo_root)
    oversized_classes = [
        class_entry for class_entry in classes if line_counts.get(class_entry.symbol, 1) > 300
    ]
    if not oversized_classes:
        return []

    matrix_path = repo_root / BACKEND_CLASS_BOUNDARY_MATRIX_PATH
    matrix_rows, parse_violation = _load_backend_class_boundary_matrix(matrix_path)
    if parse_violation is not None:
        if parse_violation.startswith("missing "):
            return [
                GuardrailViolation(
                    code="CLASS_BOUNDARY_MATRIX",
                    path=str(class_entry.relative_path),
                    line=class_entry.line,
                    message=(
                        f"production class {class_entry.name} is over 300 lines "
                        f"({line_counts.get(class_entry.symbol, 1)}) and must be present in "
                        f"{BACKEND_CLASS_BOUNDARY_MATRIX_PATH}"
                    ),
                    symbol=class_entry.symbol,
                )
                for class_entry in oversized_classes
            ]
        return [
            GuardrailViolation(
                code="CLASS_BOUNDARY_MATRIX",
                path=str(BACKEND_CLASS_BOUNDARY_MATRIX_PATH),
                line=1,
                message=parse_violation,
            )
        ]

    violations: list[GuardrailViolation] = []
    for class_entry in oversized_classes:
        line_count = line_counts.get(class_entry.symbol, 1)
        row = matrix_rows.get(class_entry.name)
        if row is None:
            violations.append(
                GuardrailViolation(
                    code="CLASS_BOUNDARY_MATRIX",
                    path=str(class_entry.relative_path),
                    line=class_entry.line,
                    message=(
                        f"production class {class_entry.name} is over 300 lines "
                        f"({line_count}) and must be present in "
                        f"{BACKEND_CLASS_BOUNDARY_MATRIX_PATH}"
                    ),
                    symbol=class_entry.symbol,
                )
            )
            continue
        recorded_lines = _parse_recorded_lines(row.get("Current lines", ""))
        if recorded_lines is not None and _line_count_drifted(recorded_lines, line_count):
            violations.append(
                GuardrailViolation(
                    code="CLASS_BOUNDARY_MATRIX",
                    path=str(BACKEND_CLASS_BOUNDARY_MATRIX_PATH),
                    line=1,
                    message=(
                        f"production class {class_entry.name} matrix line count is stale "
                        f"(recorded {recorded_lines}, measured {line_count}); refresh the "
                        "'Current lines' cell so the retain/split decision reflects the "
                        "class's actual size"
                    ),
                    symbol=class_entry.symbol,
                )
            )
        if line_count <= 500:
            continue
        decision = row.get("Decision", "").lower()
        evidence = row.get("Evidence", "").strip()
        if ("split" in decision or "retain" in decision) and evidence:
            continue
        violations.append(
            GuardrailViolation(
                code="CLASS_BOUNDARY_MATRIX",
                path=str(BACKEND_CLASS_BOUNDARY_MATRIX_PATH),
                line=1,
                message=(
                    f"production class {class_entry.name} is over 500 lines "
                    f"({line_count}) and must have a split/retain decision "
                    "and evidence"
                ),
                symbol=class_entry.symbol,
            )
        )
    return violations


def _parse_recorded_lines(value: str) -> int | None:
    """Parse the leading integer from a matrix 'Current lines' cell, or None."""
    match = re.match(r"\s*(\d+)", value)
    return int(match.group(1)) if match else None


def _line_count_drifted(recorded: int, measured: int) -> bool:
    """Return whether the recorded matrix line count is stale vs the measured span.

    A class naturally grows and shrinks; the matrix is stale only when it drifts
    materially. The tolerance is the larger of 50 lines or 15% of the measured
    span, so small edits don't churn the matrix while a god-object that has
    quietly tripled (e.g. recorded 715, measured 2429) is caught.
    """
    tolerance = max(50, int(0.15 * measured))
    return abs(measured - recorded) > tolerance


def _production_class_line_counts(repo_root: Path) -> dict[str, int]:
    source_root = repo_root / QTS_ROOT
    if not source_root.exists():
        return {}
    line_counts: dict[str, int] = {}
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        qts_relative_path = path.relative_to(source_root)
        if qts_relative_path.parts[:1] == ("testing",):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path.relative_to(repo_root)))
        module_name = "qts." + qts_relative_path.with_suffix("").as_posix().replace("/", ".")
        for node in _iter_top_level_classes(tree):
            if not _is_public_class(node):
                continue
            line_counts[f"{module_name}.{node.name}"] = _class_line_count(node)
    return line_counts


def _class_line_count(node: ast.ClassDef) -> int:
    end_lineno = getattr(node, "end_lineno", None)
    if not isinstance(end_lineno, int):
        return 1
    return max(1, end_lineno - node.lineno + 1)


def _load_backend_class_boundary_matrix(
    path: Path,
) -> tuple[dict[str, dict[str, str]], str | None]:
    if not path.exists():
        return {}, f"missing backend class boundary review matrix: {path}"
    rows: dict[str, dict[str, str]] = {}
    header: tuple[str, ...] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
        if not cells:
            continue
        if cells == MATRIX_COLUMNS:
            header = cells
            continue
        if header is None:
            continue
        if _is_markdown_separator(cells):
            continue
        if len(cells) != len(header):
            return rows, f"invalid row in backend class boundary matrix: {line}"
        row = dict(zip(header, cells, strict=True))
        class_name = row["Class"]
        if class_name:
            rows[class_name] = row
    if header is None:
        return rows, "backend class boundary matrix is missing the required table header"
    return rows, None


def _is_markdown_separator(cells: tuple[str, ...]) -> bool:
    return all(cell.replace(":", "").replace("-", "").strip() == "" for cell in cells)


def _is_protocol_class(node: ast.ClassDef) -> bool:
    return any(_base_name(base) == "Protocol" for base in node.bases)


def _is_small_boundary_value_class(node: ast.ClassDef) -> bool:
    if not node.name.endswith(
        (
            "DTO",
            "Value",
            "ValueObject",
            "Config",
            "Result",
            "Event",
            "Command",
            "Request",
            "Response",
        )
    ):
        return False
    public_methods = [
        item
        for item in node.body
        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
        and not item.name.startswith("_")
    ]
    return len(public_methods) <= 1


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return ""


def _class_docstring_first_line(node: ast.ClassDef) -> str:
    docstring = ast.get_docstring(node)
    if docstring is None:
        return ""
    return docstring.splitlines()[0].strip()


def _has_ownership_verb(first_line: str) -> bool:
    words = {
        word.strip(".,:;()[]{}'\"`").lower()
        for word in first_line.split()
        if word.strip(".,:;()[]{}'\"`")
    }
    return bool(words & OWNERSHIP_DOCSTRING_VERBS)


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
        """Return no per-file violations; this rule only scans the repository tree."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Flag single-field DTO/value objects lacking a baseline boundary justification."""
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
        """Return no per-file violations; this rule only scans the repository tree."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Flag DTO class names duplicated across application and runtime packages."""
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
    "ClassInventoryBudgetRule",
    "DuplicateDtoNameRule",
    "PlatformFreezeRule",
    "SingleFieldDtoJustificationRule",
]
