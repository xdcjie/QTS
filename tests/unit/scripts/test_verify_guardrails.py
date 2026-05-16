from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast


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


def _write(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _codes(root: Path) -> set[str]:
    return {violation.code for violation in run_guardrails(root)}


def _codes_by_suite(root: Path, *rules: object) -> set[str]:
    suite = _load_guardrails_module().GuardrailSuite(rules=tuple(rules))
    return {violation.code for violation in suite.check(root)}


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

    assert _codes(root) == {"STRATEGY_SDK_INTERNAL_LEAK"}


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
        "from qts.portfolio.position_book import PositionBook\n",
    )

    assert _codes(root) == {"ADAPTER_STATE_DEPENDENCY"}


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
        "class ReplayMarketDataAdapter:\n    pass\n",
    )

    assert _codes(root) == {"LIVE_PACKAGE_REPLAY_CLASS"}


def test_guardrails_reject_fake_classes_in_production_data_package(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/live/fake_adapter.py",
        "class FakeMarketDataAdapter:\n    pass\n",
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
        "class MarketDataAdapter:\n    pass\n\nclass StreamingFeedAdapter:\n    pass\n",
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
        "class MarketDataAdapter:\n    pass\n",
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

    assert _codes(root) == {"REMOVED_IMPORT_USAGE"}


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
        "from qts.testing.fakes.broker import FakeBrokerAdapter\n",
    )
    _write(
        root,
        "backend/src/qts/testing/consumer.py",
        "from qts.testing.fakes.broker import FakeBrokerAdapter\n",
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
        "from qts.testing.fakes.broker import FakeBrokerAdapter\n",
    )

    assert _codes(root) == {"PRODUCTION_TESTING_IMPORT"}


def test_guardrails_reject_pipeline_importing_runtime_actor(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/bars/pipeline.py",
        "from qts.runtime.actor_ref import ActorRef\n",
    )

    assert _codes(root) == {"PIPELINE_ACTOR_IMPORT"}


def test_guardrails_reject_transport_importing_runtime_actor(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/adapters/ibkr_transport.py",
        "from qts.runtime.actors.account_actor import AccountActor\n",
    )

    assert _codes(root) == {"TRANSPORT_ACTOR_IMPORT"}


def test_guardrails_reject_provider_sdk_import_in_runtime(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "from ib_async import IB\n",
    )

    assert _codes(root) == {"PROVIDER_SDK_IMPORT"}


def test_guardrail_report_contains_remediation(tmp_path: Path) -> None:
    root = tmp_path
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


def test_guardrails_reject_runtime_session_complexity_without_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path
    methods = "\n".join(f"    def public_{index}(self):\n        pass" for index in range(13))
    _write(
        root,
        "backend/src/qts/runtime/session.py",
        f"class RuntimeSession:\n{methods}\n\n    def _helper_0(self):\n        pass\n",
    )

    assert _codes(root) == {"RUNTIME_SESSION_COMPLEXITY"}


def test_guardrails_reject_runtime_coordinator_without_decision_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/recovery.py",
        "class RuntimeRecoveryCoordinator:\n    def recover(self):\n        pass\n",
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
        "docs/architecture/backtest_live_parallel_sequence.html",
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
    rule_names = {rule.__class__.__name__ for rule in guardrails.GuardrailSuite().rules}

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
    } <= rule_names


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


def test_make_check_keeps_guardrails_before_tests() -> None:
    makefile = Path("Makefile").read_text(encoding="utf-8")

    assert (
        "check: format lint guardrails typecheck test-unit test-integration test-anchor" in makefile
    )
