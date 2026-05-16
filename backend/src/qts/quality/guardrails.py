"""Verify repository architecture and domain-boundary guardrails."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

QTS_ROOT = Path("backend/src/qts")
PRODUCT_SYMBOLS = frozenset({"GC", "SI", "ES", "NQ", "CL", "HG", "ZN", "ZB", "YM", "RTY"})
BROKER_TOKENS = frozenset({"IBKR", "TWS"})
PROVIDER_SDK_MODULE_PREFIXES = ("ib_async", "ibapi")
TEST_SUPPORT_TOKENS = frozenset({"ANCHOR", "FIXTURE"})
SHARED_CAPABILITY_MODULE_TOKENS = frozenset({"ROLL", "SESSION", "RESOLUTION"})
SHARED_DATA_LIVE_CONTRACT_CLASSES = frozenset(
    {
        "FeedCapabilities",
        "FeedSubscription",
        "LiveFeedAdapter",
        "LiveFeedEvent",
        "LiveFeedFailure",
        "MarketDataAdapter",
        "MarketDataFeedCapabilities",
        "MarketDataSourceEvent",
        "MarketDataSourceFailure",
        "MarketDataSubscribed",
        "MarketDataSubscription",
        "StreamingFeedAdapter",
    }
)
REMOVED_IMPORT_MODULES = frozenset(
    {
        "qts.data.adapters.ibkr_async_transport",
        "qts.data.adapters.ibkr_transport",
        "qts.data.live.adapter",
        "qts.data.live.capabilities",
        "qts.data.live.events",
        "qts.execution.adapters.ibkr_async_transport",
        "qts.execution.adapters.ibkr_order_ids",
        "qts.execution.adapters.ibkr_transport",
        "qts.application.commands.start_paper",
        "qts.runtime.live_runtime_session",
        "qts.runtime.live_runtime_dependencies",
        "qts.runtime.live_runtime_topology",
    }
)
SOURCE_SPECIFIC_BOUNDARY_PREFIXES = (
    ("backtest",),
    ("data", "historical"),
)
OOP_FACTORY_FUNCTION_PREFIXES = ("build_", "create_", "load_", "make_")
OOP_CLASS_OWNED_HELPER_PREFIXES = (
    "_map",
    "_normalize",
    "_parse",
    "_render",
    "_require",
    "_select",
    "_validate",
)
OOP_PUBLIC_FACTORY_ALLOWED = frozenset(
    {
        ("api/app.py", "create_app"),  # FastAPI framework entrypoint.
        ("observability/logging.py", "build_log_record"),  # pure DTO transformation
    }
)
OOP_HELPER_OWNERSHIP_ALLOWED_FILES = frozenset(
    {
        "config/ibkr.py",
        "data/bars/alignment.py",
        "data/sessions/filter.py",
        "observability/logging.py",
    }
)

PRODUCT_FACT_ALLOWED_PREFIXES = (
    ("registry", "providers"),
    ("portfolio", "valuation"),
    ("risk", "margin"),
)
BROKER_FACT_ALLOWED_PREFIXES = (
    ("config",),
    ("data", "adapters"),
    ("data", "transports"),
    ("execution", "adapters"),
    ("execution", "transports"),
    ("application", "commands"),
)
BROKER_SYMBOL_MAPPING_ALLOWED_PREFIXES = (
    ("registry",),
    ("data", "adapters"),
    ("execution", "adapters"),
    ("application", "commands"),
)
PROVIDER_SDK_ALLOWED_PREFIXES = (
    ("data", "adapters"),
    ("data", "transports"),
    ("execution", "adapters"),
    ("execution", "transports"),
)
BROKER_ADAPTER_FORBIDDEN_IMPORT_PREFIXES = (
    "qts.portfolio",
    "qts.runtime",
)
STRATEGY_SDK_FORBIDDEN_IMPORT_PREFIXES = (
    "qts.runtime",
    "qts.execution.adapters",
    "qts.risk.risk_engine",
)
STRATEGY_SDK_FORBIDDEN_SYMBOLS = frozenset(
    {"BrokerActor", "OrderManagerActor", "ContractSpec", "BrokerSymbolMapping"}
)
BACKTEST_RUNNER_FORBIDDEN_IMPORT_PREFIXES = (
    "qts.data.historical.config",
    "qts.data.historical.csv_dataset",
    "qts.data.provenance",
    "qts.domain.instruments",
    "qts.registry",
)
BACKTEST_RAW_CATALOG_LOADERS = frozenset(
    {
        "load_historical_catalog",
        "load_historical_catalog_from_config",
    }
)
BACKTEST_RUNNER_FORBIDDEN_HELPERS = frozenset(
    {
        "_chain_path_exists",
        "_dataset_metadata",
        "_historical_data_config_for",
        "_instrument_registry_for",
        "_iter_root_bars",
        "_load_catalog",
        "_stream_configured_bars",
        "_symbol_resolvers_from_config",
    }
)
BACKTEST_INPUT_FORBIDDEN_IMPORTS = frozenset(
    {
        "qts.data.historical.config",
    }
)
BACKTEST_INPUT_FORBIDDEN_HELPERS = frozenset(
    {
        "_chain_path_exists",
        "_historical_data_config",
        "_load_catalog",
        "_symbol_resolvers_from_config",
    }
)
BACKTEST_ENGINE_FORBIDDEN_IMPORT_PREFIXES = (
    "qts.data.historical.chains",
    "qts.data.historical.config",
)
BACKTEST_ENGINE_FORBIDDEN_HELPERS = frozenset(
    {
        "_contract_multipliers_from_config",
    }
)
GUARDRAIL_REMEDIATIONS = {
    "ADAPTER_BOUNDARY": (
        "Move cross-service behavior behind the correct data or execution adapter boundary."
    ),
    "ADAPTER_STATE_DEPENDENCY": (
        "Keep mutable runtime state in actors and pass normalized DTOs through adapters."
    ),
    "BACKTEST_ENGINE_COHESION": (
        "Move historical replay assembly into a backtest input or data source boundary."
    ),
    "BACKTEST_INPUT_COHESION": (
        "Consume loaded catalog/input objects instead of constructing source data locally."
    ),
    "BACKTEST_RUNNER_COHESION": (
        "Keep runners as orchestration and delegate reusable input assembly."
    ),
    "BROKER_SPECIFIC_IMPLEMENTATION": (
        "Move broker-specific facts to config, registry mapping, or adapter modules."
    ),
    "BROKER_SYMBOL_BOUNDARY": (
        "Resolve broker symbols at registry, adapter, or application command boundaries."
    ),
    "IMPORT_BOUNDARY": (
        "Move the dependency to the owning lower layer or introduce a boundary DTO/protocol."
    ),
    "LIVE_PACKAGE_REPLAY_CLASS": (
        "Place replay concepts under data sources or historical boundaries."
    ),
    "OOP_HELPER_OWNERSHIP": "Move one-class private helpers onto the owning class.",
    "OOP_PUBLIC_FACTORY_FUNCTION": "Use class-owned construction or a config-owned constructor.",
    "PIPELINE_ACTOR_IMPORT": "Keep data pipelines pure and connect actors from runtime flow code.",
    "PLACEHOLDER_DOCSTRING": "Replace placeholder text with the artifact or behavior contract.",
    "PRODUCT_SPECIFIC_IMPLEMENTATION": (
        "Move product facts to registry, session, valuation, or risk data boundaries."
    ),
    "DATA_LIVE_SHARED_CONTRACT": "Move shared market-data contracts out of qts.data.live.",
    "REMOVED_IMPORT_USAGE": "Use the canonical module path instead of removed modules.",
    "PRODUCTION_FAKE_CLASS": "Move fakes under qts.testing or tests/support.",
    "PRODUCTION_TESTING_IMPORT": (
        "Production packages must depend on simulation or explicit interfaces."
    ),
    "PROVIDER_SDK_IMPORT": "Import provider SDKs only from adapter or transport boundaries.",
    "SHARED_CAPABILITY_IN_SOURCE_BOUNDARY": (
        "Move shared roll/session/resolution logic to a shared package."
    ),
    "SHARED_RUNTIME_WORDING": "Use mode-neutral runtime wording.",
    "STRATEGY_SDK_INTERNAL_LEAK": (
        "Expose only Strategy SDK public facades and readonly value types."
    ),
    "TEST_SUPPORT_IN_PRODUCTION": "Move test support helpers under tests.",
    "TRANSPORT_CANONICAL_PATH": "Move transport classes under a transports package.",
    "TRANSPORT_ACTOR_IMPORT": (
        "Keep transports free of runtime actors and emit normalized callbacks instead."
    ),
}


@dataclass(frozen=True, order=True, slots=True)
class GuardrailViolation:
    """One architecture or domain-boundary guardrail violation."""

    code: str
    path: str
    line: int
    message: str
    remediation: str = ""

    def __post_init__(self) -> None:
        """Attach a default remediation for report consumers."""
        if self.remediation:
            return
        object.__setattr__(
            self,
            "remediation",
            GUARDRAIL_REMEDIATIONS.get(
                self.code,
                "Move the behavior to the documented owner boundary.",
            ),
        )

    def format(self) -> str:
        """Perform format."""
        return (
            f"{self.path}:{self.line}: {self.code}: {self.message} remediation: {self.remediation}"
        )


class Rule(Protocol):
    """Pluggable guardrail rule interface."""

    code: str

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        ...


GuardrailRule = Rule


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
        """Perform check."""
        if qts_relative_path.parts[:1] == ("quality",):
            return []
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            violations.extend(
                _check_import(relative_path, qts_relative_path, imported_module, line)
            )
        return violations


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
        """Perform check."""
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


class ProductionNoFakeClassRule:
    """Reject fake classes from production packages."""

    code = "PRODUCTION_FAKE_CLASS"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if qts_relative_path.parts[:1] in {("testing",), ("quality",)}:
            return []
        violations: list[GuardrailViolation] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name.startswith("Fake"):
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=node.lineno,
                        message="test fakes belong under qts.testing or tests/support",
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
        """Perform check."""
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
        """Perform check."""
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
        """Perform check."""
        violations: list[GuardrailViolation] = []
        for imported_module, line in _iter_imports(tree):
            if imported_module not in REMOVED_IMPORT_MODULES:
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message=f"removed import path is not allowed: {imported_module}",
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
        """Perform check."""
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
        """Perform check."""
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
                    line=getattr(node, "lineno", 1),
                    message="shared runtime docstrings must be mode-neutral",
                )
            )
        return violations


class ProductionPlaceholderDocstringRule:
    """Reject placeholder docstrings in production code."""

    code = "PLACEHOLDER_DOCSTRING"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if qts_relative_path.parts[:1] == ("quality",):
            return []
        violations: list[GuardrailViolation] = []
        for node, docstring in _iter_docstrings(tree):
            if "placeholder" not in docstring.lower():
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=getattr(node, "lineno", 1),
                    message="production docstrings must describe the artifact contract",
                )
            )
        return violations


class ProductSpecificRule:
    """Reject product hard-coding outside documented locations."""

    code = "PRODUCT_SPECIFIC_IMPLEMENTATION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if _has_allowed_prefix(qts_relative_path, PRODUCT_FACT_ALLOWED_PREFIXES):
            return []
        return _check_product_specific_code(relative_path, qts_relative_path, tree)


class BrokerSpecificRule:
    """Reject broker hard-coding outside broker boundaries."""

    code = "BROKER_SPECIFIC_IMPLEMENTATION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if _has_allowed_prefix(qts_relative_path, BROKER_FACT_ALLOWED_PREFIXES):
            return []
        return _check_broker_specific_code(relative_path, qts_relative_path, tree)


class BrokerSymbolBoundaryRule:
    """Reject broker symbol mapping imports outside approved boundary modules."""

    code = "BROKER_SYMBOL_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        if _has_allowed_prefix(qts_relative_path, BROKER_SYMBOL_MAPPING_ALLOWED_PREFIXES):
            return []
        violations: list[GuardrailViolation] = []
        violation_lines: set[int] = set()
        for imported_module, line in _iter_imports(tree):
            if imported_module == "qts.registry.broker_symbol_mapping":
                violation_lines.add(line)
        for imported_module, imported_name, line in _iter_imported_names(tree):
            if imported_module == "qts.registry" and imported_name == "BrokerSymbolMapping":
                violation_lines.add(line)
        for line in sorted(violation_lines):
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(relative_path),
                    line=line,
                    message="BrokerSymbolMapping must stay at registry or adapter boundaries",
                )
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
        """Perform check."""
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


class TestSupportRule:
    """Reject test/anchor support in production source."""

    code = "TEST_SUPPORT_IN_PRODUCTION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        return _check_test_support_code(relative_path, qts_relative_path, tree)


class SharedCapabilityRule:
    """Reject shared capability semantics in source-specific modules."""

    code = "SHARED_CAPABILITY_IN_SOURCE_BOUNDARY"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        return _check_shared_capability_placement(relative_path, qts_relative_path)


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


class StrategySdkPublicSurfaceRule:
    """Reject internal runtime/broker/risk symbols from strategy SDK modules."""

    code = "STRATEGY_SDK_INTERNAL_LEAK"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        return _check_strategy_sdk_internal_leak(relative_path, qts_relative_path, tree)


class GuardrailSuite:
    """Execute a configured set of guardrail rules against Python files."""

    def __init__(self, rules: tuple[Rule, ...] | None = None) -> None:
        self.rules = rules or (
            ImportBoundaryRule(),
            ProductSpecificRule(),
            BrokerSpecificRule(),
            BrokerSymbolBoundaryRule(),
            ProviderSdkImportRule(),
            TestSupportRule(),
            SharedCapabilityRule(),
            OOPPublicFactoryRule(),
            OOPHelperOwnershipRule(),
            BacktestRunnerCohesionRule(),
            BacktestInputCohesionRule(),
            BacktestEngineCohesionRule(),
            StrategySdkPublicSurfaceRule(),
            LivePackageNoReplayClassRule(),
            DataLiveNoSharedContractRule(),
            TransportCanonicalPathRule(),
            RemovedImportNoNewUsageRule(),
            ProductionNoFakeClassRule(),
            ProductionNoTestingImportRule(),
            SharedRuntimeWordingRule(),
            ProductionPlaceholderDocstringRule(),
        )

    def check_file(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check_file."""
        violations: list[GuardrailViolation] = []
        for rule in self.rules:
            violations.extend(
                rule.check(
                    relative_path=relative_path,
                    qts_relative_path=qts_relative_path,
                    tree=tree,
                )
            )
        return violations

    def check(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform check."""
        source_root = repo_root / QTS_ROOT
        if not source_root.exists():
            return []

        violations: list[GuardrailViolation] = []
        for path in sorted(source_root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            relative_path = path.relative_to(repo_root)
            qts_relative_path = path.relative_to(repo_root / QTS_ROOT)
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(relative_path))
            violations.extend(
                self.check_file(
                    relative_path=relative_path,
                    qts_relative_path=qts_relative_path,
                    tree=tree,
                )
            )
        return sorted(violations)


def run_guardrails(repo_root: Path) -> list[GuardrailViolation]:
    """Return all guardrail violations under the repository root."""
    return GuardrailSuite().check(repo_root)


def _check_python_file(repo_root: Path, path: Path) -> list[GuardrailViolation]:
    relative_path = path.relative_to(repo_root)
    qts_relative_path = path.relative_to(repo_root / QTS_ROOT)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(relative_path))
    return GuardrailSuite().check_file(
        relative_path=relative_path,
        qts_relative_path=qts_relative_path,
        tree=tree,
    )


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

    if _is_transport_actor_import(qts_relative_path, imported_module):
        return [
            GuardrailViolation(
                code="TRANSPORT_ACTOR_IMPORT",
                path=str(relative_path),
                line=line,
                message=f"transport boundary must not import runtime actors: {imported_module}",
            )
        ]
    if _is_pipeline_actor_import(qts_relative_path, imported_module):
        return [
            GuardrailViolation(
                code="PIPELINE_ACTOR_IMPORT",
                path=str(relative_path),
                line=line,
                message=f"data pipeline must not import runtime actors: {imported_module}",
            )
        ]

    if _is_forbidden_broker_adapter_dependency(qts_relative_path, imported_module):
        return [
            GuardrailViolation(
                code="ADAPTER_STATE_DEPENDENCY",
                path=str(relative_path),
                line=line,
                message=(
                    f"execution/data adapter should not import mutable state owner "
                    f"{imported_module}"
                ),
            )
        ]
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


def _is_forbidden_broker_adapter_dependency(
    qts_relative_path: Path,
    imported_module: str,
) -> bool:
    if qts_relative_path.parts[:2] in {("execution", "adapters"), ("data", "adapters")}:
        return any(
            imported_module.startswith(prefix)
            for prefix in BROKER_ADAPTER_FORBIDDEN_IMPORT_PREFIXES
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


def _is_transport_actor_import(qts_relative_path: Path, imported_module: str) -> bool:
    if "transport" not in qts_relative_path.stem:
        return False
    return _is_runtime_actor_module(imported_module)


def _is_pipeline_actor_import(qts_relative_path: Path, imported_module: str) -> bool:
    if qts_relative_path.parts[:1] != ("data",):
        return False
    if "pipeline" not in qts_relative_path.stem:
        return False
    return _is_runtime_actor_module(imported_module)


def _is_runtime_actor_module(imported_module: str) -> bool:
    return imported_module.startswith(
        (
            "qts.runtime.actor",
            "qts.runtime.actor_ref",
            "qts.runtime.actors",
            "qts.runtime.mailbox",
        )
    )


def _is_provider_sdk_module(imported_module: str) -> bool:
    return any(
        imported_module == prefix or imported_module.startswith(f"{prefix}.")
        for prefix in PROVIDER_SDK_MODULE_PREFIXES
    )


def _check_product_specific_code(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts[:1] == ("quality",):
        return []
    return _check_forbidden_tokens(
        relative_path,
        tree,
        tokens=PRODUCT_SYMBOLS,
        code="PRODUCT_SPECIFIC_IMPLEMENTATION",
        description="product-specific facts belong in registry/spec/session/risk data boundaries",
    )


def _check_broker_specific_code(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts[:1] == ("quality",):
        return []
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


def _check_oop_public_factory_functions(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    module_path = qts_relative_path.as_posix()
    violations: list[GuardrailViolation] = []
    module = cast(ast.Module, tree)
    for node in module.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name.startswith("_"):
            continue
        if not node.name.startswith(OOP_FACTORY_FUNCTION_PREFIXES):
            continue
        if (module_path, node.name) in OOP_PUBLIC_FACTORY_ALLOWED:
            continue
        violations.append(
            GuardrailViolation(
                code="OOP_PUBLIC_FACTORY_FUNCTION",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "stable concept construction belongs on the owning class or config object, "
                    f"not module-level factory function {node.name}"
                ),
            )
        )
    return violations


def _check_oop_helper_ownership(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    module_path = qts_relative_path.as_posix()
    if module_path in OOP_HELPER_OWNERSHIP_ALLOWED_FILES:
        return []
    module = cast(ast.Module, tree)
    public_classes = [
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    ]
    public_functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    ]
    private_functions = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith("_")
    ]
    if public_functions or not private_functions:
        return []
    if len(public_classes) == 1:
        return [
            GuardrailViolation(
                code="OOP_HELPER_OWNERSHIP",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "module-private helper next to a single public class should be owned by "
                    f"{public_classes[0].name}: {node.name}"
                ),
            )
            for node in private_functions
        ]
    if len(public_classes) < 2:
        return []
    violations: list[GuardrailViolation] = []
    for node in private_functions:
        if not node.name.startswith(OOP_CLASS_OWNED_HELPER_PREFIXES):
            continue
        owner_classes = [
            class_node.name
            for class_node in public_classes
            if _node_references_name(class_node, node.name)
        ]
        if len(owner_classes) != 1:
            continue
        violations.append(
            GuardrailViolation(
                code="OOP_HELPER_OWNERSHIP",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "module-private helper used by one public class should be owned by "
                    f"{owner_classes[0]}: {node.name}"
                ),
            )
        )
    return violations


def _check_backtest_runner_cohesion(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts != ("backtest", "runner.py"):
        return []
    violations: list[GuardrailViolation] = []
    for imported_module, line in _iter_imports(tree):
        if imported_module.startswith(BACKTEST_RUNNER_FORBIDDEN_IMPORT_PREFIXES):
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_RUNNER_COHESION",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "backtest runner should orchestrate input builders, not own "
                        f"replay input assembly via {imported_module}"
                    ),
                )
            )
    for imported_module, imported_name, line in _iter_imported_names(tree):
        if (
            imported_module == "qts.data.historical.catalog"
            and imported_name in BACKTEST_RAW_CATALOG_LOADERS
        ):
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_RUNNER_COHESION",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "backtest runner should use the configured catalog boundary, "
                        f"not raw catalog loader {imported_name}"
                    ),
                )
            )
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name not in BACKTEST_RUNNER_FORBIDDEN_HELPERS:
            continue
        violations.append(
            GuardrailViolation(
                code="BACKTEST_RUNNER_COHESION",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "backtest runner private helpers must not own configured historical "
                    f"replay input assembly: {node.name}"
                ),
            )
        )
    return violations


def _check_backtest_input_cohesion(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts != ("backtest", "inputs.py"):
        return []
    violations: list[GuardrailViolation] = []
    for imported_module, line in _iter_imports(tree):
        if imported_module in BACKTEST_INPUT_FORBIDDEN_IMPORTS:
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_INPUT_COHESION",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "backtest input builder should consume a loaded catalog, "
                        f"not own catalog configuration via {imported_module}"
                    ),
                )
            )
    for imported_module, imported_name, line in _iter_imported_names(tree):
        if (
            imported_module == "qts.data.historical.catalog"
            and imported_name in BACKTEST_RAW_CATALOG_LOADERS
        ):
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_INPUT_COHESION",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "backtest input builder should consume a loaded catalog, "
                        f"not raw catalog loader {imported_name}"
                    ),
                )
            )
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name not in BACKTEST_INPUT_FORBIDDEN_HELPERS:
            continue
        violations.append(
            GuardrailViolation(
                code="BACKTEST_INPUT_COHESION",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "backtest input builder must not own historical catalog construction: "
                    f"{node.name}"
                ),
            )
        )
    return violations


def _check_backtest_engine_cohesion(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts != ("backtest", "engine.py"):
        return []
    violations: list[GuardrailViolation] = []
    for imported_module, line in _iter_imports(tree):
        if imported_module.startswith(BACKTEST_ENGINE_FORBIDDEN_IMPORT_PREFIXES):
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_ENGINE_COHESION",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "backtest engine should consume prepared replay inputs, not own "
                        f"historical input assembly via {imported_module}"
                    ),
                )
            )
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name not in BACKTEST_ENGINE_FORBIDDEN_HELPERS:
            continue
        violations.append(
            GuardrailViolation(
                code="BACKTEST_ENGINE_COHESION",
                path=str(relative_path),
                line=node.lineno,
                message=(
                    "backtest engine private helpers must not own historical replay "
                    f"input assembly: {node.name}"
                ),
            )
        )
    return violations


def _check_strategy_sdk_internal_leak(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts[:1] != ("strategy_sdk",):
        return []
    violations: list[GuardrailViolation] = []
    for imported_module, line in _iter_imports(tree):
        if imported_module.startswith(STRATEGY_SDK_FORBIDDEN_IMPORT_PREFIXES):
            violations.append(
                GuardrailViolation(
                    code="STRATEGY_SDK_INTERNAL_LEAK",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "Strategy SDK public modules must not import execution/runtime "
                        f"internals: {imported_module}"
                    ),
                )
            )
    for imported_module, imported_name, line in _iter_imported_names(tree):
        if (
            imported_module.startswith(STRATEGY_SDK_FORBIDDEN_IMPORT_PREFIXES)
            or imported_name in STRATEGY_SDK_FORBIDDEN_SYMBOLS
        ):
            if imported_module.startswith(STRATEGY_SDK_FORBIDDEN_IMPORT_PREFIXES):
                continue
            if imported_name not in STRATEGY_SDK_FORBIDDEN_SYMBOLS:
                continue
            violations.append(
                GuardrailViolation(
                    code="STRATEGY_SDK_INTERNAL_LEAK",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "Strategy SDK public modules must not reference internal actor/risk "
                        f"symbol {imported_name}"
                    ),
                )
            )
    module = cast(ast.Module, tree)
    for node in ast.walk(module):
        if not isinstance(node, ast.Name):
            continue
        if isinstance(node.ctx, ast.Store):
            continue
        if node.id in STRATEGY_SDK_FORBIDDEN_SYMBOLS:
            violations.append(
                GuardrailViolation(
                    code="STRATEGY_SDK_INTERNAL_LEAK",
                    path=str(relative_path),
                    line=getattr(node, "lineno", 1),
                    message=(
                        "Strategy SDK public modules must not reference internal actor/risk symbol "
                        f"{node.id}"
                    ),
                )
            )
    return violations


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


def _node_references_name(node: ast.AST, name: str) -> bool:
    return any(
        isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id == name
        for child in ast.walk(node)
    )


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


def _iter_imported_names(tree: ast.AST) -> list[tuple[str, str, int]]:
    imports: list[tuple[str, str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module is not None:
            imports.extend((node.module, alias.name, node.lineno) for alias in node.names)
    return imports


def _iter_docstrings(tree: ast.AST) -> list[tuple[ast.AST, str]]:
    docstrings: list[tuple[ast.AST, str]] = []
    for node in ast.walk(tree):
        if not isinstance(
            node,
            ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        ):
            continue
        docstring = ast.get_docstring(node)
        if docstring is not None:
            docstrings.append((node, docstring))
    return docstrings


def _has_allowed_prefix(path: Path, prefixes: tuple[tuple[str, ...], ...]) -> bool:
    return any(path.parts[: len(prefix)] == prefix for prefix in prefixes)


def main() -> int:
    """Perform main."""
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
