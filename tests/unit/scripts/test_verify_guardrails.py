from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest


def _load_guardrails_module() -> ModuleType:
    module_path = Path("scripts/verify_guardrails.py")
    spec = importlib.util.spec_from_file_location("verify_guardrails", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_guardrails = cast(Any, _load_guardrails_module().run_guardrails)


def _without_platform_freeze(violations: list[object]) -> set[str]:
    """Hide platform freeze in guardrail tests focused on this boundary."""
    codes = {violation.code for violation in violations if hasattr(violation, "code")}
    return {code for code in codes if code != "PLATFORM_FREEZE"}


def _write(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _write_platform_freeze_stub(root: Path) -> None:
    _write(
        root,
        "docs/architecture/platform_freeze_exceptions.yaml",
        "exceptions: []\n",
    )


def _codes(root: Path) -> set[str]:
    return _without_platform_freeze(run_guardrails(root))


def _codes_by_suite(root: Path, *rules: object) -> set[str]:
    suite = _load_guardrails_module().GuardrailSuite(rules=tuple(rules))
    return _without_platform_freeze(suite.check(root))


def test_guardrails_reject_domain_imports_from_runtime(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/bad.py",
        "from qts.runtime.actor import Actor\n",
    )

    assert _codes(root) == {"IMPORT_BOUNDARY"}


def test_guardrails_reject_strategy_sdk_imports_from_execution(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/strategy_sdk/bad.py",
        "from qts.execution.order_manager import OrderManager\n",
    )

    assert _codes(root) == {"IMPORT_BOUNDARY"}


def test_guardrails_reject_strategy_sdk_internal_runtime_imports(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/strategy_sdk/bad.py",
        "from qts.runtime.actors.order_manager_actor import OrderManagerActor\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_guardrails_reject_strategy_sdk_internal_domain_symbols(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/strategy_sdk/bad.py",
        "from qts.domain.instruments import ContractSpec\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_strategy_package_cannot_import_runtime_internals(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/strategy_sdk/bad.py",
        "from qts.runtime.actor import Actor\n"
        "from qts.reconciliation import reconcile_snapshots\n"
        "from qts.portfolio.account_actor import AccountActor\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_strategy_package_cannot_import_broker_transports(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/strategy_sdk/bad.py",
        "from qts.execution.adapters.ibkr_order_execution import IbkrOrderExecutionAdapter\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_factor_package_has_no_runtime_dependency(tmp_path: Path) -> None:
    root = tmp_path
    _write(root, "backend/src/qts/factors/bad.py", "from qts.runtime.actor import Actor\n")

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_research_package_has_no_runtime_dependency(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/research/bad.py",
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from qts.runtime.config import BacktestRuntimeConfig\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_research_package_has_no_runtime_execution_risk_or_portfolio_imports(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/research/bad.py",
        "from qts.execution.order_manager import OrderManager\n"
        "from qts.risk.standard_rules import StandardRiskRules\n"
        "from qts.portfolio.holdings import Holding\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_factor_package_has_no_runtime_execution_broker_imports(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/factors/bad.py",
        "from qts.execution.adapters.ibkr_order_execution import IbkrOrderExecutionAdapter\n"
        "from qts.portfolio.account_actor import AccountActor\n"
        "from qts.reconciliation import ReconciliationSnapshot\n",
    )

    assert "STRATEGY_SDK_INTERNAL_LEAK" in _codes(root)


def test_guardrails_reject_market_data_and_execution_adapter_coupling(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/adapters/bad.py",
        "from qts.execution.order_manager import OrderManager\n",
    )
    _write(
        root,
        "backend/src/qts/execution/adapters/bad.py",
        "from qts.data.adapters.ibkr_market_data import IbkrMarketDataAdapter\n",
    )

    assert _codes(root) == {"ADAPTER_BOUNDARY"}


def test_guardrails_reject_ibkr_transport_cross_boundary_imports(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/adapters/ibkr_transport.py",
        "from qts.execution.adapters.ibkr_order_execution import IbkrOrderExecutionAdapter\n",
    )
    _write(
        root,
        "backend/src/qts/execution/adapters/ibkr_transport.py",
        "from qts.data.adapters.ibkr_market_data import IbkrMarketDataAdapter\n",
    )

    assert _codes(root) == {"ADAPTER_BOUNDARY"}


def test_guardrails_reject_execution_adapter_state_dependency(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/execution/adapters/bad.py",
        "from qts.runtime.actors.account_actor import AccountActor\n"
        "from qts.portfolio.holdings import HoldingBook\n",
    )

    assert _codes(root) == {"ADAPTER_STATE_DEPENDENCY", "LAYER_DEPENDENCY"}


def test_guardrails_reject_removed_position_book_import(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "from qts.portfolio.position_book import PositionBook\n",
    )

    assert _codes(root) == {"REMOVED_IMPORT_USAGE"}


def test_guardrails_reject_product_specific_identifiers_in_core_implementation(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/bad.py",
        "GC_SESSION_OPEN = '18:00'\n\ndef gc_session_id_for_timestamp():\n    return None\n",
    )

    assert _codes(root) == {"PRODUCT_SPECIFIC_IMPLEMENTATION"}


def test_guardrails_reject_product_symbol_branching_in_core_implementation(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/bad.py",
        "def session_for(root: str) -> str:\n"
        "    if root == 'GC':\n"
        "        return 'special'\n"
        "    return 'generic'\n",
    )

    assert _codes(root) == {"PRODUCT_SPECIFIC_IMPLEMENTATION"}


def test_guardrails_reject_broker_specific_identifiers_outside_boundaries(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "IBKR_GATEWAY_NAME = 'ibkr-paper'\n",
    )

    assert _codes(root) == {"BROKER_SPECIFIC_IMPLEMENTATION"}


def test_guardrails_reject_broker_symbol_mapping_outside_boundary(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "from qts.registry.broker_symbol_mapping import BrokerSymbolMapping\n",
    )

    assert "BROKER_SYMBOL_BOUNDARY" in _codes(root)


def test_guardrails_reject_anchor_helpers_in_backend_source(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/anchor_helper.py",
        "class SessionRollAnchorRow:\n"
        "    pass\n\n"
        "def session_roll_anchor_payload() -> dict[str, object]:\n"
        "    return {}\n",
    )

    assert _codes(root) == {"TEST_SUPPORT_IN_PRODUCTION"}


def test_guardrails_reject_shared_roll_resolution_in_historical_boundary(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/session_roll.py",
        "def session_roll_resolution() -> None:\n    return None\n",
    )

    assert _codes(root) == {"SHARED_CAPABILITY_IN_SOURCE_BOUNDARY"}


def test_guardrails_reject_shared_session_resolution_in_backtest_boundary(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/session_resolution.py",
        "def session_resolution() -> None:\n    return None\n",
    )

    assert _codes(root) == {"SHARED_CAPABILITY_IN_SOURCE_BOUNDARY"}


def test_guardrails_reject_backtest_runner_replay_input_assembly(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/runner.py",
        "from qts.data.historical.csv_dataset import iter_historical_bars\n\n"
        "def _stream_configured_bars():\n"
        "    return iter_historical_bars\n",
    )

    assert _codes(root) == {"BACKTEST_RUNNER_COHESION"}


def test_guardrails_allow_backtest_runner_configured_catalog_boundary(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/runner.py",
        "from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig\n\n"
        "def run_backtest(config):\n"
        "    catalog_config = HistoricalCatalogLoadConfig.from_historical_market_data_config(\n"
        "        config.market_data.config_path,\n"
        "        catalog=config.market_data.catalog,\n"
        "        roots=config.roots,\n"
        "    )\n"
        "    return HistoricalCatalog.load(catalog_config)\n",
    )

    assert _codes(root) == set()


def test_guardrails_reject_backtest_input_catalog_construction(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/inputs.py",
        "from qts.data.historical.catalog import load_historical_catalog\n\n"
        "class ReplayMarketDataSource:\n"
        '    """Owns replay market data source test behavior."""\n'
        "    def _load_catalog(self):\n"
        "        return load_historical_catalog\n",
    )

    assert _codes(root) == {"BACKTEST_INPUT_COHESION"}


def test_guardrails_reject_public_factory_function_for_stable_concept(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/widget.py",
        "class WidgetConfig:\n"
        "    pass\n\n"
        "class Widget:\n"
        "    pass\n\n"
        "def load_widget(config: WidgetConfig) -> Widget:\n"
        "    return Widget()\n",
    )

    assert _codes(root) == {"OOP_PUBLIC_FACTORY_FUNCTION"}


def test_guardrails_allow_public_pure_algorithm_function(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/amounts.py",
        "from decimal import Decimal\n\n"
        "def combine_amounts(left: Decimal, right: Decimal) -> Decimal:\n"
        "    return left + right\n",
    )

    assert _codes(root) == set()


def test_guardrails_reject_private_helper_next_to_single_public_class(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/widget.py",
        "class Widget:\n"
        "    def __init__(self, payload: str) -> None:\n"
        "        self.payload = _normalize_payload(payload)\n\n"
        "def _normalize_payload(payload: str) -> str:\n"
        "    return payload.strip()\n",
    )

    assert _codes(root) == {"OOP_HELPER_OWNERSHIP"}


def test_guardrails_reject_private_helper_owned_by_one_class_in_multi_class_module(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/widget.py",
        "class WidgetConfig:\n"
        "    pass\n\n"
        "class Widget:\n"
        "    def __init__(self, payload: str) -> None:\n"
        "        self.payload = _normalize_payload(payload)\n\n"
        "def _normalize_payload(payload: str) -> str:\n"
        "    return payload.strip()\n",
    )

    assert _codes(root) == {"OOP_HELPER_OWNERSHIP"}


def test_guardrails_reject_apply_helper_owned_by_one_class_in_multi_class_module(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/widget.py",
        "class WidgetConfig:\n"
        "    pass\n\n"
        "class Widget:\n"
        "    def __init__(self, payload: str) -> None:\n"
        "        self.payload = payload\n\n"
        "    def render(self) -> str:\n"
        "        return _apply_payload(self.payload)\n\n"
        "def _apply_payload(payload: str) -> str:\n"
        "    return payload.strip()\n",
    )

    assert _codes(root) == {"OOP_HELPER_OWNERSHIP"}


def test_guardrails_allow_class_owned_private_helper(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/widget.py",
        "class Widget:\n"
        "    def __init__(self, payload: str) -> None:\n"
        "        self.payload = self._normalize_payload(payload)\n\n"
        "    @staticmethod\n"
        "    def _normalize_payload(payload: str) -> str:\n"
        "        return payload.strip()\n",
    )

    assert _codes(root) == set()


def test_guardrails_require_large_production_classes_in_boundary_matrix(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/domain/large_service.py",
        "class LargeService:\n"
        '    """Owns runtime test behavior for matrix coverage."""\n'
        + "\n".join(
            f"    def method_{index}(self):\n        return {index}" for index in range(155)
        )
        + "\n",
    )

    violations = run_guardrails(root)

    assert {violation.code for violation in violations} == {"CLASS_BOUNDARY_MATRIX"}
    assert violations[0].symbol == "qts.domain.large_service.LargeService"
    assert "over 300 lines" in violations[0].message


def test_guardrails_require_split_or_retain_evidence_for_very_large_classes(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/domain/large_service.py",
        "class LargeService:\n"
        '    """Owns runtime test behavior for matrix coverage."""\n'
        + "\n".join(
            f"    def method_{index}(self):\n        return {index}" for index in range(260)
        )
        + "\n",
    )
    _write(
        root,
        "docs/plan/backend_class_boundary_review_status_matrix.md",
        "# Backend Class Boundary Review Status Matrix\n\n"
        "| Class | Current lines | Owner | Risk | Decision | Target | Evidence | Status |\n"
        "| --- | ---: | --- | --- | --- | --- | --- | --- |\n"
        "| LargeService | 522 | runtime | High | Review | "
        "Split into lifecycle and routing owners |  | Open |\n",
    )

    violations = run_guardrails(root)

    assert {violation.code for violation in violations} == {"CLASS_BOUNDARY_MATRIX"}
    assert violations[0].symbol == "qts.domain.large_service.LargeService"
    assert "split/retain decision and evidence" in violations[0].message


def test_guardrails_allow_large_classes_with_matrix_decision_and_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/domain/large_service.py",
        "class LargeService:\n"
        '    """Owns runtime test behavior for matrix coverage."""\n'
        + "\n".join(
            f"    def method_{index}(self):\n        return {index}" for index in range(260)
        )
        + "\n",
    )
    _write(
        root,
        "docs/plan/backend_class_boundary_review_status_matrix.md",
        "# Backend Class Boundary Review Status Matrix\n\n"
        "| Class | Current lines | Owner | Risk | Decision | Target | Evidence | Status |\n"
        "| --- | ---: | --- | --- | --- | --- | --- | --- |\n"
        "| LargeService | 522 | runtime | High | Retain | Keep as facade pending split | "
        "`tests/unit/scripts/test_verify_guardrails.py` | Complete |\n",
    )

    assert run_guardrails(root) == []


def test_guardrails_require_ownership_verb_for_broad_class_suffix_docstrings(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/domain/services.py",
        "class RuntimeService:\n"
        '    """Runtime utilities for tests."""\n'
        "    pass\n\n"
        "class RuntimeCoordinator:\n"
        "    pass\n",
    )

    violations = run_guardrails(root)

    assert {violation.code for violation in violations} == {"CLASS_OWNERSHIP_DOCSTRING"}
    assert {violation.symbol for violation in violations} == {
        "qts.domain.services.RuntimeCoordinator",
        "qts.domain.services.RuntimeService",
    }


def test_guardrails_allow_ownership_verb_for_broad_suffix_classes_and_small_protocols(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/domain/services.py",
        "from typing import Protocol\n\n"
        "class RuntimeService:\n"
        '    """Owns runtime test behavior."""\n'
        "    pass\n\n"
        "class RuntimeCoordinator:\n"
        '    """Coordinates runtime test behavior."""\n'
        "    pass\n\n"
        "class MarketDataSource(Protocol):\n"
        "    def subscribe(self) -> None: ...\n",
    )

    assert run_guardrails(root) == []


def test_guardrails_reject_backtest_engine_historical_input_assembly(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/engine.py",
        "from qts.data.historical.config import HistoricalMarketDataConfig\n\n"
        "class BacktestEngine:\n"
        "    @staticmethod\n"
        "    def _contract_multipliers_from_config(config):\n"
        "        return HistoricalMarketDataConfig.from_yaml(config.market_data.config_path)\n",
    )

    assert _codes(root) == {"BACKTEST_ENGINE_COHESION"}


def test_guardrails_reject_backtest_engine_artifact_and_runtime_ownership(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/backtest/engine.py",
        "from qts.reporting.backtest import BacktestArtifactWriter\n"
        "from qts.runtime.actors.account_actor import AccountSnapshot\n"
        "from qts.runtime.sinks.backtest import BacktestRuntimeEventSink\n"
        "from qts.runtime.topology import RuntimeTopologyBuilder\n"
        "from qts.risk.rule_registry import RiskRuleRegistry\n"
        "from qts.risk.margin.calculator import MarginCalculator\n\n"
        "class BacktestEngine:\n"
        "    def run(self):\n"
        "        return (\n"
        "            BacktestArtifactWriter, AccountSnapshot, BacktestRuntimeEventSink,\n"
        "            RuntimeTopologyBuilder, RiskRuleRegistry, MarginCalculator,\n"
        "        )\n",
    )

    assert _codes(root) == {"BACKTEST_ENGINE_COHESION"}


def test_guardrails_allow_backtest_engine_type_only_runtime_import(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/backtest/engine.py",
        "from __future__ import annotations\n\n"
        "from typing import TYPE_CHECKING\n\n"
        "if TYPE_CHECKING:\n"
        "    from qts.runtime.actors.account_actor import AccountSnapshot\n\n"
        "class BacktestEngine:\n"
        "    def final_account(self) -> AccountSnapshot: ...\n",
    )

    assert _codes(root) == set()


def test_guardrails_reject_backtest_actor_loop_boundary_ownership(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/actor_loop.py",
        "from qts.data.historical.config import HistoricalMarketDataConfig\n"
        "from qts.reporting.backtest import BacktestArtifactWriter\n\n"
        "class BacktestActorLoop:\n"
        "    def run(self):\n"
        "        return HistoricalMarketDataConfig, BacktestArtifactWriter\n",
    )

    assert _codes(root) == {"BACKTEST_ACTOR_LOOP_COHESION"}


def test_guardrails_reject_backtest_actor_loop_private_helper_growth(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/actor_loop.py",
        "class BacktestActorLoop:\n"
        "    def run(self):\n"
        "        return None\n\n"
        "    def _resolve_actor_classes(self):\n"
        "        return None\n\n"
        "    def _write_account_snapshot(self):\n"
        "        return None\n\n"
        "    def _format_broker_capability_payload(self):\n"
        "        return None\n",
    )

    assert _codes(root) == {"BACKTEST_ACTOR_LOOP_COHESION"}


def test_guardrails_allow_product_facts_in_registry_providers(tmp_path: Path) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/registry/providers/comex_gold_calendar_provider.py",
        "GC_SESSION_OPEN = '18:00'\n"
        "class ComexGoldCalendarProvider:\n"
        "    calendar_id = 'COMEX.GC'\n",
    )

    assert run_guardrails(root) == []


def test_guardrails_reject_replay_classes_in_live_package(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/live/adapter.py",
        "class ReplayMarketDataAdapter:\n"
        '    """Adapts replay market data for guardrail tests."""\n'
        "    pass\n",
    )

    assert _codes(root) == {"LIVE_PACKAGE_REPLAY_CLASS"}


def test_guardrails_reject_fake_classes_in_production_data_package(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/live/fake_adapter.py",
        "class FakeMarketDataAdapter:\n"
        '    """Adapts fake market data for guardrail tests."""\n'
        "    pass\n",
    )

    assert _codes(root) == {"PRODUCTION_FAKE_CLASS"}


def test_guardrails_reject_fake_classes_outside_testing_package(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/fakes.py",
        "class FakeRuntimeSession:\n    pass\n",
    )
    _write(
        root,
        "backend/src/qts/testing/fakes/runtime.py",
        "class FakeRuntimeSession:\n    pass\n",
    )

    assert _codes_by_suite(root, guardrails.ProductionNoFakeClassRule()) == {
        "PRODUCTION_FAKE_CLASS"
    }


def test_guardrails_reject_shared_contract_classes_in_data_live_package(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/data/live/adapter.py",
        "class MarketDataAdapter:\n    pass\n",
    )
    _write(
        root,
        "backend/src/qts/data/live/events.py",
        "class MarketDataSourceEvent:\n    pass\n\nclass MarketDataSubscription:\n    pass\n",
    )

    assert _codes_by_suite(root, guardrails.DataLiveNoSharedContractRule()) == {
        "DATA_LIVE_SHARED_CONTRACT"
    }


def test_default_guardrails_reject_shared_contract_classes_in_data_live_package(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/live/adapter.py",
        'class MarketDataAdapter:\n    """Adapts market data for guardrail tests."""\n    pass\n',
    )

    assert _codes(root) == {"DATA_LIVE_SHARED_CONTRACT"}


def test_guardrails_reject_transport_canonical_classes_in_adapters(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/data/adapters/ibkr_transport.py",
        "class IbkrTwsMarketDataTransport:\n    pass\n",
    )
    _write(
        root,
        "backend/src/qts/execution/adapters/ibkr_transport.py",
        "class IbkrTwsOrderExecutionTransport:\n    pass\n",
    )
    _write(
        root,
        "backend/src/qts/data/transports/ibkr_tws_market_data_transport.py",
        "class IbkrTwsMarketDataTransport:\n    pass\n",
    )

    assert _codes_by_suite(root, guardrails.TransportCanonicalPathRule()) == {
        "TRANSPORT_CANONICAL_PATH"
    }


def test_default_guardrails_reject_transport_canonical_classes_in_adapters(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/adapters/ibkr_transport.py",
        "class IbkrTwsMarketDataTransport:\n    pass\n",
    )

    assert _codes(root) == {"TRANSPORT_CANONICAL_PATH"}


def test_guardrails_reject_removed_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session_consumer.py",
        "from qts.runtime.live_runtime_session import LiveRuntimeSession\n",
    )
    _write(
        root,
        "backend/src/qts/data/consumer.py",
        "from qts.data.live.events import FeedSubscription\n",
    )
    _write(
        root,
        "backend/src/qts/runtime/start_runtime_consumer.py",
        "from qts.application.commands.start_paper import start_paper\n",
    )
    _write(
        root,
        "backend/src/qts/reporting/old_report_consumer.py",
        "from qts.reporting.live import LiveReportWriter\n",
    )

    assert _codes_by_suite(root, guardrails.RemovedImportNoNewUsageRule()) == {
        "REMOVED_IMPORT_USAGE"
    }


def test_guardrails_reject_removed_simulated_broker_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/execution_consumer.py",
        "from qts.execution.simulator.simulated_broker import SimulatedBroker\n",
    )
    _write(
        root,
        "backend/src/qts/runtime/execution_package_consumer.py",
        "from qts.execution.simulator import SimulatedBroker\n",
    )

    violations = guardrails.GuardrailSuite(rules=(guardrails.RemovedImportNoNewUsageRule(),)).check(
        root
    )

    assert {violation.code for violation in violations} == {"REMOVED_IMPORT_USAGE"}
    assert {violation.symbol for violation in violations} == {
        "qts.execution.simulator.simulated_broker.SimulatedBroker",
        "qts.execution.simulator.SimulatedBroker",
    }


def test_guardrails_reject_removed_fake_broker_adapter_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/testing/consumer.py",
        "from qts.testing.fakes.broker import FakeBrokerAdapter\n",
    )
    _write(
        root,
        "backend/src/qts/testing/package_consumer.py",
        "from qts.testing import FakeBrokerAdapter\n",
    )

    violations = guardrails.GuardrailSuite(rules=(guardrails.RemovedImportNoNewUsageRule(),)).check(
        root
    )

    assert {violation.code for violation in violations} == {"REMOVED_IMPORT_USAGE"}
    assert {violation.symbol for violation in violations} == {
        "qts.testing.fakes.broker.FakeBrokerAdapter",
        "qts.testing.FakeBrokerAdapter",
    }


def test_guardrails_reject_removed_runtime_live_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session_consumer.py",
        "from qts.runtime.live import RuntimeOrderResult\n",
    )

    assert _codes_by_suite(root, guardrails.RemovedImportNoNewUsageRule()) == {
        "REMOVED_IMPORT_USAGE"
    }


def test_guardrails_reject_removed_live_runtime_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session_consumer.py",
        "from qts.runtime.live import LiveRuntime\n",
    )

    violations = guardrails.GuardrailSuite(rules=(guardrails.RemovedImportNoNewUsageRule(),)).check(
        root
    )

    assert {violation.code for violation in violations} == {"REMOVED_IMPORT_USAGE"}
    assert violations[0].symbol == "qts.runtime.live.LiveRuntime"


def test_guardrails_reject_removed_m1_runtime_naming_imports(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/removed_m1_consumer.py",
        "from qts.runtime.config import LiveRuntimeConfig\n"
        "from qts.runtime.config.paper import PaperBrokerRuntimeConfig\n"
        "from qts.runtime.permissions import LiveOrderPermission\n"
        "from qts.runtime.sinks.live import LiveRuntimeEventSink\n"
        "from qts.runtime.live_reconciliation import LiveReconciliation\n"
        "from qts.runtime.state_recovery import LiveRecoveryDecision\n",
    )

    assert _codes_by_suite(root, guardrails.RemovedImportNoNewUsageRule()) == {
        "REMOVED_IMPORT_USAGE"
    }


def test_removed_live_alias_imports_fail(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/removed_live_alias_consumer.py",
        "from qts.runtime.config import LiveRuntimeConfig\n"
        "from qts.runtime.sinks import LiveRuntimeEventSink\n"
        "from qts.runtime.permissions import LiveOrderPermission\n"
        "from qts.runtime.live_reconciliation import LiveReconciliation\n"
        "from qts.runtime.state_recovery import LiveRecoveryDecision\n"
        "from qts.runtime.sinks.live import LiveRuntimeEventSink as OldSink\n"
        "from qts.reporting.live import LiveReportWriter\n",
    )

    violations = guardrails.GuardrailSuite(rules=(guardrails.RemovedImportNoNewUsageRule(),)).check(
        root
    )

    assert {violation.code for violation in violations} == {"REMOVED_IMPORT_USAGE"}
    assert {violation.symbol for violation in violations} == {
        "qts.runtime.config.LiveRuntimeConfig",
        "qts.runtime.sinks.LiveRuntimeEventSink",
        "qts.runtime.permissions.LiveOrderPermission",
        "qts.runtime.live_reconciliation.LiveReconciliation",
        "qts.runtime.state_recovery.LiveRecoveryDecision",
        "qts.runtime.sinks.live.LiveRuntimeEventSink",
        "qts.reporting.live",
    }


def test_guardrails_allow_canonical_broker_startup_and_order_result_imports(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session_consumer.py",
        "from qts.runtime.broker_startup import BrokerRuntimeStartupDecision\n"
        "from qts.runtime.order_result import RuntimeOrderResult\n",
    )

    assert _codes_by_suite(root, guardrails.RemovedImportNoNewUsageRule()) == set()


def test_default_guardrails_reject_removed_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/session_consumer.py",
        "from qts.runtime.live_runtime_session import LiveRuntimeSession\n",
    )

    assert _codes(root) == {"REMOVED_IMPORT_USAGE"}


def test_guardrails_reject_old_live_report_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/reporting/old_report_consumer.py",
        "from qts.reporting.live import LiveReportWriter\n",
    )

    assert _codes_by_suite(root, guardrails.RemovedImportNoNewUsageRule()) == {
        "REMOVED_IMPORT_USAGE"
    }


def test_guardrails_reject_old_live_report_export_name_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/reporting/old_report_consumer.py",
        "from qts.reporting import LiveReportWriter\n",
    )

    assert _codes_by_suite(root, guardrails.RemovedImportNoNewUsageRule()) == {
        "REMOVED_IMPORT_USAGE"
    }


def test_default_guardrails_reject_removed_transport_import_usage(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/transport_consumer.py",
        "from qts.data.adapters.ibkr_transport import IbkrTwsMarketDataTransport\n"
        "from qts.execution.adapters.ibkr_async_transport import "
        "IbAsyncOrderExecutionTransport\n",
    )
    _write(
        root,
        "backend/src/qts/data/adapters/ibkr_transport.py",
        "from qts.data.transports.ibkr_tws_market_data_transport import "
        "IbkrTwsMarketDataTransport\n",
    )
    _write(
        root,
        "backend/src/qts/execution/adapters/ibkr_async_transport.py",
        "from qts.execution.transports.ib_async_order_execution_transport import "
        "IbAsyncOrderExecutionTransport\n",
    )

    assert _codes(root) == {"REMOVED_IMPORT_USAGE", "RUNTIME_EXECUTION_BOUNDARY"}


def test_default_guardrails_reject_transport_importing_adapter_modules(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/execution/transports/ibkr_bad_transport.py",
        "from qts.execution.adapters.ibkr_order_execution import IbkrOrderExecutionAdapter\n",
    )
    _write(
        root,
        "backend/src/qts/data/transports/ibkr_bad_transport.py",
        "from qts.data.adapters.ibkr_market_data import IbkrMarketDataAdapter\n",
    )

    assert _codes(root) == {"TRANSPORT_ADAPTER_IMPORT"}


def test_guardrails_reject_production_imports_from_qts_testing(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter\n",
    )
    _write(
        root,
        "backend/src/qts/testing/consumer.py",
        "from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter\n",
    )

    assert _codes_by_suite(root, guardrails.ProductionNoTestingImportRule()) == {
        "PRODUCTION_TESTING_IMPORT"
    }


def test_default_guardrails_reject_production_imports_from_qts_testing(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter\n",
    )

    assert _codes(root) == {"PRODUCTION_TESTING_IMPORT"}


def test_guardrails_reject_pipeline_importing_runtime_actor(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/bars/pipeline.py",
        "from qts.runtime.actor_ref import ActorRef\n",
    )

    assert _codes(root) == {"PIPELINE_ACTOR_IMPORT", "LAYER_DEPENDENCY"}


def test_guardrails_reject_transport_importing_runtime_actor(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/adapters/ibkr_transport.py",
        "from qts.runtime.actors.account_actor import AccountActor\n",
    )

    assert _codes(root) == {"TRANSPORT_ACTOR_IMPORT", "LAYER_DEPENDENCY"}


def test_guardrails_reject_provider_sdk_import_in_runtime(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "from ib_async import IB\n",
    )

    assert _codes(root) == {"PROVIDER_SDK_IMPORT"}


def test_guardrails_reject_research_run_research_scripts(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "scripts/research/run_factor_research.py",
        '"""One-off research runner shortcut."""\n',
    )

    assert _codes(root) == {"RESEARCH_RUN_SCRIPT"}


def test_guardrails_reject_vwap_research_runner_scripts(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "scripts/research/run_vwap_smoke.py",
        '"""One-off VWAP research runner shortcut."""\n',
    )

    assert _codes(root) == {"RESEARCH_RUN_SCRIPT", "VWAP_ADHOC_RUNNER_FORBIDDEN"}


def test_guardrails_reject_nested_vwap_research_runner_scripts(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "scripts/research/archive/run_vwap_smoke.py",
        '"""Nested one-off VWAP research runner shortcut."""\n',
    )

    assert _codes(root) == {"RESEARCH_RUN_SCRIPT", "VWAP_ADHOC_RUNNER_FORBIDDEN"}


@pytest.mark.parametrize(
    "relative_path",
    [
        "configs/optimizer/vwap_factor_search.yaml",
        "configs/optimizer/gc_vwap_factor_search.yaml",
        "configs/optimizer/vwap_factor_search.yml",
    ],
)
def test_guardrails_reject_vwap_optimizer_configs(
    tmp_path: Path,
    relative_path: str,
) -> None:
    root = tmp_path
    _write(
        root,
        relative_path,
        "objective_metric: sharpe_ratio\n",
    )

    assert _codes(root) == {"VWAP_OPTIMIZER_CONFIG", "VWAP_ADHOC_RUNNER_FORBIDDEN"}


def test_guardrails_reject_vwap_adhoc_runner_scripts(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "scripts/research/run_vwap_smoke.py",
        '"""One-off VWAP research runner shortcut."""\n',
    )

    assert "VWAP_ADHOC_RUNNER_FORBIDDEN" in _codes(root)


def test_guardrails_reject_nested_vwap_adhoc_runner_scripts(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "scripts/research/archive/run_vwap_smoke.py",
        '"""Nested one-off VWAP research runner shortcut."""\n',
    )

    assert "VWAP_ADHOC_RUNNER_FORBIDDEN" in _codes(root)


@pytest.mark.parametrize(
    "relative_path",
    [
        "configs/optimizer/vwap_factor_search.yaml",
        "configs/optimizer/gc_vwap_factor_search.yaml",
        "configs/optimizer/vwap_factor_search.yml",
    ],
)
def test_guardrails_reject_vwap_adhoc_optimizer_configs(
    tmp_path: Path,
    relative_path: str,
) -> None:
    root = tmp_path
    _write(
        root,
        relative_path,
        "objective_metric: sharpe_ratio\n",
    )

    assert "VWAP_ADHOC_RUNNER_FORBIDDEN" in _codes(root)


def test_guardrails_reject_vwap_adhoc_runner_and_optimizer_combined(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "scripts/research/run_vwap_alpha.py",
        '"""One-off VWAP alpha runner."""\n',
    )
    _write(
        root,
        "configs/optimizer/vwap_alpha_search.yaml",
        "objective_metric: sharpe_ratio\n",
    )

    codes = _codes(root)
    assert "VWAP_ADHOC_RUNNER_FORBIDDEN" in codes
    # Both files should be flagged by the unified rule.
    violations = [v for v in run_guardrails(root) if v.code == "VWAP_ADHOC_RUNNER_FORBIDDEN"]
    assert len(violations) == 2


def test_guardrails_vwap_adhoc_runner_forbidden_passes_clean_repo(tmp_path: Path) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)

    assert "VWAP_ADHOC_RUNNER_FORBIDDEN" not in _codes(root)


def test_guardrails_allow_quickstart_optimizer_config(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/optimizer/quickstart.yaml",
        Path("configs/optimizer/quickstart.yaml").read_text(encoding="utf-8"),
    )

    assert _codes(root) == set()


def test_guardrails_reject_production_strategy_imports_from_research(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "strategies/production/bad.py",
        "from strategies.research.vwap_factor_research import VwapFactorResearchStrategy\n",
    )

    assert _codes(root) == {"PRODUCTION_STRATEGY_IMPORT"}


def test_guardrails_reject_production_strategy_imports_from_examples(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "strategies/production/bad.py",
        "import examples.strategies.vwap_pullback_v2\n",
    )

    assert _codes(root) == {"PRODUCTION_STRATEGY_IMPORT"}


@pytest.mark.parametrize(
    "forbidden_key",
    ["generate_code", "promote", "paper", "live", "broker", "orders", "runtime", "trade"],
)
def test_guardrails_reject_research_workflow_runtime_keys_anywhere(
    tmp_path: Path, forbidden_key: str
) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/workflows/bad.yaml",
        "version: 1\n"
        "steps:\n"
        "  - id: shortcut\n"
        "    kind: research\n"
        "    nested:\n"
        f"      {forbidden_key}: true\n",
    )

    violations = [
        violation for violation in run_guardrails(root) if violation.code != "PLATFORM_FREEZE"
    ]

    assert {violation.code for violation in violations} == {"RESEARCH_WORKFLOW_RUNTIME_KEY"}
    assert {violation.symbol for violation in violations} == {forbidden_key}


def test_guardrails_scan_nested_research_workflow_runtime_keys(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/workflows/routes/bad.yaml",
        "version: 1\nruntime: live\n",
    )

    assert "RESEARCH_WORKFLOW_RUNTIME_KEY" in _codes(root)


def test_guardrail_rejects_promotion_without_evidence_bundle(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\nstatus: review_required\nidea_id: idea_001\n",
    )

    assert "EVIDENCE_BUNDLE_REQUIRED_FOR_PROMOTION" in _codes(root)


def test_guardrail_rejects_candidate_without_idea_id(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\nevidence_bundle_id: evb_001\nstatus: paper_candidate\n"
        "paper_readiness:\n  trade_diagnostics_available: true\n",
    )

    assert "IDEA_REGISTRY_REQUIRED_FOR_CANDIDATE" in _codes(root)


def test_guardrail_rejects_paper_candidate_without_diagnostics(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\nevidence_bundle_id: evb_001\nidea_id: idea_001\n"
        "status: paper_candidate\npaper_readiness:\n  trade_diagnostics_available: false\n",
    )

    assert "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER" in _codes(root)


def test_guardrail_rejects_paper_candidate_without_validation_scorecard(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\nevidence_bundle_id: evb_001\nidea_id: idea_001\n"
        "status: paper_candidate\npaper_readiness:\n"
        "  trade_diagnostics_available: true\n"
        "  cost_stress_available: true\n",
    )

    assert "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER" in _codes(root)


def test_guardrail_rejects_paper_candidate_without_cost_stress(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\nevidence_bundle_id: evb_001\nidea_id: idea_001\n"
        "status: paper_candidate\npaper_readiness:\n"
        "  trade_diagnostics_available: true\n"
        "  validation_scorecard_available: true\n",
    )

    assert "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER" in _codes(root)


def test_guardrail_rejects_small_live_candidate_without_diagnostics(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\nevidence_bundle_id: evb_001\nidea_id: idea_001\n"
        "status: small_live_candidate\npaper_readiness:\n"
        "  trade_diagnostics_available: false\n"
        "  validation_scorecard_available: true\n"
        "  cost_stress_available: true\n",
    )

    assert "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER" in _codes(root)


def test_guardrail_rejects_promotion_spec_with_unreviewed_examples_source(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/example.yaml",
        "promotion_candidate_id: pc_001\n"
        "strategy_id: example\n"
        "source_module: examples.strategies.gc_si_momentum\n"
        "target_module: strategies.production.gc_si_momentum\n"
        "evidence_bundle_id: evb_001\n"
        "status: review_required\n",
    )

    assert "PROMOTION_CONFIG_BOUNDARY" in _codes(root)


def test_guardrail_rejects_promotion_target_outside_production_namespace(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\n"
        "strategy_id: vwap\n"
        "source_module: strategies.research.vwap_factor_research\n"
        "target_module: strategies.research.vwap_factor_research_live\n"
        "evidence_bundle_id: evb_001\n"
        "status: review_required\n",
    )

    assert "PROMOTION_CONFIG_BOUNDARY" in _codes(root)


def test_guardrail_rejects_promotion_spec_with_research_only_params(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/promotion/vwap.yaml",
        "promotion_candidate_id: pc_001\n"
        "strategy_id: vwap\n"
        "source_module: strategies.research.vwap_factor_research\n"
        "target_module: strategies.production.vwap_production_pullback\n"
        "evidence_bundle_id: evb_001\n"
        "status: review_required\n"
        "production_params:\n"
        "  trial_budget: 30\n",
    )

    assert "PROMOTION_CONFIG_BOUNDARY" in _codes(root)


def test_guardrail_rejects_route_workflow_without_route_metadata(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/workflows/routes/route_a.yaml",
        "version: 1\nworkflow_id: route-a\nsteps:\n  - id: report\n    kind: research_report\n",
    )

    assert "ROUTE_METADATA_REQUIRED" in _codes(root)


def test_guardrail_rejects_research_report_without_decision_block(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "runs/research/reports/workflow-report.md",
        "# Research Workflow Report\n\n## Evidence Summary\n",
    )

    assert "RESEARCH_REPORT_DECISION_REQUIRED" in _codes(root)


def test_guardrail_skips_gitignored_research_run_outputs(tmp_path: Path) -> None:
    root = tmp_path
    _write(root, ".gitignore", "runs/\n")
    _write(
        root,
        "runs/research/reports/workflow-report.md",
        "# Research Workflow Report\n\n## Evidence Summary\n",
    )

    assert "RESEARCH_REPORT_DECISION_REQUIRED" not in _codes(root)


def test_guardrail_rejects_research_strategy_stale_examples_docstring(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "strategies/research/vwap_factor_research.py",
        '"""This strategy intentionally lives under examples."""\n',
    )

    assert "RESEARCH_STRATEGY_STALE_DOCSTRING" in _codes(root)


def test_guardrails_allow_valid_research_workflow(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "configs/research/workflows/quickstart.yaml",
        Path("configs/research/workflows/quickstart.yaml").read_text(encoding="utf-8"),
    )

    assert _codes(root) == set()


def test_guardrail_report_contains_remediation(tmp_path: Path) -> None:
    root = tmp_path
    _write_platform_freeze_stub(root)
    _write(
        root,
        "backend/src/qts/domain/bad.py",
        "from qts.runtime.actor import Actor\n",
    )

    violation = run_guardrails(root)[0]
    assert violation.remediation
    assert "remediation:" in violation.format()


def test_guardrails_reject_shared_runtime_backtest_only_docstring(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/intent_processing.py",
        "class TargetIntentProcessor:\n"
        '    """Translate strategy target intents into validated backtest orders."""\n',
    )

    assert _codes(root) == {"SHARED_RUNTIME_WORDING"}


def test_guardrails_reject_shared_runtime_module_mode_specific_wording(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/intent_processing.py",
        '"""Backtest intent processing."""\n',
    )

    assert _codes(root) == {"SHARED_RUNTIME_WORDING"}


def test_guardrails_reject_shared_runtime_fake_adapter_wording(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/live.py",
        '"""Live runtime lifecycle and fake-adapter orchestration."""\n',
    )

    assert _codes(root) == {"SHARED_RUNTIME_WORDING"}


def test_runtime_session_complexity_budget_passes(tmp_path: Path) -> None:
    root = tmp_path
    branch_method = "\n".join(
        f"        if value == {index}:\n            return {index}" for index in range(10)
    )
    public_methods = "\n".join(
        (f"    def public_0(self, value):\n{branch_method}\n        return None")
        if index == 0
        else f"    def public_{index}(self):\n        pass"
        for index in range(14)
    )
    private_helpers = "\n".join(
        f"    def _helper_{index}(self):\n        pass" for index in range(8)
    )
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        f"class RuntimeSession:\n{public_methods}\n{private_helpers}\n",
    )

    assert _codes_by_suite(root, _load_guardrails_module().RuntimeSessionComplexityRule()) == set()


def test_guardrails_reject_runtime_session_complexity_without_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path
    methods = "\n".join(f"    def public_{index}(self):\n        pass" for index in range(15))
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        f"class RuntimeSession:\n{methods}\n\n    def _helper_0(self):\n        pass\n",
    )

    assert _codes(root) == {"RUNTIME_SESSION_COMPLEXITY"}


def test_runtime_session_does_not_import_ibkr_transport(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        "from qts.execution.transports.ibkr_tws_order_client import IbkrTwsOrderClient\n\n"
        "class RuntimeSession:\n"
        "    def start(self):\n"
        "        return IbkrTwsOrderClient\n",
    )

    assert _codes_by_suite(root, _load_guardrails_module().RuntimeSessionComplexityRule()) == {
        "RUNTIME_SESSION_COMPLEXITY"
    }


def test_runtime_session_does_not_apply_account_mutation_directly(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        "class RuntimeSession:\n"
        "    def on_fill(self, partition, message):\n"
        "        partition.account_actor._apply_fill(message)\n",
    )

    assert _codes_by_suite(root, _load_guardrails_module().RuntimeSessionComplexityRule()) == {
        "RUNTIME_SESSION_COMPLEXITY"
    }


def test_guardrails_reject_runtime_coordinator_without_decision_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/recovery.py",
        "class RuntimeRecoveryCoordinator:\n"
        '    """Coordinates runtime recovery test behavior."""\n'
        "    def recover(self):\n"
        "        pass\n",
    )

    assert _codes(root) == {"RUNTIME_COORDINATOR_DECISION"}


def test_every_runtime_coordinator_has_decision_record(tmp_path: Path) -> None:
    root = tmp_path
    coordinator_sources = {
        "backend/src/qts/runtime/recovery.py": "RuntimeRecoveryCoordinator",
        "backend/src/qts/runtime/rollback.py": "RuntimeRollbackCoordinator",
        "backend/src/qts/runtime/broker_lifecycle.py": "RuntimeBrokerLifecycleCoordinator",
        "backend/src/qts/runtime/market_data_coordinator.py": "RuntimeMarketDataCoordinator",
        "backend/src/qts/runtime/safety_controller.py": "RuntimeSafetyController",
        "backend/src/qts/runtime/startup_gate.py": "BrokerRuntimeStartupGate",
        "backend/src/qts/runtime/broker_runtime_topology.py": "BrokerRuntimeTopologyResolver",
    }
    for relative_path, class_name in coordinator_sources.items():
        _write(
            root,
            relative_path,
            f"class {class_name}:\n"
            '    """Coordinates runtime decision test behavior."""\n'
            "    pass\n",
        )
    _write(
        root,
        "docs/architecture/runtime_coordinator_decisions.md",
        "# Runtime Coordinator Decisions\n\n"
        "| Candidate | Decision | Evidence | Gate |\n"
        "| --- | --- | --- | --- |\n"
        "| RuntimeRecoveryCoordinator | Keep | state/policy | gate |\n"
        "| RuntimeRollbackCoordinator | Keep | safety boundary | gate |\n"
        "| RuntimeBrokerLifecycleCoordinator | Keep | external boundary | gate |\n"
        "| RuntimeMarketDataCoordinator | Keep | complexity threshold | gate |\n"
        "| RuntimeSafetyController | Keep | safety boundary | gate |\n"
        "| BrokerRuntimeStartupGate | Keep | independent test value | gate |\n",
    )

    assert _codes(root) == {"RUNTIME_COORDINATOR_DECISION"}


def test_deleted_coordinator_has_no_production_import(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        "from qts.runtime.recovery import RuntimeRecoveryCoordinator\n",
    )
    _write(
        root,
        "docs/architecture/runtime_coordinator_decisions.md",
        "# Runtime Coordinator Decisions\n\n"
        "| Candidate | Decision | Evidence | Gate |\n"
        "| --- | --- | --- | --- |\n"
        "| RuntimeRecoveryCoordinator | Delete | no production references | gate |\n",
    )

    assert _codes(root) == {"RUNTIME_COORDINATOR_DECISION"}


def test_kept_coordinator_has_state_policy_or_evidence_responsibility(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/recovery.py",
        "class RuntimeRecoveryCoordinator:\n"
        '    """Coordinates runtime recovery tests."""\n'
        "    pass\n",
    )
    _write(
        root,
        "docs/architecture/runtime_coordinator_decisions.md",
        "# Runtime Coordinator Decisions\n\n"
        "| Candidate | Decision | Evidence | Gate |\n"
        "| --- | --- | --- | --- |\n"
        "| RuntimeRecoveryCoordinator | Keep | convenience wrapper | gate |\n",
    )

    assert _codes(root) == {"RUNTIME_COORDINATOR_DECISION"}


def test_guardrails_reject_placeholder_docstrings_in_production(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/reporting/base.py",
        'class ReportWriter:\n    """Boundary placeholder for report generation."""\n',
    )

    assert _codes(root) == {"PLACEHOLDER_DOCSTRING"}


def test_guardrails_reject_stale_architecture_runtime_text(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "docs/architecture/runtime_value_model_boundaries.md",
        "| RuntimeOrderResult | qts.runtime.live | runtime result |\n",
    )

    assert _codes_by_suite(root, guardrails.StaleArchitectureTextRule()) == {
        "STALE_ARCHITECTURE_TEXT"
    }


def test_guardrails_reject_stale_architecture_html_runtime_text(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "docs/architecture/runtime_architecture.html",
        "<section>LiveRuntimeSession</section>\n",
    )

    assert _codes_by_suite(root, guardrails.StaleArchitectureTextRule()) == {
        "STALE_ARCHITECTURE_TEXT"
    }


def test_guardrails_allow_canonical_architecture_runtime_text(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "docs/architecture/runtime_value_model_boundaries.md",
        "| RuntimeOrderResult | qts.runtime.order_result | runtime result |\n",
    )

    assert _codes_by_suite(root, guardrails.StaleArchitectureTextRule()) == set()


def test_guardrails_reject_runtime_importing_execution_internal_types(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        "from qts.execution.order_manager import OrderFill\n",
    )

    assert _codes_by_suite(root, guardrails.RuntimeExecutionBoundaryRule()) == {
        "RUNTIME_EXECUTION_BOUNDARY"
    }


def test_guardrails_allow_runtime_importing_whitelisted_execution_types(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        "from qts.execution.order_manager import OrderManager\n"
        "from qts.execution.execution_adapter import ExecutionAdapter\n"
        "from qts.execution.idempotency import FillIdempotencyStore\n"
        "from qts.execution.broker import BrokerExecutionReport\n",
    )

    assert _codes_by_suite(root, guardrails.RuntimeExecutionBoundaryRule()) == set()


def test_guardrails_allow_non_runtime_importing_execution_types(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/reporting/consumer.py",
        "from qts.execution.order_manager import OrderFill\n",
    )

    assert _codes_by_suite(root, guardrails.RuntimeExecutionBoundaryRule()) == set()


def test_guardrails_pass_current_repository() -> None:
    assert run_guardrails(Path(".")) == []


def test_guardrail_suite_can_target_single_rule(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/bad.py",
        "from qts.runtime.actor import Actor\n",
    )
    assert _codes_by_suite(root, _load_guardrails_module().ImportBoundaryRule()) == {
        "IMPORT_BOUNDARY"
    }


def test_guardrail_suite_can_target_product_specific_rule(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/bad.py",
        "GC_SESSION_OPEN = '18:00'\n",
    )
    assert _codes_by_suite(root, _load_guardrails_module().ProductSpecificRule()) == {
        "PRODUCT_SPECIFIC_IMPLEMENTATION"
    }


def test_guardrail_script_extends_canonical_quality_entrypoint() -> None:
    source = Path("scripts/verify_guardrails.py").read_text(encoding="utf-8")
    guardrails = _load_guardrails_module()

    assert "qts.quality.guardrails" not in source
    assert "from qts.quality import" in source
    assert guardrails.GuardrailSuite.__mro__[1].__module__ == "qts.quality.suite"
    assert guardrails.ProductionPlaceholderDocstringRule.__module__.startswith("qts.quality.rules.")
    assert guardrails.ResearchRunScriptRule.__module__ == "qts.quality.rules.flows"


def test_all_guardrail_rules_live_under_rule_modules() -> None:
    guardrails = _load_guardrails_module()

    rule_modules = {rule.__class__.__module__ for rule in guardrails.GuardrailSuite().rules}

    assert rule_modules
    assert all(module.startswith("qts.quality.rules.") for module in rule_modules)
    assert "qts.quality.guardrails" not in rule_modules


def test_guardrail_suite_default_preserves_expected_codes(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/bad.py",
        "from qts.runtime.actor import Actor\nGC_SESSION_OPEN = '18:00'\n",
    )
    root_codes = _codes(root)
    suite_codes = _codes_by_suite(root, *_load_guardrails_module().GuardrailSuite().rules)
    assert root_codes == suite_codes


def test_guardrail_suite_includes_required_m0_hard_gate_rules() -> None:
    guardrails = _load_guardrails_module()
    rules = guardrails.GuardrailSuite().rules
    rule_names = {rule.__class__.__name__ for rule in rules}
    rule_codes = {rule.code for rule in rules}

    assert {
        "ImportBoundaryRule",
        "LivePackageNoReplayClassRule",
        "ProductionNoFakeClassRule",
        "DataLiveNoSharedContractRule",
        "TransportCanonicalPathRule",
        "RemovedImportNoNewUsageRule",
        "ProductionNoTestingImportRule",
        "SharedRuntimeWordingRule",
        "ProductionPlaceholderDocstringRule",
        "BrokerSymbolBoundaryRule",
        "ProviderSdkImportRule",
        "StrategySdkPublicSurfaceRule",
        "StaleArchitectureTextRule",
        "PlatformFreezeRule",
        "RuntimeExecutionBoundaryRule",
    } <= rule_names
    assert {
        "RESEARCH_RUN_SCRIPT",
        "VWAP_OPTIMIZER_CONFIG",
        "VWAP_ADHOC_RUNNER_FORBIDDEN",
        "PRODUCTION_STRATEGY_IMPORT",
        "RESEARCH_WORKFLOW_RUNTIME_KEY",
        "EVIDENCE_BUNDLE_REQUIRED_FOR_PROMOTION",
        "IDEA_REGISTRY_REQUIRED_FOR_CANDIDATE",
        "TRADE_DIAGNOSTICS_REQUIRED_FOR_PAPER",
        "ROUTE_METADATA_REQUIRED",
        "RESEARCH_REPORT_DECISION_REQUIRED",
        "RESEARCH_STRATEGY_STALE_DOCSTRING",
    } <= rule_codes


def test_guardrail_report_contains_rule_path_symbol_and_guidance(tmp_path: Path) -> None:
    root = tmp_path
    guardrails = _load_guardrails_module()
    _write(
        root,
        "backend/src/qts/runtime/session_consumer.py",
        "from qts.runtime.live import LiveRuntime\n",
    )

    violation = guardrails.GuardrailSuite(rules=(guardrails.RemovedImportNoNewUsageRule(),)).check(
        root
    )[0]

    report = violation.format()
    assert "backend/src/qts/runtime/session_consumer.py:1" in report
    assert "REMOVED_IMPORT_USAGE" in report
    assert "qts.runtime.live.LiveRuntime" in report
    assert "remediation:" in report


def test_ci_and_pre_commit_run_architecture_guardrails() -> None:
    workflow = Path(".github/workflows/quality.yml").read_text(encoding="utf-8")
    pre_commit = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "make guardrails" in workflow
    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "make test-unit" in workflow
    assert "make guardrails" in pre_commit
    assert "tests/quality/test_platform_freeze.py" in workflow


def test_make_check_keeps_guardrails_before_tests() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert (
        "check: format lint guardrails typecheck test-unit test-integration test-anchor" in makefile
    )
