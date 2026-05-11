"""Verify repository architecture and domain-boundary guardrails."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

QTS_ROOT = Path("backend/src/qts")
PRODUCT_SYMBOLS = frozenset({"GC", "SI", "ES", "NQ", "CL", "HG", "ZN", "ZB", "YM", "RTY"})
BROKER_TOKENS = frozenset({"IBKR", "TWS"})
TEST_SUPPORT_TOKENS = frozenset({"ANCHOR", "FIXTURE"})
SHARED_CAPABILITY_MODULE_TOKENS = frozenset({"ROLL", "SESSION", "RESOLUTION"})
SOURCE_SPECIFIC_BOUNDARY_PREFIXES = (
    ("backtest",),
    ("data", "historical"),
)

PRODUCT_FACT_ALLOWED_PREFIXES = (
    ("registry", "providers"),
    ("portfolio", "valuation"),
    ("risk", "margin"),
)
BROKER_FACT_ALLOWED_PREFIXES = (
    ("config",),
    ("data", "adapters"),
    ("execution", "adapters"),
)


@dataclass(frozen=True, order=True, slots=True)
class GuardrailViolation:
    """One architecture or domain-boundary guardrail violation."""

    code: str
    path: str
    line: int
    message: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.code}: {self.message}"


def run_guardrails(repo_root: Path) -> list[GuardrailViolation]:
    """Return all guardrail violations under the repository root."""

    source_root = repo_root / QTS_ROOT
    if not source_root.exists():
        return []
    violations: list[GuardrailViolation] = []
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        violations.extend(_check_python_file(repo_root, path))
    return sorted(violations)


def _check_python_file(repo_root: Path, path: Path) -> list[GuardrailViolation]:
    relative_path = path.relative_to(repo_root)
    qts_relative_path = path.relative_to(repo_root / QTS_ROOT)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(relative_path))
    violations: list[GuardrailViolation] = []

    for imported_module, line in _iter_imports(tree):
        violations.extend(_check_import(relative_path, qts_relative_path, imported_module, line))

    if not _has_allowed_prefix(qts_relative_path, PRODUCT_FACT_ALLOWED_PREFIXES):
        violations.extend(_check_product_specific_code(relative_path, tree))

    if not _has_allowed_prefix(qts_relative_path, BROKER_FACT_ALLOWED_PREFIXES):
        violations.extend(_check_broker_specific_code(relative_path, tree))

    violations.extend(_check_test_support_code(relative_path, qts_relative_path, tree))
    violations.extend(_check_shared_capability_placement(relative_path, qts_relative_path))

    return violations


def _check_import(
    relative_path: Path,
    qts_relative_path: Path,
    imported_module: str,
    line: int,
) -> list[GuardrailViolation]:
    if not imported_module.startswith("qts."):
        return []
    source_layer = qts_relative_path.parts[0]
    imported_parts = imported_module.split(".")
    imported_layer = imported_parts[1] if len(imported_parts) > 1 else ""
    if imported_layer in ("", source_layer):
        return []

    if _is_forbidden_dependency(source_layer, imported_module, imported_layer):
        return [
            GuardrailViolation(
                code="IMPORT_BOUNDARY",
                path=str(relative_path),
                line=line,
                message=f"{source_layer} must not import {imported_module}",
            )
        ]
    if _is_forbidden_adapter_dependency(qts_relative_path, imported_module):
        return [
            GuardrailViolation(
                code="ADAPTER_BOUNDARY",
                path=str(relative_path),
                line=line,
                message=f"adapter boundary must not import {imported_module}",
            )
        ]
    return []


def _is_forbidden_dependency(
    source_layer: str,
    imported_module: str,
    imported_layer: str,
) -> bool:
    if source_layer == "core":
        return imported_layer != "core"
    if source_layer == "domain":
        return imported_layer not in {"core", "domain"}
    if source_layer == "strategy_sdk":
        return imported_layer in {
            "api",
            "application",
            "backtest",
            "data",
            "execution",
            "registry",
            "risk",
            "runtime",
            "workers",
        }
    if source_layer == "api":
        return imported_module.startswith("qts.runtime.actors") or imported_module.startswith(
            "qts.execution.order_manager"
        )
    return False


def _is_forbidden_adapter_dependency(qts_relative_path: Path, imported_module: str) -> bool:
    parts = qts_relative_path.parts
    if parts[:2] == ("data", "adapters"):
        return imported_module.startswith(
            ("qts.execution", "qts.portfolio", "qts.risk", "qts.runtime")
        )
    if parts[:2] == ("execution", "adapters"):
        return imported_module.startswith("qts.data")
    return False


def _check_product_specific_code(
    relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    return _check_forbidden_tokens(
        relative_path,
        tree,
        tokens=PRODUCT_SYMBOLS,
        code="PRODUCT_SPECIFIC_IMPLEMENTATION",
        description="product-specific facts belong in registry/spec/session/risk data boundaries",
    )


def _check_broker_specific_code(
    relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    return _check_forbidden_tokens(
        relative_path,
        tree,
        tokens=BROKER_TOKENS,
        code="BROKER_SPECIFIC_IMPLEMENTATION",
        description="broker-specific facts belong in config or adapter boundaries",
    )


def _check_test_support_code(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    violations: list[GuardrailViolation] = []
    path_tokens = _identifier_tokens(qts_relative_path.stem)
    if path_tokens.intersection(TEST_SUPPORT_TOKENS):
        violations.append(
            GuardrailViolation(
                code="TEST_SUPPORT_IN_PRODUCTION",
                path=str(relative_path),
                line=1,
                message="test/anchor support code belongs under tests, not backend/src/qts",
            )
        )
    for node in ast.walk(tree):
        name = _node_identifier_name(node)
        if name is None or not _contains_forbidden_token(name, TEST_SUPPORT_TOKENS):
            continue
        violations.append(
            GuardrailViolation(
                code="TEST_SUPPORT_IN_PRODUCTION",
                path=str(relative_path),
                line=getattr(node, "lineno", 1),
                message=f"{name!r} is test/anchor support code; put it under tests",
            )
        )
    return violations


def _check_shared_capability_placement(
    relative_path: Path,
    qts_relative_path: Path,
) -> list[GuardrailViolation]:
    if not _has_allowed_prefix(qts_relative_path, SOURCE_SPECIFIC_BOUNDARY_PREFIXES):
        return []
    path_tokens = _identifier_tokens(qts_relative_path.stem)
    if not path_tokens.intersection(SHARED_CAPABILITY_MODULE_TOKENS):
        return []
    return [
        GuardrailViolation(
            code="SHARED_CAPABILITY_IN_SOURCE_BOUNDARY",
            path=str(relative_path),
            line=1,
            message=(
                "shared roll/session/resolution modules belong in registry, "
                "data/sessions, or another documented shared boundary"
            ),
        )
    ]


def _check_forbidden_tokens(
    relative_path: Path,
    tree: ast.AST,
    *,
    tokens: frozenset[str],
    code: str,
    description: str,
) -> list[GuardrailViolation]:
    violations: list[GuardrailViolation] = []
    for node in ast.walk(tree):
        name = _node_identifier_name(node)
        if name is not None and _contains_forbidden_token(name, tokens):
            violations.append(
                GuardrailViolation(
                    code=code,
                    path=str(relative_path),
                    line=getattr(node, "lineno", 1),
                    message=f"{name!r} uses a specialized token; {description}",
                )
            )
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _contains_forbidden_token(node.value, tokens):
                violations.append(
                    GuardrailViolation(
                        code=code,
                        path=str(relative_path),
                        line=getattr(node, "lineno", 1),
                        message=f"{node.value!r} uses a specialized token; {description}",
                    )
                )
    return violations


def _node_identifier_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
        return node.name
    if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store):
        return node.attr
    return None


def _contains_forbidden_token(value: str, forbidden_tokens: frozenset[str]) -> bool:
    return any(token in forbidden_tokens for token in _identifier_tokens(value))


def _identifier_tokens(value: str) -> set[str]:
    tokens: set[str] = set()
    for part in re.split(r"[^A-Za-z0-9]+", value):
        if not part:
            continue
        tokens.add(part.upper())
        tokens.update(
            item.upper() for item in re.findall(r"[A-Z]+(?=[A-Z][a-z]|$)|[A-Z]?[a-z]+|\d+", part)
        )
    return tokens


def _iter_imports(tree: ast.AST) -> list[tuple[str, int]]:
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            imports.append((node.module, node.lineno))
    return imports


def _has_allowed_prefix(path: Path, prefixes: tuple[tuple[str, ...], ...]) -> bool:
    return any(path.parts[: len(prefix)] == prefix for prefix in prefixes)


def main() -> int:
    repo_root = Path.cwd()
    violations = run_guardrails(repo_root)
    if not violations:
        print("Architecture guardrails passed.")
        return 0
    print("Architecture guardrails failed:")
    for violation in violations:
        print(f"  {violation.format()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
