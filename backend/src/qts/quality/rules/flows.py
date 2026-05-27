"""Flow-boundary guardrail rules."""

from __future__ import annotations

import ast
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode  # type: ignore[import-untyped]

from qts.quality.guardrails import (
    GuardrailViolation,
    _iter_imported_names,
    _iter_imports,
)

FORBIDDEN_RESEARCH_WORKFLOW_KEYS = frozenset(
    {"broker", "generate_code", "live", "orders", "paper", "promote", "runtime", "trade"}
)
FORBIDDEN_PRODUCTION_STRATEGY_IMPORT_PREFIXES = ("examples", "strategies.research")


class _ResearchRunScriptRule:
    """Reject one-off research runner scripts from source control."""

    code = "RESEARCH_RUN_SCRIPT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        scripts_path = repo_root / "scripts" / "research"
        if not scripts_path.exists():
            return []

        rejected_paths = set(scripts_path.rglob("run_*_research.py"))
        rejected_paths.update(scripts_path.rglob("run_vwap_*.py"))
        return [
            GuardrailViolation(
                code=self.code,
                path=str(path.relative_to(repo_root)),
                line=1,
                message=(
                    "research runner shortcuts must not live under scripts/research; "
                    "use the shared research workflow entrypoint"
                ),
                remediation=(
                    "Move reusable behavior behind the research workflow boundary and remove "
                    "the one-off runner script."
                ),
                symbol=path.name,
            )
            for path in sorted(rejected_paths)
            if path.is_file()
        ]


class _VwapOptimizerConfigRule:
    """Reject VWAP optimizer configs outside research workflow gates."""

    code = "VWAP_OPTIMIZER_CONFIG"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        optimizer_path = repo_root / "configs" / "optimizer"
        if not optimizer_path.exists():
            return []

        return [
            GuardrailViolation(
                code=self.code,
                path=str(path.relative_to(repo_root)),
                line=1,
                message=("VWAP optimizer configs must not bypass research workflow gates"),
                remediation=(
                    "Model VWAP research through configs/research/workflows and keep "
                    "configs/optimizer for generic optimizer examples."
                ),
                symbol=path.name,
            )
            for path in sorted(optimizer_path.iterdir())
            if path.is_file()
            and path.suffix.lower() in {".yaml", ".yml"}
            and "vwap" in path.stem.lower()
        ]


class _ProductionStrategyImportRule:
    """Reject production strategies importing research or example strategies."""

    code = "PRODUCTION_STRATEGY_IMPORT"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        production_path = repo_root / "strategies" / "production"
        if not production_path.exists():
            return []

        violations: list[GuardrailViolation] = []
        for path in sorted(production_path.rglob("*.py")):
            tree = ast.parse(
                path.read_text(encoding="utf-8"), filename=str(path.relative_to(repo_root))
            )
            violations.extend(
                self._check_tree(
                    relative_path=path.relative_to(repo_root),
                    tree=tree,
                )
            )
        return violations

    def _check_tree(self, *, relative_path: Path, tree: ast.AST) -> list[GuardrailViolation]:
        violations: list[GuardrailViolation] = []
        seen: set[tuple[int, str]] = set()
        for imported_module, line in _iter_imports(tree):
            if not _is_forbidden_production_strategy_import(imported_module):
                continue
            seen.add((line, imported_module))
            violations.append(
                self._violation(
                    relative_path=relative_path,
                    line=line,
                    symbol=imported_module,
                )
            )

        for imported_module, imported_name, line in _iter_imported_names(tree):
            imported_symbol = f"{imported_module}.{imported_name}"
            if _has_seen_import(seen, line, imported_symbol):
                continue
            if not _is_forbidden_production_strategy_parent_import(imported_module, imported_name):
                continue
            violations.append(
                self._violation(
                    relative_path=relative_path,
                    line=line,
                    symbol=imported_symbol,
                )
            )
        return violations

    def _violation(self, *, relative_path: Path, line: int, symbol: str) -> GuardrailViolation:
        return GuardrailViolation(
            code=self.code,
            path=str(relative_path),
            line=line,
            message=("production strategies must not import research or example strategy modules"),
            remediation=(
                "Promote reusable strategy behavior into a production-owned module or shared "
                "Strategy SDK abstraction before importing it."
            ),
            symbol=symbol,
        )


class _ResearchWorkflowRuntimeKeyRule:
    """Reject promotion/runtime shortcut keys from research workflow configs."""

    code = "RESEARCH_WORKFLOW_RUNTIME_KEY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform per-file check."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        workflow_path = repo_root / "configs" / "research" / "workflows"
        if not workflow_path.exists():
            return []

        violations: list[GuardrailViolation] = []
        workflow_files = [
            path
            for path in workflow_path.rglob("*")
            if path.is_file() and path.suffix.lower() in {".yaml", ".yml"}
        ]
        for path in sorted(workflow_files):
            source = path.read_text(encoding="utf-8")
            root_node = yaml.compose(source)
            if root_node is None:
                continue
            relative_path = path.relative_to(repo_root)
            for key, line in _iter_yaml_mapping_keys(root_node):
                normalized_key = key.lower()
                if normalized_key not in FORBIDDEN_RESEARCH_WORKFLOW_KEYS:
                    continue
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=(
                            "research workflows must not declare promotion or runtime "
                            f"shortcut key: {key}"
                        ),
                        remediation=(
                            "Keep research workflows limited to research evidence gates; "
                            "paper/live/broker/order runtime wiring belongs in runtime configs."
                        ),
                        symbol=key,
                    )
                )
        return violations


def _is_forbidden_production_strategy_import(imported_module: str) -> bool:
    return any(
        imported_module == prefix or imported_module.startswith(f"{prefix}.")
        for prefix in FORBIDDEN_PRODUCTION_STRATEGY_IMPORT_PREFIXES
    )


def _is_forbidden_production_strategy_parent_import(
    imported_module: str, imported_name: str
) -> bool:
    if imported_module == "strategies" and imported_name == "research":
        return True
    return imported_module == "examples"


def _has_seen_import(seen: set[tuple[int, str]], line: int, imported_symbol: str) -> bool:
    return any(
        seen_line == line
        and (imported_symbol == seen_symbol or imported_symbol.startswith(f"{seen_symbol}."))
        for seen_line, seen_symbol in seen
    )


def _iter_yaml_mapping_keys(node: Node) -> list[tuple[str, int]]:
    keys: list[tuple[str, int]] = []
    if isinstance(node, MappingNode):
        for key_node, value_node in node.value:
            if isinstance(key_node, ScalarNode):
                keys.append((str(key_node.value), key_node.start_mark.line + 1))
            keys.extend(_iter_yaml_mapping_keys(value_node))
    elif isinstance(node, SequenceNode):
        for child_node in node.value:
            keys.extend(_iter_yaml_mapping_keys(child_node))
    return keys


ResearchRunScriptRule = _ResearchRunScriptRule
ResearchWorkflowRuntimeKeyRule = _ResearchWorkflowRuntimeKeyRule
ProductionStrategyImportRule = _ProductionStrategyImportRule
VwapOptimizerConfigRule = _VwapOptimizerConfigRule

__all__ = [
    "ResearchRunScriptRule",
    "ResearchWorkflowRuntimeKeyRule",
    "ProductionStrategyImportRule",
    "VwapOptimizerConfigRule",
]
