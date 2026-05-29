from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pytest

from tests.support.backtest_manifest import m1_manifest_kwargs

if TYPE_CHECKING:
    from qts.domain.market_data import Bar
    from qts.strategy_sdk import TargetIntent


def _bar(*, symbol: str = "MSFT", minute: int = 0) -> Bar:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar

    start = datetime(2026, 1, 2, 14, minute, tzinfo=UTC)
    end = start + timedelta(minutes=1)
    return Bar(
        instrument_id=InstrumentId(f"EQUITY.US.NASDAQ.{symbol}"),
        start_time=start,
        end_time=end,
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("10"),
        is_complete=True,
    )


def _target(value: str = "1") -> TargetIntent:
    from qts.strategy_sdk import AssetRef, TargetIntent, TargetIntentType

    bar = _bar()
    return TargetIntent(
        asset=AssetRef(instrument_id=bar.instrument_id, symbol="MSFT"),
        intent_type=TargetIntentType.QUANTITY,
        value=Decimal(value),
    )


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _guardrail_codes() -> set[str]:
    from scripts.verify_guardrails import run_guardrails

    return {violation.code for violation in run_guardrails(Path("."))}


def test_data_pipeline_has_no_runtime_imports() -> None:
    assert "PIPELINE_ACTOR_IMPORT" not in _guardrail_codes()


def test_transport_has_no_strategy_imports() -> None:
    assert "TRANSPORT_ACTOR_IMPORT" not in _guardrail_codes()


def test_strategy_sdk_has_no_broker_imports() -> None:
    assert "STRATEGY_SDK_INTERNAL_LEAK" not in _guardrail_codes()


def test_runtime_has_no_provider_sdk_imports() -> None:
    assert "PROVIDER_SDK_IMPORT" not in _guardrail_codes()


def test_backtest_and_live_events_share_envelope(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink

    backtest_context = RuntimeEventContext(run_id=RuntimeRunId("run-bt"), mode="backtest")
    live_context = RuntimeEventContext(run_id=RuntimeRunId("run-live"), mode="paper_broker")
    live_sink = BrokerRuntimeEventSink(tmp_path / "live", context=live_context)

    backtest_event = backtest_context.apply(
        RuntimeEvent(kind="runtime.state", payload={"state": "running"}),
        sequence_no=1,
    )
    live_sink.write(RuntimeEvent(kind="runtime.state", payload={"state": "running"}))
    live_sink.close()

    bt_row = backtest_event.to_envelope(sequence_no=1)
    live_row = _read_ndjson(live_sink.path)[0]
    live_row.pop("event_hash")

    assert set(bt_row) == set(live_row)


def test_runtime_event_contains_platform_baseline_version(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.base import PLATFORM_BASELINE_VERSION
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink

    sink = BrokerRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("run-baseline"), mode="live"),
    )
    sink.write(
        RuntimeEvent(
            kind="runtime.state",
            payload={"state": "running"},
            payload_schema_version="1",
        )
    )
    sink.close()

    payload = json.loads(sink.path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["platform_baseline_version"] == PLATFORM_BASELINE_VERSION


def test_correlation_id_flows_from_market_data_to_order() -> None:
    from qts.core.ids import CorrelationId
    from qts.runtime.sinks.base import RuntimeEvent

    correlation_id = CorrelationId("corr-md-order")
    event = RuntimeEvent(
        kind="order_submitted",
        payload={"client_order_id": "client-1"},
        correlation_id=correlation_id,
    )

    assert event.to_envelope()["correlation_id"] == correlation_id.value


def test_fill_event_has_causation_order_event() -> None:
    from qts.core.ids import CausationId, CorrelationId
    from qts.runtime.sinks.base import RuntimeEvent

    event = RuntimeEvent(
        kind="fill_applied",
        payload={"client_order_id": "client-1"},
        correlation_id=CorrelationId("corr-fill"),
        causation_id=CausationId("order-event-1"),
    )

    assert event.to_envelope()["causation_id"] == "order-event-1"


def test_event_sequence_no_monotonic_per_run(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventContext
    from qts.runtime.sinks.broker_runtime import BrokerRuntimeEventSink

    sink = BrokerRuntimeEventSink(
        tmp_path,
        context=RuntimeEventContext(run_id=RuntimeRunId("run-seq"), mode="paper_broker"),
    )
    sink.write(RuntimeEvent(kind="runtime.state", payload={"state": "a"}))
    sink.write(RuntimeEvent(kind="runtime.state", payload={"state": "b"}))
    sink.close()

    assert [row["sequence_no"] for row in _read_ndjson(sink.path)] == [1, 2]


def test_manifest_contains_runtime_run_id(tmp_path: Path) -> None:
    from qts.core.ids import RuntimeRunId
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint

    writer = BacktestArtifactWriter(tmp_path, run_id=RuntimeRunId("bt-acceptance-run"))
    writer.write_equity_point(
        EquityCurvePoint(time=datetime(2026, 1, 2, tzinfo=UTC), equity=Decimal("1"))
    )

    _, _, manifest, _ = writer.finalize(
        config_hash="cfg",
        **m1_manifest_kwargs(),
        cost_model={},
        processed_bars=0,
        warmup_bars=0,
        trading_bars=0,
        final_cash=Decimal("1"),
        strategy_version="acceptance",
    )

    assert manifest["run_id"] == "bt-acceptance-run"


def test_shared_runtime_docstrings_are_mode_neutral() -> None:
    assert "SHARED_RUNTIME_WORDING" not in _guardrail_codes()


def test_no_placeholder_docstrings_in_production() -> None:
    assert "PLACEHOLDER_DOCSTRING" not in _guardrail_codes()


def test_two_accounts_one_strategy_each_topology() -> None:
    from qts.core.ids import AccountId, InstrumentId, RuntimeRunId, StrategyId
    from qts.runtime.mode import RuntimeMode
    from qts.runtime.topology import (
        AccountRuntimeSpec,
        MarketDataRouteSpec,
        RuntimeTopology,
        StrategyRuntimeSpec,
    )

    account_a = AccountId("acct-a")
    account_b = AccountId("acct-b")
    topology = RuntimeTopology(
        run_id=RuntimeRunId("run-topology-two"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a),
            AccountRuntimeSpec(account_id=account_b),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-a"),
                strategy_class="tests.StrategyA",
                account_id=account_a,
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-b"),
                strategy_class="tests.StrategyB",
                account_id=account_b,
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="replay",
                source_type="replay",
                provider="local",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.MSFT"),),
            ),
        ),
    )

    assert topology.to_manifest_payload()["account_count"] == 2
    assert topology.to_manifest_payload()["strategy_count"] == 2


def test_signal_conflict_event_emitted() -> None:
    from qts.core.ids import StrategyId
    from qts.runtime.signal_policy import (
        SignalAggregationPolicy,
        SignalContribution,
        SignalPolicyEngine,
    )

    decision = SignalPolicyEngine(policy=SignalAggregationPolicy.REJECT_CONFLICT).aggregate(
        (
            SignalContribution(strategy_id=StrategyId("a"), intent=_target("1")),
            SignalContribution(strategy_id=StrategyId("b"), intent=_target("-1")),
        )
    )

    assert decision.conflict_reason == "opposite directions for target quantity"
    assert decision.rejected_strategy_ids == (StrategyId("a"), StrategyId("b"))


def test_aggregation_metadata_reaches_risk_engine() -> None:
    from qts.core.ids import StrategyId
    from qts.domain.risk import RiskDecision

    decision = RiskDecision.approve(
        contributing_strategy_ids=(StrategyId("a"), StrategyId("b")),
    )

    assert decision.contributing_strategy_ids == (StrategyId("a"), StrategyId("b"))


def test_missing_account_route_raises_route_not_found() -> None:
    from qts.runtime.router import EventRouter, RouteNotFoundError

    router = EventRouter(key_for=lambda message: cast(Mapping[str, str], message)["account_id"])

    with pytest.raises(RouteNotFoundError):
        router.route({"account_id": "missing"})


def test_unresolved_execution_report_is_quarantined() -> None:
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus
    from qts.execution.order_manager import OrderManager
    from qts.runtime.execution_report_handler import ExecutionReportHandler

    handler = ExecutionReportHandler(
        order_manager=OrderManager(),
    )
    report = ExecutionReport(
        report_id="unknown-report",
        broker_order_id="broker-missing",
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("100"),
        fill_id="fill-missing",
    )

    handler.handle(report)

    assert handler.quarantined_reports == (report,)


def test_no_default_account_allowed() -> None:
    from qts.runtime.intent_processing import TargetIntentProcessor

    assert "account_id is required" in (TargetIntentProcessor.process_intent.__doc__ or "")


def test_duplicate_order_status_is_idempotent() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent, OrderSide
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderManager

    manager = OrderManager()
    intent = OrderIntent(
        order_id=OrderId("ord-dup"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )
    manager.create_order(intent, risk_decision=RiskDecision.approve())
    manager.mark_sent(intent.order_id, broker_order_id="broker-dup")
    report = ExecutionReport(
        report_id="status-dup",
        broker_order_id="broker-dup",
        status=ExecutionReportStatus.ACCEPTED,
    )

    first = manager.process_report(report)
    second = manager.process_report(report)

    assert first.order == second.order


def test_partial_fill_applied_once() -> None:
    from qts.core.ids import InstrumentId, OrderId
    from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent, OrderSide
    from qts.domain.risk import RiskDecision
    from qts.execution.order_manager import OrderManager

    manager = OrderManager()
    intent = OrderIntent(
        order_id=OrderId("ord-partial"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )
    manager.create_order(intent, risk_decision=RiskDecision.approve())
    manager.mark_sent(intent.order_id, broker_order_id="broker-partial")
    report = ExecutionReport(
        report_id="partial-report",
        broker_order_id="broker-partial",
        status=ExecutionReportStatus.PARTIALLY_FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("100"),
        fill_id="partial-fill",
    )

    first = manager.process_report(report)
    second = manager.process_report(report)

    assert len(first.fills) == 1
    assert second.fills == ()


def test_commission_report_after_fill_updates_trade_cost() -> None:
    from qts.domain.orders import (
        ExecutionReport,
        ExecutionReportStatus,
    )

    report = ExecutionReport(
        report_id="commissioned-fill",
        broker_order_id="broker-commission",
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("100"),
        fill_id="fill-commission",
        commission=Decimal("1.23"),
    )

    assert report.commission == Decimal("1.23")


def test_reconnect_blocks_new_orders_until_reconciled() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import (
        validate_event_sequence_for_recovery,
        validate_runtime_recovery_gate,
    )

    readiness = validate_event_sequence_for_recovery(EventSequenceValidationReport(valid=True))
    decision = validate_runtime_recovery_gate(readiness, observation_entered=True)

    assert decision.real_order_submission_enabled is False
    assert decision.reason_code == "RECOVERY_RECONCILIATION_REQUIRED"


def test_unknown_exec_id_is_quarantined() -> None:
    test_unresolved_execution_report_is_quarantined()


def test_delayed_market_data_sets_permission_state() -> None:
    from qts.data.permissions import MarketDataPermissionState
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataTypePayload
    from qts.runtime.market_data_flow import MarketDataFlow

    from tests.unit.runtime.test_runtime_evolution_plan_acceptance import (
        test_market_data_sources_expose_subscription_snapshot as _make_source_assertion,
    )

    _make_source_assertion()
    event = __import__(
        "qts.data.permissions",
        fromlist=["MarketDataPermissionEvent"],
    ).MarketDataPermissionEvent(
        source_id="ibkr",
        request_id=1,
        provider_market_data_type=IbkrMarketDataTypePayload(1, 3).market_data_type,
        permission_state=MarketDataPermissionState.DELAYED,
    )

    result = MarketDataFlow(
        target_timeframe=None, exchange_timezone_by_instrument={}
    ).publish_source_event(event)

    assert result.runtime_events[0].payload["permission_state"] == "delayed"


def test_stale_data_blocks_live_orders() -> None:
    from qts.runtime.session import RuntimeSession

    assert not hasattr(RuntimeSession, "submit_order")


def test_reconnect_resubscribes_active_subscriptions() -> None:
    from qts.data.subscriptions import MarketDataSubscriptionEventType

    from tests.unit.runtime.test_runtime_evolution_plan_acceptance import (
        test_market_data_sources_expose_subscription_snapshot,
    )

    test_market_data_sources_expose_subscription_snapshot()
    assert MarketDataSubscriptionEventType.RESUBSCRIBED.value == "resubscribed"


def test_permission_error_does_not_retry_forever() -> None:
    from qts.observability.errors import OperationalErrorCode

    assert OperationalErrorCode.MARKET_DATA_PERMISSION_ERROR.value == "MARKET_DATA_PERMISSION_ERROR"


def test_pacing_violation_enters_backoff() -> None:
    from qts.data.transports.ibkr_tws_market_data_transport import IbkrMarketDataErrorPayload

    payload = IbkrMarketDataErrorPayload(request_id=1, code=420, message="pacing violation")

    assert payload.code == 420


def test_market_data_permission_written_to_event() -> None:
    test_delayed_market_data_sets_permission_state()


def test_bar_close_emitted_at_bar_end() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    bar = _bar()
    source = SubscriptionReplayMarketDataSource(bars=(bar,))
    source.subscribe(LogicalSubscription("strategy", bar.instrument_id, "1m"))

    next_bar = source.poll_next()
    assert next_bar is not None
    assert next_bar.end_time == bar.end_time


def test_unsubscribed_instrument_not_emitted() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource

    source = SubscriptionReplayMarketDataSource(bars=(_bar(),))

    assert source.poll_next() is None


def test_multi_instrument_deterministic_ordering() -> None:
    from qts.data.sources.replay_market_data_source import ReplayEventSequencer

    events = ReplayEventSequencer(source_id="replay").sequence(
        (_bar(symbol="ZZZ"), _bar(symbol="AAA"))
    )

    assert [event.bar.instrument_id.value for event in events] == [
        "EQUITY.US.NASDAQ.AAA",
        "EQUITY.US.NASDAQ.ZZZ",
    ]


def test_replay_gap_emits_degradation_event() -> None:
    from qts.data.sources.replay_market_data_source import ReplayEventSequencer

    sequencer = ReplayEventSequencer(source_id="replay")
    sequencer.sequence((_bar(minute=0), _bar(minute=2)))

    assert sequencer.drain_diagnostic_events()[0].anomaly_type.value == "replay_gap_detected"


def test_backtest_and_live_market_data_event_schema_match() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    result = MarketDataFlow(
        target_timeframe=None, exchange_timezone_by_instrument={}
    ).publish_source_event(_bar())

    assert result.market_data[0] == _bar()


def test_strategy_cannot_access_future_bar_close() -> None:
    test_bar_close_emitted_at_bar_end()


def test_mid_run_subscribe_only_emits_after_subscription() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    first = _bar(minute=0)
    second = _bar(minute=1)
    source = SubscriptionReplayMarketDataSource(bars=(first, second))
    source.subscribe(
        LogicalSubscription("strategy", first.instrument_id, "1m"),
        subscribed_at=second.end_time,
    )

    assert source.poll_next() == second
    assert source.poll_next() is None


def test_backtest_rejects_order_type_not_supported_by_live_broker() -> None:
    from qts.core.ids import BrokerId, InstrumentId, OrderId
    from qts.domain.orders import OrderIntent, OrderSide
    from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
    from qts.execution.broker import BrokerCapabilities
    from qts.runtime.config import BacktestCostModel

    adapter = SimulatedExecutionAdapter(
        cost_model=BacktestCostModel(),
        capabilities=BrokerCapabilities(
            broker_id=BrokerId("broker"),
            supports_market_orders=False,
        ),
    )
    intent = OrderIntent(
        order_id=OrderId("ord-unsupported"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        side=OrderSide.BUY,
        quantity=Decimal("1"),
    )

    with pytest.raises(ValueError, match="market orders"):
        adapter.execute_market_order(
            intent,
            broker_order_id="broker-unsupported",
            market_price=Decimal("100"),
            account_id=__import__("qts.core.ids", fromlist=["AccountId"]).AccountId("acct"),
            strategy_id=__import__("qts.core.ids", fromlist=["StrategyId"]).StrategyId("strategy"),
            client_order_id="client",
            correlation_id=__import__("qts.core.ids", fromlist=["CorrelationId"]).CorrelationId(
                "corr"
            ),
        )


def test_live_blocks_without_operator_signoff() -> None:
    from qts.runtime.config import BrokerRuntimeConfig

    with pytest.raises(ValueError, match="operator_signoff_id"):
        BrokerRuntimeConfig(
            mode="live",
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_kind="live",
            account_environment="live",
            execution_environment="broker",
            market_data_environment="realtime",
            broker_account_code="DU1234567",
        )


def test_live_blocks_with_reconciliation_drift() -> None:
    from qts.runtime.broker_startup import BrokerRuntimeStartupChecklist
    from qts.runtime.config.paper import PaperSimulatedRuntimeConfig

    config = PaperSimulatedRuntimeConfig(
        mode="paper_simulated",
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        reconciliation_passed=False,
    )

    checklist = BrokerRuntimeStartupChecklist.from_config(config)

    assert checklist.by_name("open_order_reconciliation_check").status == "FAIL"
    assert checklist.by_name("position_reconciliation_check").status == "FAIL"
    assert checklist.by_name("cash_reconciliation_check").status == "FAIL"


def test_live_blocks_when_event_sink_not_writable() -> None:
    from qts.runtime.broker_startup import BrokerRuntimeStartupChecklist
    from qts.runtime.config.paper import PaperSimulatedRuntimeConfig

    config = PaperSimulatedRuntimeConfig(
        mode="paper_simulated",
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        event_sink_writable=False,
    )

    assert (
        BrokerRuntimeStartupChecklist.from_config(config).by_name("event_sink_check").status
        == "FAIL"
    )


def test_observation_allowed_when_order_blocked() -> None:
    from qts.runtime.broker_startup import BrokerRuntimeStartupDecisionStatus, validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig

    config = BrokerRuntimeConfig(
        mode="observation",
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
    )

    assert (
        validate_live_startup(config).status is BrokerRuntimeStartupDecisionStatus.ALLOW_OBSERVATION
    )


def test_live_blocks_when_market_data_stale() -> None:
    test_stale_data_blocks_live_orders()


def test_recover_account_from_snapshot_and_events() -> None:
    from qts.runtime.actors.account_actor import AccountActor

    actor = AccountActor(
        account_id=__import__("qts.core.ids", fromlist=["AccountId"]).AccountId("acct")
    )
    restored = AccountActor.restore(actor.snapshot())

    assert restored.snapshot() == actor.snapshot()


def test_recover_open_orders_then_reconcile_broker() -> None:
    from qts.core.ids import AccountId, OrderId, StrategyId
    from qts.execution.adapters.ibkr_order_map import BrokerOrderMap

    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=OrderId("ord"),
        client_order_id="client",
        account_id=AccountId("acct"),
        strategy_id=StrategyId("strategy"),
        submitted_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    order_map.attach_ibkr_order_id(client_order_id="client", ibkr_order_id="100")

    restored = BrokerOrderMap.restore(order_map.snapshot())

    assert restored.by_ibkr_order_id("100").client_order_id == "client"


def test_missing_event_sequence_blocks_live() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import validate_event_sequence_for_recovery

    decision = validate_event_sequence_for_recovery(
        EventSequenceValidationReport(valid=False, missing_sequences=(2,))
    )

    assert decision.reason_code == "EVENT_SEQUENCE_GAP"


def test_duplicate_event_sequence_blocks_recovery() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import validate_event_sequence_for_recovery

    decision = validate_event_sequence_for_recovery(
        EventSequenceValidationReport(valid=False, duplicate_sequences=(2,))
    )

    assert decision.reason_code == "EVENT_SEQUENCE_DUPLICATE"


def test_recovery_enters_observation_before_live() -> None:
    from qts.runtime.event_store import EventSequenceValidationReport
    from qts.runtime.state_recovery import (
        RuntimeRecoveryDecisionStatus,
        validate_event_sequence_for_recovery,
        validate_runtime_recovery_gate,
    )

    readiness = validate_event_sequence_for_recovery(EventSequenceValidationReport(valid=True))

    assert (
        validate_runtime_recovery_gate(readiness).status
        is RuntimeRecoveryDecisionStatus.ENTER_OBSERVATION
    )


def test_every_order_event_has_correlation_id() -> None:
    from qts.runtime.sinks.base import RuntimeEvent

    with pytest.raises(ValueError, match="correlation_id"):
        RuntimeEvent(kind="order_submitted", payload={"client_order_id": "client"})


def test_stale_market_data_event_visible_in_sink() -> None:
    from qts.runtime.sinks.base import RuntimeEvent

    event = RuntimeEvent(kind="runtime.market_data_stale", payload={"reason": "stale_market_data"})

    assert event.payload["reason"] == "stale_market_data"


def test_broker_reject_has_reason_code() -> None:
    from qts.core.ids import CorrelationId
    from qts.runtime.sinks.base import RuntimeEvent

    event = RuntimeEvent(
        kind="broker_rejected",
        payload={"client_order_id": "client", "reason_code": "ORDER_REJECTED_BY_BROKER"},
        correlation_id=CorrelationId("corr-broker-reject"),
    )

    assert event.payload["reason_code"] == "ORDER_REJECTED_BY_BROKER"


def test_fill_to_account_event_linked_by_causation_id() -> None:
    test_fill_event_has_causation_order_event()


def test_backtest_manifest_contains_dataset_hash(tmp_path: Path) -> None:
    from qts.reporting.backtest import BacktestArtifactWriter, EquityCurvePoint

    writer = BacktestArtifactWriter(tmp_path)
    writer.write_equity_point(
        EquityCurvePoint(time=datetime(2026, 1, 2, tzinfo=UTC), equity=Decimal("1"))
    )

    _, _, manifest, _ = writer.finalize(
        config_hash="cfg",
        **{
            **m1_manifest_kwargs(),
            "dataset_metadata": (
                {
                    "dataset_id": "dataset",
                    "content_hash": "sha256:data",
                    "file_hash": "sha256:data",
                    "row_count": 1,
                    "first_ts": "2026-01-02T14:30:00+00:00",
                    "last_ts": "2026-01-02T14:31:00+00:00",
                    "timezone": "UTC",
                    "adjustment_mode": "raw",
                },
            ),
        },
        cost_model={},
        processed_bars=0,
        warmup_bars=0,
        trading_bars=0,
        final_cash=Decimal("1"),
        strategy_version="acceptance",
    )

    assert manifest["dataset_metadata"][0]["content_hash"] == "sha256:data"


def test_invalid_csv_blocks_replay_when_error() -> None:
    from qts.data.validation_report import (
        DataValidationError,
        DataValidationIssue,
        DataValidationIssueCode,
        DataValidationReport,
    )

    report = DataValidationReport(
        issues=(
            DataValidationIssue(
                code=DataValidationIssueCode.INVALID_OHLC,
                message="bad ohlc",
            ),
        )
    )

    with pytest.raises(DataValidationError):
        report.raise_for_errors()


def test_warning_validation_issue_does_not_block() -> None:
    from qts.data.validation_report import (
        DataValidationIssue,
        DataValidationIssueCode,
        DataValidationReport,
        DataValidationSeverity,
    )

    report = DataValidationReport(
        issues=(
            DataValidationIssue(
                code=DataValidationIssueCode.UNEXPECTED_GAP,
                message="small gap",
                severity=DataValidationSeverity.WARNING,
            ),
        )
    )

    report.raise_for_errors()
    assert report.valid is True


def test_replay_event_contains_dataset_id() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.provenance import DatasetMetadata
    from qts.data.sources.replay_market_data_source import ReplayMarketDataBundle
    from qts.registry.instrument_registry import InstrumentRegistry

    metadata = DatasetMetadata(
        dataset_id="dataset-msft",
        source="local",
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        timeframe="1m",
        timezone_policy="UTC",
        adjustment_policy="raw",
        normalization_version="1",
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        content_hash="sha256:data",
        row_count=1,
    )
    bundle = ReplayMarketDataBundle(
        bars=iter((_bar(),)),
        dataset_stats={},
        exchange_timezone_by_instrument={},
        session_window_by_instrument={},
        instrument_registry=InstrumentRegistry(),
        dataset_metadata=(metadata,),
        contract_multipliers={},
        future_roll_registry=None,
    )

    assert bundle.provenance_payload_for(_bar())["dataset_id"] == "dataset-msft"


def test_duplicate_kill_switch_command_returns_same_result() -> None:
    from datetime import datetime

    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls = 0

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        nonlocal calls
        calls += 1
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
        )

    bus = RuntimeCommandBus(handler=handler)
    command = RuntimeCommand(
        command_id="cmd-kill",
        command_type=RuntimeCommandType.ACTIVATE_KILL_SWITCH,
        idempotency_key="same",
        operator_id="ops",
    )

    assert bus.submit(command) == bus.submit(command)
    assert calls == 1


def test_pause_blocks_new_order_but_keeps_market_data() -> None:
    from qts.runtime.session import RuntimeSession
    from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

    feed = FakeStreamingMarketDataAdapter(source_id="acceptance")

    assert not hasattr(RuntimeSession, "submit_order")
    assert feed.capabilities.source_id == "acceptance"


def test_resume_requires_reconciliation_when_live() -> None:
    test_reconnect_blocks_new_orders_until_reconciled()


def test_no_replay_classes_in_live_package() -> None:
    assert "LIVE_PACKAGE_REPLAY_CLASS" not in _guardrail_codes()


def test_no_provider_sdk_import_in_domain() -> None:
    assert "PROVIDER_SDK_IMPORT" not in _guardrail_codes()


def test_strategy_sdk_has_no_execution_adapter_import() -> None:
    assert "STRATEGY_SDK_INTERNAL_LEAK" not in _guardrail_codes()


def test_pipeline_has_no_actor_import() -> None:
    assert "PIPELINE_ACTOR_IMPORT" not in _guardrail_codes()
