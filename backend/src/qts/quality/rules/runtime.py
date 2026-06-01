"""Runtime guardrail rules."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from qts.quality.guardrails import (
    QTS_ROOT,
    RUNTIME_COORDINATOR_CANDIDATES,
    RUNTIME_COORDINATOR_DECISIONS_PATH,
    RUNTIME_COORDINATOR_KEEP_EVIDENCE,
    RUNTIME_SESSION_ACCOUNT_MUTATORS,
    RUNTIME_SESSION_EVIDENCE_PATH,
    RUNTIME_SESSION_LIMITS,
    RUNTIME_SESSION_METHOD_GROUPS,
    GuardrailViolation,
    _iter_imported_names,
    _iter_imports,
)

RUNTIME_EXECUTION_ALLOWED_IMPORTS: frozenset[tuple[str, str]] = frozenset(
    {
        ("qts.execution.order_manager", "OrderManager"),
        ("qts.execution.idempotency", "FillIdempotencyStore"),
        ("qts.execution.execution_adapter", "ExecutionAdapter"),
        ("qts.execution.broker", "BrokerAdapter"),
        ("qts.execution.broker", "BrokerExecutionReport"),
        ("qts.execution.broker", "BrokerOrderRequest"),
        ("qts.execution.broker", "BrokerCapabilities"),
        ("qts.execution.broker", "normalize_broker_execution_report"),
        # Execution-boundary lifecycle errors the runtime catches/raises at the
        # order-execution edge (report quarantine + replace capability gate).
        ("qts.execution.errors", "UnknownBrokerOrder"),
        ("qts.execution.errors", "UnsupportedOrderReplace"),
    }
)


@dataclass(frozen=True, slots=True)
class _RuntimeSessionMetrics:
    public_methods: int
    private_helpers: int
    decision_branches: int
    file_lines: int
    overlong_methods: tuple[str, ...]
    complex_methods: tuple[str, ...]


def _find_class(tree: ast.AST, class_name: str) -> ast.ClassDef | None:
    module = cast(ast.Module, tree)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    return None


def _runtime_session_metrics(source: str, class_node: ast.ClassDef) -> _RuntimeSessionMetrics:
    methods = [
        node for node in class_node.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]
    public_methods = [
        method
        for method in methods
        if not method.name.startswith("_") and not _is_property_method(method)
    ]
    private_helpers = [
        method
        for method in methods
        if method.name.startswith("_")
        and not method.name.startswith("__")
        and not _is_property_method(method)
    ]
    overlong_methods = tuple(
        method.name
        for method in methods
        if _node_line_count(method) > RUNTIME_SESSION_LIMITS["method_lines"]
    )
    complex_methods = tuple(
        method.name
        for method in methods
        if _cyclomatic_complexity(method) > RUNTIME_SESSION_LIMITS["cyclomatic"]
    )
    return _RuntimeSessionMetrics(
        public_methods=len(public_methods),
        private_helpers=len(private_helpers),
        decision_branches=sum(_decision_branch_count(method) for method in methods),
        file_lines=len(source.splitlines()),
        overlong_methods=overlong_methods,
        complex_methods=complex_methods,
    )


def _runtime_session_metric_violations(metrics: _RuntimeSessionMetrics) -> list[str]:
    violations: list[str] = []
    for metric_name, value in (
        ("public_methods", metrics.public_methods),
        ("private_helpers", metrics.private_helpers),
        ("decision_branches", metrics.decision_branches),
        ("file_lines", metrics.file_lines),
    ):
        limit = RUNTIME_SESSION_LIMITS[metric_name]
        if value > limit:
            violations.append(f"{metric_name}={value}>{limit}")
    if metrics.overlong_methods:
        violations.append(
            "method_lines>"
            f"{RUNTIME_SESSION_LIMITS['method_lines']}:{','.join(metrics.overlong_methods)}"
        )
    if metrics.complex_methods:
        violations.append(
            f"cyclomatic>{RUNTIME_SESSION_LIMITS['cyclomatic']}:{','.join(metrics.complex_methods)}"
        )
    return violations


def _is_property_method(method: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in method.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "property":
            return True
    return False


def _node_line_count(node: ast.AST) -> int:
    lineno = _node_line(node)
    end_lineno = _node_end_line(node, lineno)
    return end_lineno - lineno + 1


def _node_line(node: ast.AST) -> int:
    try:
        return int(object.__getattribute__(node, "lineno"))
    except AttributeError:
        return 1


def _node_end_line(node: ast.AST, default: int) -> int:
    try:
        end_lineno = object.__getattribute__(node, "end_lineno")
    except AttributeError:
        return default
    if not isinstance(end_lineno, int):
        return default
    return end_lineno


def _cyclomatic_complexity(node: ast.AST) -> int:
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, ast.If | ast.For | ast.AsyncFor | ast.While | ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += max(1, len(child.values) - 1)
        elif isinstance(child, ast.IfExp | ast.comprehension):
            complexity += 1
    return complexity


def _decision_branch_count(node: ast.AST) -> int:
    branch_nodes = (
        ast.If,
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.ExceptHandler,
        ast.IfExp,
    )
    return sum(1 for child in ast.walk(node) if isinstance(child, branch_nodes))


def _runtime_session_forbidden_imports(
    tree: ast.AST, relative_path: Path
) -> list[GuardrailViolation]:
    violations: list[GuardrailViolation] = []
    for imported_module, line in _iter_imports(tree):
        if _is_runtime_session_ibkr_transport_import(imported_module):
            violations.append(
                GuardrailViolation(
                    code=RuntimeSessionComplexityRule.code,
                    path=str(relative_path),
                    line=line,
                    message=(
                        "RuntimeSession must not import IBKR transport modules; "
                        "wire broker transports at adapter/topology boundaries."
                    ),
                    symbol=imported_module,
                )
            )
    for imported_module, imported_name, line in _iter_imported_names(tree):
        symbol = f"{imported_module}.{imported_name}"
        if _is_runtime_session_ibkr_transport_import(symbol):
            violations.append(
                GuardrailViolation(
                    code=RuntimeSessionComplexityRule.code,
                    path=str(relative_path),
                    line=line,
                    message=(
                        "RuntimeSession must not import IBKR transport symbols; "
                        "wire broker transports at adapter/topology boundaries."
                    ),
                    symbol=symbol,
                )
            )
    return violations


def _is_runtime_session_ibkr_transport_import(imported_symbol: str) -> bool:
    normalized = imported_symbol.lower()
    if "ibkr" not in normalized and "ib_async" not in normalized:
        return False
    return ".transports." in normalized or ".adapters." in normalized


def _runtime_session_account_mutations(
    class_node: ast.ClassDef, relative_path: Path
) -> list[GuardrailViolation]:
    violations: list[GuardrailViolation] = []
    for node in ast.walk(class_node):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in RUNTIME_SESSION_ACCOUNT_MUTATORS:
            continue
        receiver_parts = _attribute_parts(node.func.value)
        if not _looks_like_account_state_receiver(receiver_parts):
            continue
        violations.append(
            GuardrailViolation(
                code=RuntimeSessionComplexityRule.code,
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "RuntimeSession must not mutate account state directly; "
                    "route fills through AccountActor ownership."
                ),
                symbol=".".join((*receiver_parts, node.func.attr)),
            )
        )
    return violations


def _attribute_parts(node: ast.AST) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        return (*_attribute_parts(node.value), node.attr)
    if isinstance(node, ast.Call):
        return _attribute_parts(node.func)
    return ()


def _looks_like_account_state_receiver(parts: tuple[str, ...]) -> bool:
    return any(
        part in {"account_actor", "_account_actor", "account", "_account", "cash", "_cash"}
        or "position" in part
        for part in parts
    )


def _read_runtime_session_evidence(repo_root: Path) -> str:
    evidence_path = repo_root / RUNTIME_SESSION_EVIDENCE_PATH
    if not evidence_path.exists():
        return ""
    return evidence_path.read_text(encoding="utf-8")


def _read_runtime_coordinator_decision_evidence(repo_root: Path) -> str:
    evidence_path = repo_root / RUNTIME_COORDINATOR_DECISIONS_PATH
    if not evidence_path.exists():
        return ""
    return evidence_path.read_text(encoding="utf-8")


def _has_runtime_session_complexity_evidence(evidence: str) -> bool:
    normalized = evidence.lower()
    if "runtimesession complexity evidence" not in normalized:
        return False
    if "m5 guardrail evidence" not in normalized:
        return False
    return all(group in normalized for group in RUNTIME_SESSION_METHOD_GROUPS)


def _runtime_coordinator_decision(evidence: str, class_name: str) -> tuple[str | None, str]:
    pattern = re.compile(
        rf"^\|\s*{re.escape(class_name)}\s*\|\s*(keep|merge|delete)\s*\|\s*([^|]+)\|",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(evidence)
    if match is None:
        return None, ""
    return match.group(1).lower(), match.group(2).strip().lower()


def _has_coordinator_keep_evidence(evidence: str) -> bool:
    return any(token in evidence for token in RUNTIME_COORDINATOR_KEEP_EVIDENCE)


def _deleted_coordinator_import_violations(
    repo_root: Path, evidence: str
) -> list[GuardrailViolation]:
    deleted_candidates = {
        class_name: relative_path
        for class_name, relative_path in RUNTIME_COORDINATOR_CANDIDATES.items()
        if _runtime_coordinator_decision(evidence, class_name)[0] == "delete"
    }
    if not deleted_candidates:
        return []
    source_root = repo_root / QTS_ROOT
    if not source_root.exists():
        return []
    candidate_modules = {
        class_name: _module_name_for_runtime_path(relative_path)
        for class_name, relative_path in deleted_candidates.items()
    }
    violations: list[GuardrailViolation] = []
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative_path = path.relative_to(repo_root)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                for class_name, module_name in candidate_modules.items():
                    if node.module == module_name and any(
                        alias.name == class_name for alias in node.names
                    ):
                        violations.append(
                            _deleted_coordinator_import_violation(
                                relative_path, node.lineno, class_name
                            )
                        )
            if isinstance(node, ast.Import):
                for class_name, module_name in candidate_modules.items():
                    if any(alias.name == module_name for alias in node.names):
                        violations.append(
                            _deleted_coordinator_import_violation(
                                relative_path, node.lineno, class_name
                            )
                        )
    return violations


def _module_name_for_runtime_path(relative_path: Path) -> str:
    return ".".join(relative_path.with_suffix("").parts[2:])


def _deleted_coordinator_import_violation(
    relative_path: Path, line: int, class_name: str
) -> GuardrailViolation:
    return GuardrailViolation(
        code=RuntimeCoordinatorDecisionRule.code,
        path=str(relative_path),
        line=line,
        message=f"{class_name} is marked delete but still has a production import",
    )


class RuntimeSessionComplexityRule:
    """Require RuntimeSession facade complexity limits or explicit M5 evidence."""

    code = "RUNTIME_SESSION_COMPLEXITY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Skip per-file analysis; this rule runs only repository-wide."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Flag RuntimeSession exceeding M5 facade limits without evidence."""
        session_path = repo_root / QTS_ROOT / "runtime/session.py"
        if not session_path.exists():
            return []
        relative_path = session_path.relative_to(repo_root)
        source = session_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(relative_path))
        session_class = _find_class(tree, "RuntimeSession")
        if session_class is None:
            return []

        hard_violations = _runtime_session_forbidden_imports(tree, relative_path)
        hard_violations.extend(_runtime_session_account_mutations(session_class, relative_path))
        if hard_violations:
            return hard_violations

        metrics = _runtime_session_metrics(source, session_class)
        violations = _runtime_session_metric_violations(metrics)
        if not violations:
            return []
        evidence = _read_runtime_session_evidence(repo_root)
        if _has_runtime_session_complexity_evidence(evidence):
            return []
        return [
            GuardrailViolation(
                code=self.code,
                path=str(relative_path),
                line=session_class.lineno,
                message=(
                    "RuntimeSession exceeds M5 facade limits without explicit evidence: "
                    + ", ".join(violations)
                ),
            )
        ]


class RuntimeCoordinatorDecisionRule:
    """Require keep/merge/delete decisions for M5 runtime coordinator candidates."""

    code = "RUNTIME_COORDINATOR_DECISION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Skip per-file analysis; this rule runs only repository-wide."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Require keep/merge/delete evidence for runtime coordinator candidates."""
        evidence = _read_runtime_coordinator_decision_evidence(repo_root)
        violations: list[GuardrailViolation] = []
        for class_name, relative_path in RUNTIME_COORDINATOR_CANDIDATES.items():
            path = repo_root / relative_path
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(relative_path))
            class_node = _find_class(tree, class_name)
            if class_node is None:
                continue
            decision, decision_evidence = _runtime_coordinator_decision(evidence, class_name)
            if decision is None:
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=class_node.lineno,
                        message=(
                            "runtime coordinator candidate lacks keep/merge/delete "
                            f"evidence: {class_name}"
                        ),
                    )
                )
                continue
            if decision != "keep":
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=class_node.lineno,
                        message=(
                            f"{class_name} is marked {decision} but still has a "
                            "production class definition"
                        ),
                    )
                )
                continue
            if not _has_coordinator_keep_evidence(decision_evidence):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=class_node.lineno,
                        message=(
                            f"{class_name} keep decision lacks retention evidence "
                            "from the M5 approved criteria"
                        ),
                    )
                )
        violations.extend(_deleted_coordinator_import_violations(repo_root, evidence))
        return violations


class RuntimeExecutionBoundaryRule:
    """Prevent runtime from importing execution-internal domain types.

    Runtime may import only explicitly whitelisted execution symbols.
    Domain types (Order, OrderFill, ExecutionReport, etc.) must be imported
    from qts.domain.orders instead.
    """

    code = "RUNTIME_EXECUTION_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Flag runtime modules importing non-whitelisted execution types."""
        if qts_relative_path.parts[:1] != ("runtime",):
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, imported_name, line in _iter_imported_names(tree):
            if not imported_module.startswith("qts.execution."):
                continue
            if (imported_module, imported_name) in RUNTIME_EXECUTION_ALLOWED_IMPORTS:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=(
                        f"runtime must not import execution-internal type "
                        f"{imported_module}.{imported_name}; "
                        f"import domain types from qts.domain.orders instead"
                    ),
                    symbol=f"{imported_module}.{imported_name}",
                )
            )
        return violations


__all__ = [
    "RuntimeCoordinatorDecisionRule",
    "RuntimeExecutionBoundaryRule",
    "RuntimeSessionComplexityRule",
]
