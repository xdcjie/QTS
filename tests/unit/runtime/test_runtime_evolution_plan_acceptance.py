from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from tests.support.backtest_manifest import m1_manifest_kwargs

if TYPE_CHECKING:
    from qts.execution.broker import BrokerOrderRequest


def _runtime_order_request() -> BrokerOrderRequest:
    from qts.core.ids import AccountId, InstrumentId, OrderId, StrategyId
    from qts.domain.orders import OrderSide
    from qts.execution.broker import BrokerOrderRequest

    return BrokerOrderRequest(
        order_id=OrderId("ord-acceptance-1"),
        client_order_id="client-acceptance-1",
        account_id=AccountId("acct-acceptance"),
        strategy_id=StrategyId("strategy-acceptance"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )


def _backtest_config_kwargs(tmp_path: Path) -> dict[str, Any]:
    from qts.runtime.config import BacktestMarketDataReference

    return {
        "roots": ("MSFT",),
        "symbols": ("MSFT",),
        "start": datetime(2026, 1, 2, tzinfo=UTC),
        "end": datetime(2026, 1, 3, tzinfo=UTC),
        "timeframe": "1m",
        "initial_cash": Decimal("100000"),
        "strategy_class": "tests.AcceptanceStrategy",
        "market_data": BacktestMarketDataReference(
            config_path=tmp_path / "historical.yaml",
            catalog="acceptance",
        ),
    }


def test_observation_mode_blocks_submit_order() -> None:
    from qts.core.ids import BrokerId
    from qts.runtime.live import LiveRuntime
    from qts.testing.fakes.broker import FakeBrokerAdapter
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

    runtime = LiveRuntime(
        broker=FakeBrokerAdapter(broker_id=BrokerId("fake")),
        feed=FakeStreamingMarketDataAdapter(source_id="acceptance"),
    )

    result = runtime.submit_order(_runtime_order_request())

    assert result.accepted is False
    assert result.reason_code == "RUNTIME_NOT_RUNNING"


def test_paper_simulated_never_constructs_ibkr_order_transport() -> None:
    from qts.runtime.config import LiveRuntimeConfig
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode

    config = LiveRuntimeConfig(
        mode=RuntimeMode.PAPER_SIMULATED,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert config.execution_environment is ExecutionEnvironment.SIMULATED


def test_mode_written_to_report_manifest(tmp_path: Path) -> None:
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_simulated"},
        runtime_mode="paper_simulated",
        account_id="acct-paper",
        runtime_instance_id="runtime-evolution-paper-simulated",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-runtime-evolution",
        connection_metadata={"host": "127.0.0.1", "port": 4002},
        event_sink=sink,
    )

    assert manifest.payload["runtime_mode"] == "paper_simulated"


def test_config_version_required(tmp_path: Path) -> None:
    from qts.runtime.config import BacktestRuntimeConfig

    with pytest.raises(ValueError, match="schema_version"):
        BacktestRuntimeConfig(
            **_backtest_config_kwargs(tmp_path),
            schema_version=" ",
        )


def test_config_hash_stable(tmp_path: Path) -> None:
    from qts.runtime.config import BacktestRuntimeConfig

    config = BacktestRuntimeConfig(**_backtest_config_kwargs(tmp_path))
    same = BacktestRuntimeConfig(**_backtest_config_kwargs(tmp_path))
    changed = replace(config, schema_version="2")

    assert config.config_hash == same.config_hash
    assert config.config_hash != changed.config_hash


def test_runtime_config_package_exposes_mode_specific_modules() -> None:
    from qts.runtime.config.backtest import BacktestRuntimeConfig
    from qts.runtime.config.base import ConfigMigration, TradingRuntimeConfig
    from qts.runtime.config.live import LiveRuntimeConfig
    from qts.runtime.config.paper import (
        PaperBrokerRuntimeConfig,
        PaperSimulatedRuntimeConfig,
    )

    assert BacktestRuntimeConfig.__name__ == "BacktestRuntimeConfig"
    assert LiveRuntimeConfig.__name__ == "LiveRuntimeConfig"
    assert PaperBrokerRuntimeConfig.__name__ == "PaperBrokerRuntimeConfig"
    assert PaperSimulatedRuntimeConfig.__name__ == "PaperSimulatedRuntimeConfig"
    assert ConfigMigration.__name__ == "ConfigMigration"
    assert TradingRuntimeConfig(mode="paper_broker").mode == "paper_broker"


def test_paper_runtime_sample_configs_are_disjoint() -> None:
    import yaml  # type: ignore[import-untyped]

    broker = yaml.safe_load(Path("configs/paper_broker.yaml").read_text(encoding="utf-8"))
    simulated = yaml.safe_load(Path("configs/paper_simulated.yaml").read_text(encoding="utf-8"))

    assert broker["mode"] == "paper_broker"
    assert broker["execution_environment"] == "broker"
    assert broker["account_environment"] == "paper"
    assert broker["broker_account_kind"] == "paper"
    assert str(broker["broker_account_code"]).startswith("DU")
    assert broker["broker_port"] == 4002
    assert simulated["mode"] == "paper_simulated"
    assert simulated["execution_environment"] == "simulated"
    assert simulated["account_environment"] == "simulated"
    assert simulated["broker_account_kind"] == "simulated"
    assert "broker_account_code" not in simulated
    assert "broker_port" not in simulated


def test_runtime_session_canonical_names_are_mode_neutral() -> None:
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.safety import RuntimeKillSwitchEvidence
    from qts.runtime.session import RuntimeSession, RuntimeSessionResult
    from qts.runtime.state import RuntimeSessionState, RuntimeStateMachine

    assert RuntimeSession.__name__ == "RuntimeSession"
    assert RuntimeSession.__module__ == "qts.runtime.session"
    assert RuntimeSessionResult.__module__ == "qts.runtime.session"
    assert RuntimeSessionDependencies.__module__ == "qts.runtime.dependencies"
    assert RuntimeSessionState.__module__ == "qts.runtime.state"
    assert RuntimeStateMachine.__module__ == "qts.runtime.state"
    assert RuntimeKillSwitchEvidence.__module__ == "qts.runtime.safety"

    assert RuntimeStateMachine().apply("start") is RuntimeSessionState.STARTING


def test_transport_canonical_modules_are_under_transports() -> None:
    from qts.data.transports.ib_async_market_data_transport import IbAsyncMarketDataTransport
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrTwsMarketDataTransport
    from qts.execution.transports.ib_async_order_execution_transport import (
        IbAsyncOrderExecutionTransport,
    )
    from qts.execution.transports.ibkr_tws_order_execution_transport import (
        IbkrTwsOrderExecutionTransport,
    )

    assert IbkrTwsMarketDataTransport.__module__ == (
        "qts.data.transports.ibkr_tws_market_data_transport"
    )
    assert IbAsyncMarketDataTransport.__module__ == (
        "qts.data.transports.ib_async_market_data_transport"
    )
    assert IbkrTwsOrderExecutionTransport.__module__ == (
        "qts.execution.transports.ibkr_tws_order_execution_transport"
    )
    assert IbAsyncOrderExecutionTransport.__module__ == (
        "qts.execution.transports.ib_async_order_execution_transport"
    )


def test_transport_adapter_paths_are_removed() -> None:
    import importlib.util

    assert importlib.util.find_spec("qts.data.adapters.ibkr_async_transport") is None
    assert importlib.util.find_spec("qts.data.adapters.ibkr_transport") is None
    assert importlib.util.find_spec("qts.execution.adapters.ibkr_async_transport") is None
    assert importlib.util.find_spec("qts.execution.adapters.ibkr_transport") is None


def test_live_config_rejects_backtest_only_fields() -> None:
    from qts.runtime.config import LiveRuntimeConfig

    kwargs: dict[str, Any] = {
        "mode": "paper_simulated",
        "broker_configured": True,
        "account_configured": True,
        "risk_configured": True,
        "calendar_configured": True,
        "kill_switch_configured": True,
        "dataset_path": "backtest-only.csv",
    }
    with pytest.raises(TypeError):
        cast(Any, LiveRuntimeConfig)(**kwargs)


def test_backtest_config_rejects_live_broker_credentials(tmp_path: Path) -> None:
    from qts.runtime.config import BacktestRuntimeConfig

    kwargs = {
        **_backtest_config_kwargs(tmp_path),
        "broker_account_code": "DU1234567",
    }
    with pytest.raises(TypeError):
        cast(Any, BacktestRuntimeConfig)(**kwargs)


def test_brokerage_model_written_to_manifest(tmp_path: Path) -> None:
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint

    writer = BacktestArtifactWriter(tmp_path)
    writer.write_equity_point(
        EquityCurvePoint(
            time=datetime(2026, 1, 2, tzinfo=UTC),
            equity=Decimal("100000"),
        )
    )

    _, _, manifest, _ = writer.finalize(
        config_hash="cfg",
        **m1_manifest_kwargs(),
        cost_model={},
        processed_bars=0,
        warmup_bars=0,
        trading_bars=0,
        final_cash=Decimal("100000"),
        strategy_version="acceptance",
        brokerage_model="IBKR_FUTURES",
    )

    assert manifest["brokerage_model"] == "IBKR_FUTURES"


def test_checklist_written_to_manifest(tmp_path: Path) -> None:
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.config import LiveRuntimeConfig
    from qts.runtime.live import BrokerRuntimeStartupChecklist
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    config = LiveRuntimeConfig(
        mode="paper_simulated",
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )
    checklist = BrokerRuntimeStartupChecklist.from_config(config)
    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload=config.to_payload(),
        runtime_mode="paper_simulated",
        account_id="acct-paper",
        runtime_instance_id="runtime-evolution-checklist",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-runtime-evolution",
        connection_metadata={},
        event_sink=sink,
        startup_checklist=checklist,
    )

    assert manifest.payload["startup_checklist"]["checklist_hash"].startswith("sha256:")
    assert "startup_checklist" in manifest.payload["artifacts"]


def test_live_market_data_permission_written_to_manifest(tmp_path: Path) -> None:
    from qts.reporting.broker_runtime import BrokerRuntimeReportWriter
    from qts.runtime.sinks.live import LiveRuntimeEventSink

    sink = LiveRuntimeEventSink(tmp_path)
    sink.close()

    manifest = BrokerRuntimeReportWriter(tmp_path).write_manifest(
        config_payload={"mode": "paper_broker"},
        runtime_mode="paper_broker",
        account_id="DU1234567",
        runtime_instance_id="runtime-evolution-market-data-permission",
        source_commit="abcdef123456",
        operator_identity_hash="sha256:operator-runtime-evolution",
        connection_metadata={},
        event_sink=sink,
        market_data_permission_state="delayed",
    )

    assert manifest.payload["market_data_permission_state"] == "delayed"


def test_snapshot_command_writes_snapshot() -> None:
    from datetime import datetime

    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    command = RuntimeCommand(
        command_id="cmd-snapshot-1",
        command_type=RuntimeCommandType.SNAPSHOT,
        idempotency_key="snap-1",
        operator_id="ops",
    )
    result = RuntimeCommandResult(
        command_id=command.command_id,
        idempotency_key=command.idempotency_key,
        accepted_at=datetime(2026, 1, 2, tzinfo=UTC),
        completed_at=datetime(2026, 1, 2, 0, 0, 1, tzinfo=UTC),
        result_status=RuntimeCommandResultStatus.COMPLETED,
        evidence={"snapshot_id": "snapshot-1"},
    )

    event = result.completed_event(command)

    assert event.event_type == "command_completed"
    assert event.payload["snapshot_id"] == "snapshot-1"


def test_reconcile_command_emits_result_event() -> None:
    from datetime import datetime

    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    command = RuntimeCommand(
        command_id="cmd-reconcile-1",
        command_type=RuntimeCommandType.RECONCILE,
        idempotency_key="reconcile-1",
        operator_id="ops",
    )
    result = RuntimeCommandResult(
        command_id=command.command_id,
        idempotency_key=command.idempotency_key,
        accepted_at=datetime(2026, 1, 2, tzinfo=UTC),
        completed_at=datetime(2026, 1, 2, 0, 0, 1, tzinfo=UTC),
        result_status=RuntimeCommandResultStatus.COMPLETED,
        evidence={"drift": "none"},
    )

    event = result.completed_event(command)

    assert event.event_type == "command_completed"
    assert event.payload["command_type"] == "reconcile"
    assert event.payload["drift"] == "none"


def test_runtime_command_stream_event_types_are_public() -> None:
    from qts.api.websocket.dtos import StreamEventType

    assert StreamEventType.RUNTIME_STATE_CHANGED.value == "runtime_state_changed"
    assert StreamEventType.COMMAND_ACCEPTED.value == "command_accepted"
    assert StreamEventType.COMMAND_COMPLETED.value == "command_completed"


def test_recovery_snapshot_store_has_durable_boundary(tmp_path: Path) -> None:
    from qts.runtime.state_recovery import DurableSnapshotStore, StateSnapshot

    store = DurableSnapshotStore(tmp_path / "snapshots.jsonl")
    snapshot = StateSnapshot(actor_id="account:acct-1", state_version=1, payload={"cash": "10"})

    store.save(snapshot)

    assert store.load("account:acct-1") == snapshot


def test_recovery_snapshot_frequency_policy_triggers_on_event_count() -> None:
    from qts.runtime.state_recovery import SnapshotFrequencyPolicy

    policy = SnapshotFrequencyPolicy(every_event_count=5)

    assert policy.should_snapshot(event_count=4, elapsed=timedelta(seconds=1)) is False
    assert policy.should_snapshot(event_count=5, elapsed=timedelta(seconds=1)) is True


def test_market_data_sources_expose_subscription_snapshot() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
    from qts.data.subscriptions import LogicalSubscription
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    symbol_mapping = BrokerSymbolMapping(BrokerId("ibkr"))
    symbol_mapping.register(instrument_id, "MSFT")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="acceptance",
        ),
        symbol_mapping=symbol_mapping,
    )
    source = StreamingMarketDataSource(adapter=adapter)
    source.subscribe(LogicalSubscription("strategy-a", instrument_id, "1m"))

    snapshot = source.subscription_snapshot()

    assert snapshot[0]["instrument_id"] == instrument_id.value
    assert snapshot[0]["requested_timeframe"] == "1m"


def test_fill_models_include_next_bar_quote_volume_and_partial_variants() -> None:
    from qts.execution.simulator.fill_model import (
        ImmediateFillModel,
        NextBarOpenFillModel,
        PartialFillModel,
        QuoteAwareFillModel,
        VolumeParticipationFillModel,
    )

    assert NextBarOpenFillModel()
    assert QuoteAwareFillModel()
    assert VolumeParticipationFillModel(max_participation_rate=Decimal("0.1"))
    assert PartialFillModel(max_fill_quantity=Decimal("2"))
    assert (
        ImmediateFillModel().to_manifest_payload()["fill_model_name"]
        != NextBarOpenFillModel().to_manifest_payload()["fill_model_name"]
    )
    assert (
        VolumeParticipationFillModel(max_participation_rate=Decimal("0.1")).to_manifest_payload()[
            "volume_participation_limit"
        ]
        == "0.1"
    )
    assert (
        PartialFillModel(max_fill_quantity=Decimal("2")).to_manifest_payload()[
            "partial_fill_policy"
        ]
        == "max_fill_quantity"
    )


def test_min_tick_rounding() -> None:
    from qts.core.ids import BrokerId
    from qts.execution.broker import BrokerCapabilities

    capabilities = BrokerCapabilities(
        broker_id=BrokerId("broker"),
        min_tick=Decimal("0.05"),
    )

    assert capabilities.round_price(Decimal("10.03")) == Decimal("10.05")


def test_lot_size_rounding() -> None:
    from qts.core.ids import BrokerId
    from qts.execution.broker import BrokerCapabilities

    capabilities = BrokerCapabilities(
        broker_id=BrokerId("broker"),
        lot_size=Decimal("5"),
    )

    assert capabilities.round_quantity(Decimal("12")) == Decimal("10")


def test_limit_order_fill_model_differs_from_market_order() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.orders import OrderIntent, OrderSide
    from qts.execution.simulator.fill_model import ImmediateFillModel, NextBarOpenFillModel

    intent = OrderIntent(
        order_id=OrderId("ord-fill-model"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )

    market_report = ImmediateFillModel().fill(
        intent,
        broker_order_id="broker-1",
        market_price=Decimal("100"),
    )
    next_open_report = NextBarOpenFillModel().fill(
        intent,
        broker_order_id="broker-2",
        market_price=Decimal("100"),
        next_open_price=Decimal("101"),
    )

    assert market_report.fill_price == Decimal("100")
    assert next_open_report.fill_price == Decimal("101")


def test_fractional_quantity_rejected_when_not_supported() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.domain.orders import OrderIntent, OrderSide
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.execution.broker import BrokerCapabilities
    from qts.runtime.config import CostModelConfig

    adapter = SimulatedExecutionAdapter(
        cost_model=CostModelConfig(),
        capabilities=BrokerCapabilities(
            broker_id=BrokerId("broker"),
            supports_fractional=False,
        ),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-fractional"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        side=OrderSide.BUY,
        quantity=Decimal("1.5"),
    )
    request = _runtime_order_request()
    assert request.strategy_id is not None

    with pytest.raises(ValueError, match="fractional"):
        adapter.execute_market_order(
            intent,
            broker_order_id="broker-1",
            market_price=Decimal("100"),
            account_id=request.account_id,
            strategy_id=request.strategy_id,
            client_order_id="client-1",
            correlation_id=__import__("qts.core.ids", fromlist=["CorrelationId"]).CorrelationId(
                "corr-1"
            ),
        )
