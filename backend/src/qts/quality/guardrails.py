"""Verify repository architecture and domain-boundary guardrails."""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol, cast, runtime_checkable

import yaml  # type: ignore[import-untyped]

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
        "qts.reporting.live",
        "qts.runtime.config.live",
        "qts.runtime.live",
        "qts.runtime.live_reconciliation",
        "qts.runtime.live_runtime_session",
        "qts.runtime.live_runtime_dependencies",
        "qts.runtime.live_runtime_topology",
        "qts.runtime.sinks.live",
    }
)
REMOVED_IMPORT_SYMBOLS = frozenset(
    {
        ("qts.reporting", "LiveEventReporter"),
        ("qts.reporting", "LiveReportManifest"),
        ("qts.reporting", "LiveReportWriter"),
        ("qts.runtime", "LiveOrderPermission"),
        ("qts.runtime", "LiveRecoveryDecision"),
        ("qts.runtime", "LiveRecoveryDecisionStatus"),
        ("qts.runtime", "LiveRuntime"),
        ("qts.runtime.config", "LiveRuntimeConfig"),
        ("qts.runtime.config.paper", "PaperBrokerRuntimeConfig"),
        ("qts.runtime.permissions", "LiveOrderPermission"),
        ("qts.runtime.sinks", "LiveRuntimeEventSink"),
        ("qts.runtime.state_recovery", "LiveRecoveryDecision"),
        ("qts.runtime.state_recovery", "LiveRecoveryDecisionStatus"),
    }
)
REMOVED_IMPORT_WILDCARD_MODULES = frozenset(
    {
        "qts.runtime.config.live",
        "qts.runtime.live",
        "qts.runtime.live_reconciliation",
        "qts.runtime.sinks.live",
    }
)
STALE_ARCHITECTURE_TEXT = {
    "qts.runtime.live": "Use qts.runtime.broker_startup or qts.runtime.order_result.",
    "LiveRuntime": "RuntimeSession is the only broker-capable runtime entrypoint.",
    "LiveRuntimeSession": "Use RuntimeSession.",
    "live-beta": "Use current runtime readiness wording.",
    "backend/src/qts/runtime/config.py": "Use the runtime/config package path.",
}
ARCHITECTURE_TEXT_GUARD_PATHS = (Path("docs/architecture"),)
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
    "qts.reconciliation",
    "qts.portfolio.account_actor",
)
STRATEGY_SDK_FORBIDDEN_SYMBOLS = frozenset(
    {
        "BrokerActor",
        "OrderManagerActor",
        "ContractSpec",
        "BrokerSymbolMapping",
        "AccountActor",
    }
)
STRATEGY_SDK_PUBLIC_SURFACE_MODULES = frozenset({("strategy_sdk",), ("factors",)})
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
BACKTEST_ACTOR_LOOP_MAX_PRIVATE_METHODS = 2
BACKTEST_ACTOR_LOOP_FORBIDDEN_IMPORT_PREFIXES = (
    "qts.data.historical.config",
    "qts.data.historical.csv_dataset",
    "qts.data.provenance",
    "qts.domain.instruments",
    "qts.registry",
)
BACKTEST_ACTOR_LOOP_FORBIDDEN_IMPORTED_NAMES = frozenset(
    {
        "BacktestArtifactWriter",
        "BacktestRuntimeEventSink",
        "BacktestArtifacts",
        "RuntimeManifest",
    }
)
BACKTEST_ACTOR_LOOP_FORBIDDEN_HELPERS = frozenset(
    {
        "_build_dataset",
        "_finalize_artifacts",
        "_load_catalog",
        "_stream_configured_bars",
        "_write_manifest",
        "_write_report",
    }
)
RUNTIME_SESSION_EVIDENCE_PATH = Path("docs/architecture/runtime_session_complexity.md")
RUNTIME_COORDINATOR_DECISIONS_PATH = Path("docs/architecture/runtime_coordinator_decisions.md")
RUNTIME_SESSION_LIMITS = {
    "public_methods": 14,
    "private_helpers": 8,
    "decision_branches": 10,
    "file_lines": 350,
    "method_lines": 50,
    "cyclomatic": 11,
}
RUNTIME_SESSION_ACCOUNT_MUTATORS = frozenset(
    {"_apply_fill", "apply_fill", "apply_delta", "set_balance", "update_position"}
)
RUNTIME_SESSION_METHOD_GROUPS = (
    "lifecycle",
    "broker lifecycle",
    "market data dispatch",
    "strategy/risk/order processing",
    "safety/rollback",
    "event writing",
)
RUNTIME_COORDINATOR_CANDIDATES = {
    "RuntimeRecoveryCoordinator": Path("backend/src/qts/runtime/recovery.py"),
    "RuntimeRollbackCoordinator": Path("backend/src/qts/runtime/rollback.py"),
    "BrokerRuntimeStartupGate": Path("backend/src/qts/runtime/startup_gate.py"),
    "RuntimeSafetyController": Path("backend/src/qts/runtime/safety_controller.py"),
    "RuntimeBrokerLifecycleCoordinator": Path("backend/src/qts/runtime/broker_lifecycle.py"),
    "RuntimeMarketDataCoordinator": Path("backend/src/qts/runtime/market_data_coordinator.py"),
    "BrokerRuntimeTopologyResolver": Path("backend/src/qts/runtime/broker_runtime_topology.py"),
}
RUNTIME_COORDINATOR_KEEP_EVIDENCE = (
    "multiple call points",
    "state/policy",
    "independent test value",
    "external boundary",
    "safety boundary",
    "complexity threshold",
)
PLATFORM_FREEZE_EXCEPTIONS_PATH = Path("docs/architecture/platform_freeze_exceptions.yaml")
CLASS_INVENTORY_BASELINE_PATH = Path("artifacts/quality/class_inventory_baseline.json")
FINAL_PLATFORM_FREEZE_PLAN_PATH = Path("docs/plan/qts_final_platform_freeze_review_and_tasks.md")
PLATFORM_FREEZE_RULE_KEY = "PLATFORM_FREEZE"
PLATFORM_FREEZE_BUNDLES: tuple[tuple[str, ...], ...] = (
    ("runtime",),
    ("execution", "adapters"),
    ("execution", "transports"),
    ("data", "sources"),
    ("data", "adapters"),
    ("data", "transports"),
    ("reconciliation",),
)
GUARDRAIL_REMEDIATIONS = {
    PLATFORM_FREEZE_RULE_KEY: (
        "Add a temporary exception with an explicit expiry and reason in "
        "platform_freeze_exceptions.yaml, or move the concept out of frozen packages."
    ),
    "ADAPTER_BOUNDARY": (
        "Move cross-service behavior behind the correct data or execution adapter boundary."
    ),
    "BACKTEST_ACTOR_LOOP_COHESION": (
        "Keep BacktestActorLoop focused on replay/event flow and move input/report ownership "
        "to source, sink, or artifact boundaries."
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
    "CLASS_INVENTORY_BUDGET": (
        "Keep production classes within the platform baseline or add an explicit freeze exception."
    ),
    "DUPLICATE_DTO_NAME": ("Use distinct DTO names across application and runtime boundaries."),
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
    "RUNTIME_COORDINATOR_DECISION": (
        "Record a keep/merge/delete decision with enforceable retention evidence."
    ),
    "RUNTIME_SESSION_COMPLEXITY": (
        "Keep RuntimeSession under facade limits or maintain explicit M5 gate evidence."
    ),
    "SHARED_CAPABILITY_IN_SOURCE_BOUNDARY": (
        "Move shared roll/session/resolution logic to a shared package."
    ),
    "SHARED_RUNTIME_WORDING": "Use mode-neutral runtime wording.",
    "SINGLE_FIELD_DTO_JUSTIFICATION": (
        "Merge pass-through wrappers or add boundary justification to the class inventory baseline."
    ),
    "STALE_ARCHITECTURE_TEXT": "Update architecture text to the canonical M0 runtime boundary.",
    "STRATEGY_SDK_INTERNAL_LEAK": (
        "Expose only Strategy SDK public facades and readonly value types."
    ),
    "TEST_SUPPORT_IN_PRODUCTION": "Move test support helpers under tests.",
    "TRANSPORT_CANONICAL_PATH": "Move transport classes under a transports package.",
    "TRANSPORT_ACTOR_IMPORT": (
        "Keep transports free of runtime actors and emit normalized callbacks instead."
    ),
    "TRANSPORT_ADAPTER_IMPORT": (
        "Keep adapter business behavior out of transports; pass normalized payloads "
        "through protocols."
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
    symbol: str = ""

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
        symbol = f" symbol: {self.symbol}" if self.symbol else ""
        return (
            f"{self.path}:{self.line}: {self.code}:{symbol} "
            f"{self.message} remediation: {self.remediation}"
        )


@dataclass(frozen=True, slots=True)
class _ClassInventoryBaseline:
    production_class_count: int
    production_classes: frozenset[str]
    single_field_boundary_justifications: frozenset[str]
    parse_violations: frozenset[tuple[int, str]]


@dataclass(frozen=True, slots=True)
class _ProductionClassEntry:
    symbol: str
    name: str
    relative_path: Path
    qts_relative_path: Path
    line: int
    field_count: int


@dataclass(frozen=True, slots=True)
class PlatformFreezeException:
    """Structured allowlisted class exception for the platform freeze rule."""

    class_name: str
    module: str
    reason: str
    owner: str
    expiry: date

    @classmethod
    def from_raw(cls, payload: dict[str, object], line: int) -> PlatformFreezeException | str:
        """Return an exception object or a parse violation message."""
        missing = {
            k for k in ("class_name", "module", "reason", "owner", "expiry") if k not in payload
        }
        if missing:
            return f"exception item missing keys: {', '.join(sorted(missing))} (line {line})"
        expiry_value = str(payload["expiry"])
        try:
            expiry = datetime.fromisoformat(expiry_value).date()
        except ValueError:
            return f"invalid expiry date: {expiry_value!r} (line {line})"
        return cls(
            class_name=str(payload["class_name"]),
            module=str(payload["module"]),
            reason=str(payload["reason"]),
            owner=str(payload["owner"]),
            expiry=expiry,
        )


@dataclass(frozen=True, slots=True)
class PlatformFreezeConfig:
    """Runtime configuration for `PlatformFreezeRule`."""

    allowed_exceptions: frozenset[tuple[str, str]] = frozenset()
    expired_exceptions: frozenset[tuple[str, str]] = frozenset()
    parse_violations: frozenset[tuple[int, str]] = frozenset()


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


def _is_platform_freeze_module(qts_relative_path: Path) -> bool:
    """Return whether module lives under a frozen package."""
    return any(
        qts_relative_path.parts[: len(frozen_prefix)] == frozen_prefix
        for frozen_prefix in PLATFORM_FREEZE_BUNDLES
    )


def _load_platform_freeze_config(repo_root: Path) -> PlatformFreezeConfig:
    """Load platform freeze exceptions from docs file."""
    path = repo_root / PLATFORM_FREEZE_EXCEPTIONS_PATH
    if not path.exists():
        return PlatformFreezeConfig(
            allowed_exceptions=frozenset(),
            expired_exceptions=frozenset(),
            parse_violations=frozenset({(1, f"missing exception file: {path}")}),
        )

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return PlatformFreezeConfig(
            parse_violations=frozenset(
                {(1, f"failed to parse platform freeze exceptions yaml: {exc}")}
            )
        )
    if not isinstance(payload, dict):
        return PlatformFreezeConfig(
            parse_violations=frozenset(
                {(1, f"platform freeze exceptions file must be a mapping: {path}")}
            )
        )

    raw_exceptions = payload.get("exceptions")
    if not isinstance(raw_exceptions, list):
        return PlatformFreezeConfig(
            parse_violations=frozenset(
                {
                    (
                        1,
                        "platform freeze exceptions must declare an 'exceptions' list."
                        f" File: {path}",
                    )
                }
            )
        )

    allowed: set[tuple[str, str]] = set()
    expired: set[tuple[str, str]] = set()
    parse_violations: set[tuple[int, str]] = set()
    today = date.today()
    for index, item in enumerate(raw_exceptions, start=1):
        if not isinstance(item, dict):
            parse_violations.add((index, "exception item must be a mapping"))
            continue
        parsed = PlatformFreezeException.from_raw(item, index)
        if isinstance(parsed, str):
            parse_violations.add((index, parsed))
            continue
        class_name = parsed.class_name
        module_name = parsed.module
        expiry_date = parsed.expiry
        key = (module_name, class_name)
        if expiry_date < today:
            expired.add(key)
        else:
            allowed.add(key)

    return PlatformFreezeConfig(
        allowed_exceptions=frozenset(allowed),
        expired_exceptions=frozenset(expired),
        parse_violations=frozenset(parse_violations),
    )


def _iter_top_level_classes(tree: ast.AST) -> list[ast.ClassDef]:
    """Return top-level class definitions from module body."""
    module = cast(ast.Module, tree)
    return [node for node in module.body if isinstance(node, ast.ClassDef)]


def _is_public_class(node: ast.ClassDef) -> bool:
    """Return whether class definition is production-public."""
    return not node.name.startswith("_")


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


@runtime_checkable
class RepositoryRule(Protocol):
    """Optional guardrail rule interface for repository-wide checks."""

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
        ...


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
        """Perform check."""
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


class StaleArchitectureTextRule:
    """Reject stale architecture wording from M0 guarded documents."""

    code = "STALE_ARCHITECTURE_TEXT"

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
        violations: list[GuardrailViolation] = []
        for relative_path in _iter_architecture_text_paths(repo_root):
            path = repo_root / relative_path
            source = path.read_text(encoding="utf-8")
            for token, guidance in STALE_ARCHITECTURE_TEXT.items():
                line = _line_number_containing(source, token)
                if line is None:
                    continue
                violations.append(
                    GuardrailViolation(
                        code=self.code,
                        path=str(relative_path),
                        line=line,
                        message=f"stale architecture text is not allowed: {token}",
                        remediation=guidance,
                        symbol=token,
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


class BacktestActorLoopCohesionRule:
    """Reject input assembly and report ownership inside the backtest actor loop."""

    code = "BACKTEST_ACTOR_LOOP_COHESION"

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Perform check."""
        return _check_backtest_actor_loop_cohesion(relative_path, qts_relative_path, tree)


class StrategySdkPublicSurfaceRule:
    """Reject internal runtime/broker/risk/reconciliation symbols from public SDK modules."""

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
        """Perform per-file check."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
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
        """Perform per-file check."""
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform repository-wide check."""
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


class GuardrailSuite:
    """Execute a configured set of guardrail rules against Python files."""

    def __init__(
        self, rules: tuple[Rule, ...] | None = None, repo_root: Path | None = None
    ) -> None:
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
            BacktestActorLoopCohesionRule(),
            StrategySdkPublicSurfaceRule(),
            LivePackageNoReplayClassRule(),
            DataLiveNoSharedContractRule(),
            TransportCanonicalPathRule(),
            TransportAdapterImportRule(),
            RemovedImportNoNewUsageRule(),
            ProductionNoFakeClassRule(),
            ProductionNoTestingImportRule(),
            SharedRuntimeWordingRule(),
            ProductionPlaceholderDocstringRule(),
            StaleArchitectureTextRule(),
            PlatformFreezeRule(repo_root=repo_root),
            RuntimeSessionComplexityRule(),
            RuntimeCoordinatorDecisionRule(),
            ClassInventoryBudgetRule(repo_root=repo_root),
            SingleFieldDtoJustificationRule(repo_root=repo_root),
            DuplicateDtoNameRule(),
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
        violations: list[GuardrailViolation] = []
        if source_root.exists():
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
        for rule in self.rules:
            if isinstance(rule, RepositoryRule):
                violations.extend(rule.check_repository(repo_root))
        return sorted(violations)


def run_guardrails(repo_root: Path) -> list[GuardrailViolation]:
    """Return all guardrail violations under the repository root."""
    return GuardrailSuite(repo_root=repo_root).check(repo_root)


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
    for metric_name in ("public_methods", "private_helpers", "decision_branches", "file_lines"):
        value = getattr(metrics, metric_name)
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
    end_lineno = getattr(node, "end_lineno", getattr(node, "lineno", 1))
    return int(end_lineno) - int(getattr(node, "lineno", 1)) + 1


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
        code="RUNTIME_COORDINATOR_DECISION",
        path=str(relative_path),
        line=line,
        message=f"{class_name} is marked delete but still has a production import",
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


def _check_backtest_actor_loop_cohesion(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts != ("backtest", "actor_loop.py"):
        return []
    violations: list[GuardrailViolation] = []
    for imported_module, line in _iter_imports(tree):
        if imported_module.startswith(BACKTEST_ACTOR_LOOP_FORBIDDEN_IMPORT_PREFIXES):
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_ACTOR_LOOP_COHESION",
                    path=str(relative_path),
                    line=line,
                    message=(
                        "BacktestActorLoop should consume prepared replay bars and "
                        f"dependencies, not own input assembly via {imported_module}"
                    ),
                )
            )
    for imported_module, imported_name, line in _iter_imported_names(tree):
        if imported_name not in BACKTEST_ACTOR_LOOP_FORBIDDEN_IMPORTED_NAMES:
            continue
        violations.append(
            GuardrailViolation(
                code="BACKTEST_ACTOR_LOOP_COHESION",
                path=str(relative_path),
                line=line,
                message=(
                    "BacktestActorLoop should emit normalized events through its sink, "
                    f"not own report artifacts via {imported_module}.{imported_name}"
                ),
            )
        )
    module = cast(ast.Module, tree)
    for node in module.body:
        if not isinstance(node, ast.ClassDef) or node.name != "BacktestActorLoop":
            continue
        private_methods = [
            item
            for item in node.body
            if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            and item.name.startswith("_")
            and not item.name.startswith("__")
        ]
        if len(private_methods) > BACKTEST_ACTOR_LOOP_MAX_PRIVATE_METHODS:
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_ACTOR_LOOP_COHESION",
                    path=str(relative_path),
                    line=node.lineno,
                    message=(
                        "BacktestActorLoop private helper count must stay at or below "
                        f"{BACKTEST_ACTOR_LOOP_MAX_PRIVATE_METHODS}; found "
                        f"{len(private_methods)}"
                    ),
                )
            )
        for method in private_methods:
            if method.name not in BACKTEST_ACTOR_LOOP_FORBIDDEN_HELPERS:
                continue
            violations.append(
                GuardrailViolation(
                    code="BACKTEST_ACTOR_LOOP_COHESION",
                    path=str(relative_path),
                    line=method.lineno,
                    message=(
                        "BacktestActorLoop private helpers must not own replay input "
                        f"or report artifact work: {method.name}"
                    ),
                )
            )
    return violations


def _check_strategy_sdk_internal_leak(
    relative_path: Path,
    qts_relative_path: Path,
    tree: ast.AST,
) -> list[GuardrailViolation]:
    if qts_relative_path.parts[:1] not in STRATEGY_SDK_PUBLIC_SURFACE_MODULES:
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


def _iter_architecture_text_paths(repo_root: Path) -> list[Path]:
    paths: set[Path] = set()
    for guarded_path in ARCHITECTURE_TEXT_GUARD_PATHS:
        path = repo_root / guarded_path
        if path.is_dir():
            for suffix in ("*.md", "*.html"):
                paths.update(item.relative_to(repo_root) for item in path.rglob(suffix))
            continue
        if path.exists():
            paths.add(path.relative_to(repo_root))
    return sorted(paths)


def _line_number_containing(source: str, token: str) -> int | None:
    for line_number, line in enumerate(source.splitlines(), start=1):
        if token == "LiveRuntime":
            if re.search(r"\bLiveRuntime\b", line):
                return line_number
            continue
        if token in line:
            return line_number
    return None


def _has_allowed_prefix(path: Path, prefixes: tuple[tuple[str, ...], ...]) -> bool:
    return any(path.parts[: len(prefix)] == prefix for prefix in prefixes)


def _class_inventory_baseline_optional(repo_root: Path) -> bool:
    return (
        not (repo_root / CLASS_INVENTORY_BASELINE_PATH).exists()
        and not (repo_root / FINAL_PLATFORM_FREEZE_PLAN_PATH).exists()
    )


def _load_class_inventory_baseline(repo_root: Path) -> _ClassInventoryBaseline | None:
    path = repo_root / CLASS_INVENTORY_BASELINE_PATH
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return _ClassInventoryBaseline(
            production_class_count=0,
            production_classes=frozenset(),
            single_field_boundary_justifications=frozenset(),
            parse_violations=frozenset({(1, f"failed to parse class inventory baseline: {exc}")}),
        )
    if not isinstance(payload, dict):
        return _ClassInventoryBaseline(
            production_class_count=0,
            production_classes=frozenset(),
            single_field_boundary_justifications=frozenset(),
            parse_violations=frozenset({(1, "class inventory baseline must be a mapping")}),
        )

    parse_violations: set[tuple[int, str]] = set()
    raw_count = payload.get("production_class_count")
    if isinstance(raw_count, int) and raw_count >= 0:
        production_class_count = raw_count
    else:
        production_class_count = 0
        parse_violations.add((1, "production_class_count must be a non-negative integer"))

    raw_classes = payload.get("production_classes")
    if isinstance(raw_classes, list) and all(isinstance(item, str) for item in raw_classes):
        production_classes = frozenset(raw_classes)
    else:
        production_classes = frozenset()
        parse_violations.add((1, "production_classes must be a list of class symbols"))

    raw_justifications = payload.get("single_field_boundary_justifications")
    if isinstance(raw_justifications, dict) and all(
        isinstance(key, str) and isinstance(value, str) and value.strip()
        for key, value in raw_justifications.items()
    ):
        single_field_justifications = frozenset(raw_justifications)
    else:
        single_field_justifications = frozenset()
        parse_violations.add(
            (
                1,
                "single_field_boundary_justifications must map class symbols to non-empty text",
            )
        )

    return _ClassInventoryBaseline(
        production_class_count=production_class_count,
        production_classes=production_classes,
        single_field_boundary_justifications=single_field_justifications,
        parse_violations=frozenset(parse_violations),
    )


def _class_inventory_parse_violations(
    code: str, baseline: _ClassInventoryBaseline
) -> list[GuardrailViolation]:
    return [
        GuardrailViolation(
            code=code,
            path=str(CLASS_INVENTORY_BASELINE_PATH),
            line=line,
            message=message,
        )
        for line, message in sorted(baseline.parse_violations)
    ]


def _scan_production_classes(repo_root: Path) -> list[_ProductionClassEntry]:
    source_root = repo_root / QTS_ROOT
    if not source_root.exists():
        return []
    entries: list[_ProductionClassEntry] = []
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative_path = path.relative_to(repo_root)
        qts_relative_path = path.relative_to(source_root)
        if qts_relative_path.parts[:1] == ("testing",):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(relative_path))
        module_name = "qts." + qts_relative_path.with_suffix("").as_posix().replace("/", ".")
        for node in _iter_top_level_classes(tree):
            if not _is_public_class(node):
                continue
            entries.append(
                _ProductionClassEntry(
                    symbol=f"{module_name}.{node.name}",
                    name=node.name,
                    relative_path=relative_path,
                    qts_relative_path=qts_relative_path,
                    line=node.lineno,
                    field_count=_class_field_count(node),
                )
            )
    return entries


def _class_field_count(node: ast.ClassDef) -> int:
    fields: set[str] = set()
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            if _is_class_var_annotation(item.annotation):
                continue
            if not item.target.id.startswith("_"):
                fields.add(item.target.id)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    fields.add(target.id)
    return len(fields)


def _is_class_var_annotation(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "ClassVar"
    if isinstance(annotation, ast.Attribute):
        return annotation.attr == "ClassVar"
    if isinstance(annotation, ast.Subscript):
        return _is_class_var_annotation(annotation.value)
    return False


def _is_dto_or_value_object_name(name: str) -> bool:
    return name.endswith("DTO") or name.endswith("ValueObject")


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
