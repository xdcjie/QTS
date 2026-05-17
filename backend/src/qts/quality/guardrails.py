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
        "qts.portfolio.position_book",
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
        ("qts.portfolio", "PositionBook"),
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
