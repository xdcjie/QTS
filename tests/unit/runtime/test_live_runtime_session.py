from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, RuntimeRunId, StrategyId
from qts.domain.market_data import Bar
from qts.execution.order_manager import ExecutionReport, ExecutionReportStatus, OrderIntent
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
from qts.runtime.topology import (
    AccountRuntimeSpec,
    MarketDataRouteSpec,
    RuntimeMode,
    RuntimeTopology,
    StrategyRuntimeSpec,
)
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent


def _bar(start: datetime) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


def _bar_for_instrument(start: datetime, instrument_id: InstrumentId) -> Bar:
    return Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("100"),
        is_complete=True,
    )


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.placed:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.placed = True


class _FixedTargetStrategy(Strategy):
    """Emit a fixed target quantity every bar."""

    def __init__(self, target: Decimal) -> None:
        self._target = target

    def initialize(self, ctx: Any) -> None:
        self._asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        ctx.target_quantity(self._asset, self._target)


class _SignedTargetStrategy(Strategy):
    """Emit a fixed target quantity every bar, including negatives."""

    def __init__(self, target: Decimal) -> None:
        self._target = target

    def initialize(self, ctx: Any) -> None:
        self._asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        ctx.target_quantity(self._asset, self._target)


class _InstrumentContext:
    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        return intent.asset.instrument_id

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        return bar.close

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        return False

    def related_contracts_for(
        self,
        continuous_instrument_id: InstrumentId,
    ) -> frozenset[InstrumentId]:
        raise RuntimeError("continuous contracts are not configured")


@dataclass(slots=True)
class _RecordingExecutionAdapter:
    seen: list[OrderIntent] = field(default_factory=list)

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = market_price, account_id, strategy_id, client_order_id, correlation_id
        self.seen.append(intent)
        return ExecutionReport(
            report_id=f"{broker_order_id}-accepted",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
        )

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


@dataclass(slots=True)
class _FilledExecutionAdapter:
    seen: list[OrderIntent] = field(default_factory=list)

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = account_id, strategy_id, client_order_id, correlation_id
        self.seen.append(intent)
        return ExecutionReport(
            report_id=f"{broker_order_id}-filled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.FILLED,
            filled_quantity=intent.quantity,
            fill_price=market_price,
            fill_id=f"{broker_order_id}-fill",
        )

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


@dataclass(slots=True)
class _RecordingSink(RuntimeEventSink):
    events: list[RuntimeEvent] = field(default_factory=list)

    def write(self, event: RuntimeEvent) -> None:
        self.events.append(event)


def _portfolio_view(
    snapshot: Any,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
) -> PortfolioView:
    positions = {
        instrument_id: PortfolioPosition(
            quantity=position.quantity,
            market_value=position.quantity * latest_prices.get(instrument_id, Decimal("0")),
        )
        for instrument_id, position in snapshot.positions.items()
    }
    cash = snapshot.cash["USD"]
    return PortfolioView(
        cash=cash,
        equity=cash + sum((position.market_value for position in positions.values()), Decimal("0")),
        positions=positions,
    )


def _registry() -> Any:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=instrument_id,
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.01"),
                lot_size=Decimal("1"),
                multiplier=Decimal("1"),
                settlement=SettlementType.CASH,
                calendar_id="NASDAQ",
            ),
        ),
    )
    return registry


def test_live_runtime_session_submits_only_through_actor_execution_path() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live import LiveRuntimeState
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("100000"))]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
            account_id=account_id,
        )
    )

    assert session.start() is LiveRuntimeState.RUNNING
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert len(adapter.seen) == 1
    assert result.orders[0].broker_order_id == "live-000001"
    assert result.account_snapshot is not None
    assert result.account_snapshot.positions == {}
    assert [event.kind for event in sink.events] == [
        "runtime.state_transition",
        "runtime.market_data",
        "runtime.signal_received",
        "runtime.strategy_intent",
        "runtime.signal_aggregated",
        "runtime.order_submitted",
        "runtime.broker_report",
        "runtime.account_snapshot",
    ]


def test_live_runtime_session_writes_contextual_runtime_event_envelope() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode

    account_id = AccountId("acct-live-1")
    strategy_id = StrategyId("strategy-live-1")
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            run_id=RuntimeRunId("run-live-1"),
            mode=RuntimeMode.PAPER_BROKER,
            execution_environment=ExecutionEnvironment.BROKER,
            account_id=account_id,
            strategy_id=strategy_id,
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("100000"))]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_RecordingExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    envelopes = [event.to_envelope() for event in sink.events]
    assert [row["sequence_no"] for row in envelopes] == list(range(1, len(envelopes) + 1))
    assert {row["run_id"] for row in envelopes} == {"run-live-1"}
    assert {row["mode"] for row in envelopes} == {"paper_broker"}
    assert {row["execution_environment"] for row in envelopes} == {"broker"}
    assert {row["account_id"] for row in envelopes} == {"acct-live-1"}
    assert {row["strategy_id"] for row in envelopes} == {"strategy-live-1"}
    order_event = next(row for row in envelopes if row["kind"] == "runtime.order_submitted")
    assert order_event["instrument_id"] == "EQUITY.US.NASDAQ.AAPL"
    assert order_event["correlation_id"] == "md:EQUITY.US.NASDAQ.AAPL:1m:2026-01-02T14:31:00+00:00"


def test_live_runtime_session_emits_order_and_fill_trace_metadata() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    account_id = AccountId("acct-live-trace")
    strategy_id = StrategyId("strategy-live-trace")
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            run_id=RuntimeRunId("run-live-trace"),
            account_id=account_id,
            strategy_id=strategy_id,
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_FilledExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    envelopes = [event.to_envelope() for event in sink.events]
    order_event = next(row for row in envelopes if row["kind"] == "runtime.order_submitted")
    broker_event = next(row for row in envelopes if row["kind"] == "runtime.broker_report")
    fill_event = next(row for row in envelopes if row["kind"] == "runtime.fill_applied")

    assert order_event["payload"]["client_order_id"] == "live-client-000001"
    assert broker_event["payload"]["client_order_id"] == "live-client-000001"
    assert fill_event["payload"]["client_order_id"] == "live-client-000001"
    assert fill_event["payload"]["order_id"] == "live-000001"
    assert fill_event["payload"]["fill_id"] == "live-000001-fill"
    assert fill_event["correlation_id"] == order_event["correlation_id"]
    assert fill_event["account_id"] == account_id.value
    assert fill_event["strategy_id"] == strategy_id.value


def test_live_runtime_session_blocks_intents_when_paused_or_degraded() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-default")
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
        )
    )

    session.start()
    session.pause()
    paused = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    session.resume()
    session.degrade()
    degraded = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))

    assert adapter.seen == []
    assert paused.reason_code == "RUNTIME_PAUSED"
    assert degraded.reason_code == "RUNTIME_DEGRADED"


def test_live_runtime_session_reconnect_blocks_orders_until_reconciled() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live import LiveRuntimeState
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_FixedTargetStrategy(Decimal("1")),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
            sink=sink,
        )
    )

    session.start()
    disconnected_state = session.on_broker_disconnect(reason="socket closed")
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    failed_reconnect_state = session.on_broker_reconnect(
        reason="socket restored",
        reconciliation_passed=False,
    )
    still_blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))
    recovered_state = session.on_broker_reconnect(
        reason="open orders and positions reconciled",
        reconciliation_passed=True,
    )
    accepted = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 32, tzinfo=UTC)))

    event_kinds = [event.kind for event in sink.events]
    assert disconnected_state is LiveRuntimeState.DEGRADED
    assert failed_reconnect_state is LiveRuntimeState.DEGRADED
    assert recovered_state is LiveRuntimeState.RUNNING
    assert blocked.reason_code == "RUNTIME_DEGRADED"
    assert still_blocked.reason_code == "RUNTIME_DEGRADED"
    assert len(adapter.seen) == 1
    assert len(accepted.orders) == 1
    assert "runtime.broker_disconnected" in event_kinds
    assert "runtime.broker_reconnected" in event_kinds


def test_live_runtime_session_blocks_orders_after_delayed_market_data_permission() -> None:
    from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_FixedTargetStrategy(Decimal("1")),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
            sink=sink,
        )
    )

    session.start()
    permission_result = session.on_market_data_source_event(
        MarketDataPermissionEvent(
            source_id="ibkr-paper-md",
            permission_state=MarketDataPermissionState.DELAYED,
            provider_market_data_type=3,
            request_id=7,
        )
    )
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    event_kinds = [event.kind for event in sink.events]
    assert permission_result.reason_code == "RUNTIME_DEGRADED"
    assert blocked.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []
    assert "market_data_permission_changed" in event_kinds
    assert "runtime.degraded" in event_kinds


def test_live_runtime_session_blocks_orders_after_market_data_subscription_failure() -> None:
    from qts.data.sources.streaming_market_data_source import (
        StreamingMarketDataSubscriptionEvent,
        StreamingMarketDataSubscriptionEventType,
    )
    from qts.data.subscriptions import LogicalSubscription, logical_key
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    subscription = LogicalSubscription("strategy-a", instrument_id, "1m")
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_FixedTargetStrategy(Decimal("1")),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
            sink=sink,
        )
    )

    session.start()
    failure_result = session.on_market_data_source_event(
        StreamingMarketDataSubscriptionEvent(
            event_type=StreamingMarketDataSubscriptionEventType.FAILED,
            source_id="ibkr-paper-md",
            instrument_id=instrument_id,
            subscription=logical_key(subscription),
            broker_symbol="AAPL",
            observed_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            reason="reqMktData failed",
        )
    )
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    event_kinds = [event.kind for event in sink.events]
    failure_event = next(
        event for event in sink.events if event.kind == "market_data_subscription_failed"
    )
    assert failure_result.reason_code == "RUNTIME_DEGRADED"
    assert blocked.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []
    assert "runtime.degraded" in event_kinds
    assert failure_event.payload["reason"] == "reqMktData failed"


def test_live_runtime_session_resolves_ids_and_filters_by_topology() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-live-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._BuyOnceStrategy",
                account_id=AccountId("acct-topo"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
            runtime_topology=topology,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    skipped = session.on_market_data(
        _bar_for_instrument(
            datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            InstrumentId("EQUITY.US.NASDAQ.GOOG"),
        )
    )

    assert len(adapter.seen) == 1
    assert skipped.market_data == ()
    assert skipped.reason_code == "INSTRUMENT_NOT_SUBSCRIBED"
    assert len(skipped.account_snapshots) == 1
    envelopes = [event.to_envelope() for event in sink.events]
    assert {row["account_id"] for row in envelopes} == {"acct-topo"}
    assert {row["strategy_id"] for row in envelopes} == {"strat-topo"}


def test_live_runtime_session_runs_multiple_strategies_in_one_account_topology() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-multi-strategy-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo-multi"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-a"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._FixedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-b"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._FixedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
            runtime_topology=topology,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert len(adapter.seen) == 1
    assert len(result.orders) == 1
    assert result.account_snapshot is not None
    assert result.account_snapshots == (
        (
            AccountId("acct-topo-multi"),
            result.account_snapshot,
        ),
    )
    assert len({order.broker_order_id for order in result.orders}) == 1
    assert result.orders[0].broker_order_id == "live-000001"
    assert adapter.seen[0].quantity == Decimal("3")

    strategy_ids_from_orders = {
        envelope["strategy_id"]
        for envelope in (event.to_envelope() for event in sink.events)
        if envelope["kind"] == "runtime.order_submitted"
    }
    assert strategy_ids_from_orders == {"strat-multi-a"}
    contributing_ids = {
        tuple(event_payload["payload"]["contributing_strategy_ids"])
        for event_payload in (
            event.to_envelope()
            for event in sink.events
            if event.to_envelope()["kind"] == "runtime.order_submitted"
        )
    }
    assert contributing_ids == {("strat-multi-a", "strat-multi-b")}


def test_live_runtime_session_separate_conflict_groups_do_not_mix_targets() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-conflict-group-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo-multi"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-a"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._FixedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                conflict_group="group-a",
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-b"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._FixedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                conflict_group="group-b",
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    adapter = _RecordingExecutionAdapter()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert [order.quantity for order in adapter.seen] == [Decimal("1"), Decimal("2")]


def test_live_runtime_session_rejects_conflicting_targets_with_reject_conflict_policy() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-conflict-reject-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo-multi"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-a"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._SignedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                signal_aggregation_policy="reject_conflict",
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-b"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._SignedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                signal_aggregation_policy="reject_conflict",
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategies=(_SignedTargetStrategy(Decimal("1")), _SignedTargetStrategy(Decimal("-1"))),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
            sink=sink,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert any(event.kind == "runtime.signal_conflict_detected" for event in sink.events)
    assert any(event.kind == "runtime.signal_rejected" for event in sink.events)


def test_live_runtime_session_routes_intents_to_multi_account_topology_partitions() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    account_a = AccountId("acct-topo-multi-a")
    account_b = AccountId("acct-topo-multi-b")
    account_actor_a = AccountActor(
        initial_cash={"USD": Decimal("10000")},
        account_id=account_a,
    )
    account_actor_b = AccountActor(
        initial_cash={"USD": Decimal("10000")},
        account_id=account_b,
    )
    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-multi-account-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-topology-a"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-topology-b"),
                strategy_class="tests.unit.runtime.test_live_runtime_session._FixedTargetStrategy",
                account_id=account_b,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    adapter = _FilledExecutionAdapter()
    sink = _RecordingSink()
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            account_actors={account_a: account_actor_a, account_b: account_actor_b},
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            sink=sink,
            runtime_topology=topology,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert len(adapter.seen) == 2
    assert adapter.seen[0].account_id == account_a
    assert adapter.seen[1].account_id == account_b
    assert account_actor_a.snapshot().positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert account_actor_b.snapshot().positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("2")
    assert result.account_snapshot is not None
    assert result.account_snapshot.account_id == account_a
    snapshot_map = {
        account_id.value: snapshot
        for account_id, snapshot in result.account_snapshots
        if account_id is not None
    }
    assert snapshot_map[account_a.value].positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert snapshot_map[account_b.value].positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("2")

    event_pairs = {
        (
            envelope["strategy_id"],
            envelope["account_id"],
        )
        for envelope in (event.to_envelope() for event in sink.events)
        if envelope["kind"] == "runtime.order_submitted"
    }
    assert event_pairs == {
        ("strat-multi-topology-a", "acct-topo-multi-a"),
        ("strat-multi-topology-b", "acct-topo-multi-b"),
    }

    signal_received_events = [
        event.to_envelope() for event in sink.events if event.kind == "runtime.signal_received"
    ]
    signal_aggregated_events = [
        event.to_envelope() for event in sink.events if event.kind == "runtime.signal_aggregated"
    ]
    assert len(signal_received_events) == 2
    assert len(signal_aggregated_events) == 2
    assert {event["strategy_id"] for event in signal_received_events} == {
        "strat-multi-topology-a",
        "strat-multi-topology-b",
    }
    contributing_ids = {
        tuple(event["payload"]["contributing_strategy_ids"]) for event in signal_aggregated_events
    }
    assert contributing_ids == {("strat-multi-topology-a",), ("strat-multi-topology-b",)}
    for event in signal_aggregated_events:
        assert event["payload"]["aggregation_policy"] == "sum_targets"


def test_live_runtime_session_observation_mode_keeps_market_data_without_orders() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-default")
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            order_submission_enabled=False,
            account_id=account_id,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert result.reason_code == "ORDER_SUBMISSION_DISABLED"
    assert result.market_data[0].instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
