"""Final-readiness product gate rules."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

_DEFERRAL_PATTERN = re.compile(r"^(?P<symbol>\S+)\s+expires=\d{4}-\d{2}-\d{2}\s+target=production$")
_LIFECYCLE_ROUTE_RESPONSE_PATTERN = re.compile(
    r"@router\.post\(\"/runtime/(?:start|stop|pause|resume|enter-observation|exit-observation)\","
    r"\s*response_model=RuntimeCommandResponseSchema"
)
_HOT_PATH_ROOTS = (
    Path("backend/src/qts/runtime"),
    Path("backend/src/qts/execution"),
    Path("backend/src/qts/risk"),
    Path("backend/src/qts/portfolio"),
)
_HOT_PATH_NOT_IMPLEMENTED_EXEMPTIONS = frozenset(
    {
        Path("backend/src/qts/runtime/sinks/base.py"),
    }
)


@dataclass(frozen=True, slots=True)
class FinalReadinessRuleSet:
    """Repository-level final-state checks required before product readiness."""

    def check(self, repo_root: Path) -> list[GuardrailViolation]:
        """Return all final-readiness violations under ``repo_root``."""

        checks: tuple[Iterable[GuardrailViolation], ...] = (
            self._production_wiring_deferrals(repo_root),
            self._runtime_start_contract(repo_root),
            self._operator_lifecycle_routes(repo_root),
            self._walk_forward_writer_ownership(repo_root),
            self._hot_path_not_implemented(repo_root),
            self._actor_ask_bounded(repo_root),
            self._shared_cost_model_naming(repo_root),
            self._required_final_tests(repo_root),
        )
        violations: list[GuardrailViolation] = []
        for group in checks:
            violations.extend(group)
        return sorted(violations)

    def _production_wiring_deferrals(self, repo_root: Path) -> list[GuardrailViolation]:
        path = repo_root / "docs/plan/wiring_deferrals.md"
        if not path.exists():
            return []
        violations: list[GuardrailViolation] = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            match = _DEFERRAL_PATTERN.match(stripped)
            if match is None:
                continue
            violations.append(
                GuardrailViolation(
                    code="FINAL_PRODUCTION_WIRING_DEFERRAL",
                    path=str(path.relative_to(repo_root)),
                    line=line_no,
                    message="final readiness allows no target=production wiring deferrals",
                    symbol=match.group("symbol"),
                )
            )
        return violations

    def _runtime_start_contract(self, repo_root: Path) -> list[GuardrailViolation]:
        path = repo_root / "backend/src/qts/application/commands/start_runtime.py"
        source = self._read_text(path)
        required_fragments = {
            "launch_plan_hash": "start command must carry launch_plan_hash",
            "RuntimeLaunchPlanStore": "runtime start must verify a launch plan store",
            "session_registry.register": "started runtime must be registered",
            "RuntimeSessionKey": "operator command key must use runtime_instance_id",
            'self.status == "started" and self.session is None': (
                "RuntimeStartResult must forbid sessionless started status"
            ),
        }
        return [
            GuardrailViolation(
                code="FINAL_RUNTIME_START_CONTRACT",
                path=str(path.relative_to(repo_root)),
                line=1,
                message=message,
                symbol=fragment,
            )
            for fragment, message in required_fragments.items()
            if fragment not in source
        ]

    def _operator_lifecycle_routes(self, repo_root: Path) -> list[GuardrailViolation]:
        path = repo_root / "backend/src/qts/api/routes/operations.py"
        source = self._read_text(path)
        violations: list[GuardrailViolation] = []
        for match in _LIFECYCLE_ROUTE_RESPONSE_PATTERN.finditer(source):
            line = source.count("\n", 0, match.start()) + 1
            violations.append(
                GuardrailViolation(
                    code="FINAL_OPERATOR_STATE_ONLY_ROUTE",
                    path=str(path.relative_to(repo_root)),
                    line=line,
                    message="operator lifecycle routes must return RuntimeCommandResult responses",
                )
            )
        return violations

    def _walk_forward_writer_ownership(self, repo_root: Path) -> list[GuardrailViolation]:
        path = repo_root / "backend/src/qts/research/orchestrator/validation_artifact_writer.py"
        tree = self._parse(path)
        if tree is None:
            return []
        violations: list[GuardrailViolation] = []
        for class_node in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            if class_node.name != "ValidationArtifactWriter":
                continue
            for method in (node for node in class_node.body if isinstance(node, ast.FunctionDef)):
                if method.name != "_walk_forward_validation_payload":
                    continue
                for node in ast.walk(method):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id in {
                                "accepted",
                                "gap",
                                "allowed_gap",
                            }:
                                violations.append(
                                    self._violation(
                                        path,
                                        node.lineno,
                                        "FINAL_VALIDATION_WRITER_VERDICT",
                                        "validation writer must not compute walk-forward verdicts",
                                        target.id,
                                        repo_root=repo_root,
                                    )
                                )
                    elif isinstance(node, ast.Dict):
                        for key in node.keys:
                            if isinstance(key, ast.Constant) and key.value in {
                                "accepted",
                                "consistent",
                            }:
                                violations.append(
                                    self._violation(
                                        path,
                                        key.lineno,
                                        "FINAL_VALIDATION_WRITER_VERDICT",
                                        "walk-forward verdict fields belong to "
                                        "WalkForwardValidationArtifact",
                                        str(key.value),
                                        repo_root=repo_root,
                                    )
                                )
        return violations

    def _hot_path_not_implemented(self, repo_root: Path) -> list[GuardrailViolation]:
        violations: list[GuardrailViolation] = []
        for root in _HOT_PATH_ROOTS:
            source_root = repo_root / root
            if not source_root.exists():
                continue
            for path in sorted(source_root.rglob("*.py")):
                relative = path.relative_to(repo_root)
                if relative in _HOT_PATH_NOT_IMPLEMENTED_EXEMPTIONS:
                    continue
                tree = self._parse(path)
                if tree is None:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Raise) and self._raises_not_implemented(node):
                        violations.append(
                            self._violation(
                                path,
                                node.lineno,
                                "FINAL_HOT_PATH_NOT_IMPLEMENTED",
                                "runtime hot paths must return structured failures, "
                                "not NotImplementedError",
                                repo_root=repo_root,
                            )
                        )
        return violations

    def _actor_ask_bounded(self, repo_root: Path) -> list[GuardrailViolation]:
        violations: list[GuardrailViolation] = []
        for path in sorted((repo_root / "backend/src/qts").rglob("*.py")):
            tree = self._parse(path)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "ask"
                    and any(
                        keyword.arg == "ask_timeout"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is None
                        for keyword in node.keywords
                    )
                ):
                    continue
                violations.append(
                    self._violation(
                        path,
                        node.lineno,
                        "FINAL_ACTOR_ASK_UNBOUNDED",
                        "ActorRef.ask calls must be bounded; ask_timeout=None is forbidden",
                        repo_root=repo_root,
                    )
                )
        return violations

    def _shared_cost_model_naming(self, repo_root: Path) -> list[GuardrailViolation]:
        violations: list[GuardrailViolation] = []
        checked_roots = (Path("backend/src/qts/runtime"), Path("backend/src/qts/application"))
        for root in checked_roots:
            source_root = repo_root / root
            if not source_root.exists():
                continue
            for path in sorted(source_root.rglob("*.py")):
                relative = path.relative_to(repo_root)
                if relative in {
                    Path("backend/src/qts/runtime/config/__init__.py"),
                    Path("backend/src/qts/runtime/config/backtest.py"),
                    Path("backend/src/qts/runtime/config/cost.py"),
                    Path("backend/src/qts/runtime/config/models.py"),
                }:
                    continue
                source = path.read_text(encoding="utf-8")
                if "BacktestCostModel" not in source:
                    continue
                violations.append(
                    self._violation(
                        path,
                        self._line_of(source, "BacktestCostModel"),
                        "FINAL_BACKTEST_NAMED_SHARED_COST_MODEL",
                        "shared runtime/application code must use SimulatedExecutionCostModel",
                        "BacktestCostModel",
                        repo_root=repo_root,
                    )
                )
        return violations

    def _required_final_tests(self, repo_root: Path) -> list[GuardrailViolation]:
        required_paths = (
            Path("tests/integration/test_catalog_futures_margin_enforced.py"),
            Path("tests/integration/test_operator_command_targets_registered_runtime.py"),
            Path("tests/integration/test_operations_unbound_lifecycle_returns_rejected.py"),
            Path("tests/integration/test_promotion_to_paper_runtime_config.py"),
            Path("tests/anchor/test_runtime_start_requires_launch_plan_hash.py"),
            Path("tests/anchor/test_multi_account_final_readiness_gate.py"),
            Path("tests/unit/research/orchestrator/test_walk_forward_validation_artifact.py"),
            Path("tests/unit/quality/test_final_readiness_rule_set.py"),
        )
        return [
            GuardrailViolation(
                code="FINAL_REQUIRED_TEST_MISSING",
                path=str(path),
                line=1,
                message="final-readiness required test file is missing",
            )
            for path in required_paths
            if not (repo_root / path).exists()
        ]

    @staticmethod
    def _raises_not_implemented(node: ast.Raise) -> bool:
        exc = node.exc
        if isinstance(exc, ast.Name):
            return exc.id == "NotImplementedError"
        if isinstance(exc, ast.Call):
            func = exc.func
            return isinstance(func, ast.Name) and func.id == "NotImplementedError"
        return False

    @staticmethod
    def _read_text(path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _parse(path: Path) -> ast.Module | None:
        if not path.exists():
            return None
        try:
            return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            return None

    @staticmethod
    def _line_of(source: str, needle: str) -> int:
        index = source.find(needle)
        if index < 0:
            return 1
        return source.count("\n", 0, index) + 1

    @staticmethod
    def _violation(
        path: Path,
        line: int,
        code: str,
        message: str,
        symbol: str | None = None,
        *,
        repo_root: Path,
    ) -> GuardrailViolation:
        return GuardrailViolation(
            code=code,
            path=str(path.relative_to(repo_root)),
            line=line,
            message=message,
            symbol=symbol or "",
        )


def run_final_readiness(repo_root: Path) -> list[GuardrailViolation]:
    """Return final-readiness violations for ``repo_root``."""

    return FinalReadinessRuleSet().check(repo_root)


__all__ = ["FinalReadinessRuleSet", "run_final_readiness"]
