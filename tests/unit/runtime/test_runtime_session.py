from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, RuntimeRunId, StrategyId
from qts.domain.market_data import Bar
from qts.domain.orders import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderFill,
    OrderIntent,
    OrderSide,
)
from qts.domain.risk import OrderRiskRequest, RiskDecision
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
from qts.runtime.topology import (
    AccountRuntimeSpec,
    MarketDataRouteSpec,
    RuntimeMode,
    RuntimeTopology,
    StrategyRuntimeSpec,
)
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy, TargetIntent


def test_runtime_session_delegates_market_data_to_coordinator() -> None:
    from qts.runtime.session import RuntimeSession

    source = inspect.getsource(RuntimeSession.on_market_data)

    assert "return self._market_data_coordinator.on_market_data(source_bar)" in source
    assert "pipeline.execute_bar" not in source
    assert "runtime.order_submitted" not in source


def test_runtime_session_delegates_broker_lifecycle_and_rollback() -> None:
    from qts.runtime.session import RuntimeSession

    recover_source = inspect.getsource(RuntimeSession.recover)
    reconnect_source = inspect.getsource(RuntimeSession.on_broker_reconnect)
    rollback_source = inspect.getsource(RuntimeSession.rollback)

    assert "return self._recovery_coordinator.recover()" in recover_source
    assert "runtime.state_transition" not in recover_source
    assert "return self._broker_lifecycle.on_broker_reconnect" in reconnect_source
    assert "runtime.broker_reconnected" not in reconnect_source
    assert "return self._rollback_coordinator.rollback(command)" in rollback_source
    assert "runtime.rollback" not in rollback_source


def test_runtime_session_public_surface_stays_thin() -> None:
    from qts.runtime.session import RuntimeSession

    public_members = [
        name
        for name, member in RuntimeSession.__dict__.items()
        if not name.startswith("_") and (inspect.isfunction(member) or isinstance(member, property))
    ]

    assert len(public_members) <= 16


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


def _live_capital_request(
    *,
    account_id: AccountId,
    strategy_id: StrategyId | None = None,
) -> Any:
    from qts.runtime.live_capital import LiveCapitalEnablementRequest, OperatorSignoff

    strategy_id = strategy_id or StrategyId("strategy")
    return LiveCapitalEnablementRequest(
        operator_signoff=OperatorSignoff(
            operator_id="operator-live",
            reason="unit test live-capital gate",
            risk_approver_id="risk-live",
            engineering_approver_id="engineering-live",
            expires_at=datetime(2099, 12, 31, tzinfo=UTC),
            strategy_ids=(strategy_id.value,),
            account_ids=(account_id.value,),
            max_notional_limit=Decimal("100000"),
            allowed_instruments=("EQUITY.US.NASDAQ.AAPL",),
        ),
        strategy_id=strategy_id.value,
        account_id=account_id.value,
        instrument_id="EQUITY.US.NASDAQ.AAPL",
        requested_notional=Decimal("100"),
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


class _RejectAllRiskRule:
    """Reject every order request for partition-boundary tests."""

    def check(self, request: OrderRiskRequest) -> RiskDecision:
        _ = request
        return RiskDecision.rejected("ACCOUNT_BLOCKED", "account risk blocked order")


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
        bar_time: object | None = None,
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
        bar_time: object | None = None,
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


@dataclass(slots=True)
class _RecordingReconnectReconciliation:
    passed: bool
    reason_code: str | None = None
    drift_count: int = 0
    unresolved_callback_count: int = 0
    calls: list[str] = field(default_factory=list)

    def resubscribe_market_data(self) -> None:
        self.calls.append("market_data")

    def refresh_open_orders(self) -> None:
        self.calls.append("open_orders")

    def refresh_positions(self) -> None:
        self.calls.append("positions")

    def refresh_executions(self) -> None:
        self.calls.append("executions")

    def refresh_account_summary(self) -> None:
        self.calls.append("account_summary")

    def reconcile_after_reconnect(self) -> Any:
        from qts.runtime.broker_lifecycle import BrokerReconnectReconciliationResult

        self.calls.append("reconcile")
        return BrokerReconnectReconciliationResult(
            passed=self.passed,
            reason_code=self.reason_code,
            drift_count=self.drift_count,
            unresolved_callback_count=self.unresolved_callback_count,
        )


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


def test_runtime_session_submits_only_through_actor_execution_path() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.state import RuntimeSessionState as RuntimeSessionState

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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

    assert session.start() is RuntimeSessionState.RUNNING
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
        "runtime.risk_decision",
        "runtime.order_submitted",
        "runtime.broker_report",
        "runtime.account_snapshot",
    ]


def test_runtime_session_writes_contextual_runtime_event_envelope() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.risk.rules.max_notional import MaxNotionalRule
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    account_id = AccountId("acct-live-1")
    strategy_id = StrategyId("strategy-live-1")
    sink = _RecordingSink()
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DUP1234567",
        )
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            run_id=RuntimeRunId("run-live-1"),
            mode=RuntimeMode.PAPER_BROKER,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
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


def test_runtime_session_emits_order_and_fill_trace_metadata() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    account_id = AccountId("acct-live-trace")
    strategy_id = StrategyId("strategy-live-trace")
    sink = _RecordingSink()
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_blocks_intents_when_paused_or_degraded() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_reconnect_blocks_orders_until_reconciled() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.state import RuntimeSessionState as RuntimeSessionState

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    reconciliation = _RecordingReconnectReconciliation(passed=False, reason_code="DRIFT")
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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
            broker_reconnect_reconciliation=reconciliation,
        )
    )

    session.start()
    disconnected_state = session.on_broker_disconnect(reason="socket closed")
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    failed_reconnect_state = session.on_broker_reconnect(reason="socket restored")
    still_blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))
    reconciliation.passed = True
    reconciliation.reason_code = None
    reconciliation.drift_count = 0
    reconciliation.unresolved_callback_count = 0
    recovered_state = session.on_broker_reconnect(reason="open orders and positions reconciled")
    accepted = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 32, tzinfo=UTC)))

    event_kinds = [event.kind for event in sink.events]
    assert disconnected_state is RuntimeSessionState.DEGRADED
    assert failed_reconnect_state is RuntimeSessionState.DEGRADED
    assert recovered_state is RuntimeSessionState.RUNNING
    assert blocked.reason_code == "RUNTIME_DEGRADED"
    assert still_blocked.reason_code == "RUNTIME_DEGRADED"
    assert len(adapter.seen) == 1
    assert len(accepted.orders) == 1
    assert "runtime.broker_disconnected" in event_kinds
    assert "runtime.broker_reconnected" in event_kinds
    assert "runtime.reconciliation_passed" in event_kinds
    assert reconciliation.calls == [
        "market_data",
        "open_orders",
        "positions",
        "executions",
        "account_summary",
        "reconcile",
        "market_data",
        "open_orders",
        "positions",
        "executions",
        "account_summary",
        "reconcile",
    ]


def test_runtime_session_reconnect_requires_configured_reconciliation_boundary() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.state import RuntimeSessionState as RuntimeSessionState

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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
    session.on_broker_disconnect(reason="socket closed")
    reconnect_state = session.on_broker_reconnect(reason="socket restored")
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert reconnect_state is RuntimeSessionState.DEGRADED
    assert blocked.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []
    failed_events = [
        event for event in sink.events if event.kind == "runtime.reconciliation_failed"
    ]
    assert failed_events[-1].payload["reason_code"] == "RECONNECT_RECONCILIATION_NOT_CONFIGURED"


def test_runtime_session_reconnect_keeps_degraded_for_unresolved_callbacks() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.state import RuntimeSessionState as RuntimeSessionState

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    reconciliation = _RecordingReconnectReconciliation(
        passed=False,
        reason_code="UNRESOLVED_CALLBACKS",
        unresolved_callback_count=2,
    )
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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
            broker_reconnect_reconciliation=reconciliation,
        )
    )

    session.start()
    session.on_broker_disconnect(reason="socket closed")
    reconnect_state = session.on_broker_reconnect(reason="socket restored")
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert reconnect_state is RuntimeSessionState.DEGRADED
    assert blocked.reason_code == "RUNTIME_DEGRADED"
    assert adapter.seen == []
    failed_event = [
        event for event in sink.events if event.kind == "runtime.reconciliation_failed"
    ][-1]
    assert failed_event.payload["reason_code"] == "UNRESOLVED_CALLBACKS"
    assert failed_event.payload["unresolved_callback_count"] == 2


def test_runtime_session_blocks_orders_after_delayed_market_data_permission() -> None:
    from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_records_market_data_risk_rejection_evidence() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-market-data-risk")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            operator_signoff_id="ops-approval-md-risk",
        ),
        live_capital_request=_live_capital_request(account_id=account_id),
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
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
            sink=sink,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert result.orders == ()
    assert adapter.seen == []
    risk_event = next(
        event.to_envelope() for event in sink.events if event.kind == "runtime.risk_rejected"
    )
    assert risk_event["payload"]["reason_code"] == "MARKET_DATA_PERMISSION_UNKNOWN"
    assert "market_data" in risk_event["payload"]["evidence"]


def test_runtime_session_blocks_orders_after_market_data_subscription_failure() -> None:
    from qts.data.sources.streaming_market_data_source import (
        StreamingMarketDataSubscriptionEvent,
        StreamingMarketDataSubscriptionEventType,
    )
    from qts.data.subscriptions import LogicalSubscription, logical_key
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-default")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    subscription = LogicalSubscription("strategy-a", instrument_id, "1m")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_resolves_ids_and_filters_by_topology() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
                strategy_class="tests.unit.runtime.test_runtime_session._BuyOnceStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_runs_multiple_strategies_in_one_account_topology() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
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
    envelopes = [event.to_envelope() for event in sink.events]
    signal_event = next(row for row in envelopes if row["kind"] == "runtime.signal_aggregated")
    risk_event = next(row for row in envelopes if row["kind"] == "runtime.risk_decision")
    order_event = next(row for row in envelopes if row["kind"] == "runtime.order_submitted")
    report_event = next(row for row in envelopes if row["kind"] == "runtime.broker_report")

    assert (
        risk_event["payload"]["aggregation_decision_id"]
        == signal_event["payload"]["aggregation_decision_id"]
    )
    assert risk_event["payload"]["contributing_strategy_ids"] == [
        "strat-multi-a",
        "strat-multi-b",
    ]
    assert order_event["payload"]["contributing_strategy_ids"] == [
        "strat-multi-a",
        "strat-multi-b",
    ]
    assert (
        report_event["payload"]["aggregation_decision_id"]
        == signal_event["payload"]["aggregation_decision_id"]
    )
    assert report_event["payload"]["contributing_strategy_ids"] == [
        "strat-multi-a",
        "strat-multi-b",
    ]


def test_runtime_session_separate_conflict_groups_do_not_mix_targets() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                conflict_group="group-a",
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_rejects_conflicting_targets_with_reject_conflict_policy() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
                strategy_class="tests.unit.runtime.test_runtime_session._SignedTargetStrategy",
                account_id=AccountId("acct-topo-multi"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
                signal_aggregation_policy="reject_conflict",
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._SignedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
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
    envelopes = [event.to_envelope() for event in sink.events]
    rejected_event = next(row for row in envelopes if row["kind"] == "runtime.signal_rejected")
    conflict_event = next(
        row for row in envelopes if row["kind"] == "runtime.signal_conflict_detected"
    )
    assert rejected_event["payload"]["rejected_strategy_ids"] == [
        "strat-multi-a",
        "strat-multi-b",
    ]
    assert conflict_event["payload"]["rejected_strategy_ids"] == [
        "strat-multi-a",
        "strat-multi-b",
    ]


def test_runtime_session_routes_intents_to_multi_account_topology_partitions() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-multi-topology-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_position_snapshot_partitioned_by_account() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    account_a = AccountId("acct-position-a")
    account_b = AccountId("acct-position-b")
    account_actor_a = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_a)
    account_actor_b = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_b)
    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-position-partitions"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-position-a"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-position-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_FilledExecutionAdapter(),
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            account_actors={account_a: account_actor_a, account_b: account_actor_b},
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert result.account_snapshot is None
    snapshot_map = {account_id: snapshot for account_id, snapshot in result.account_snapshots}
    assert set(snapshot_map) == {account_a, account_b}
    assert snapshot_map[account_a].positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("1")
    assert snapshot_map[account_b].positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("2")


def test_reconciliation_snapshot_partitioned_by_account() -> None:
    from qts.risk.kill_switch import RuntimeKillSwitchCommand
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor, ApplyFill
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession
    from qts.runtime.state_recovery import InMemorySnapshotStore

    account_a = AccountId("acct-reconcile-a")
    account_b = AccountId("acct-reconcile-b")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    account_actor_a = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_a)
    account_actor_b = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_b)
    account_actor_a.handle(
        ApplyFill(
            fill=OrderFill(
                fill_id="fill-reconcile-a",
                order_id=OrderId("ord-reconcile-a"),
                account_id=account_a,
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
                price=Decimal("100"),
            ),
            currency="USD",
            multiplier=Decimal("1"),
        )
    )
    account_actor_b.handle(
        ApplyFill(
            fill=OrderFill(
                fill_id="fill-reconcile-b",
                order_id=OrderId("ord-reconcile-b"),
                account_id=account_b,
                instrument_id=instrument_id,
                side=OrderSide.BUY,
                quantity=Decimal("2"),
                price=Decimal("100"),
            ),
            currency="USD",
            multiplier=Decimal("1"),
        )
    )
    store_a = InMemorySnapshotStore()
    store_b = InMemorySnapshotStore()
    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-reconciliation-partitions"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-reconcile-a"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-reconcile-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_RecordingExecutionAdapter(),
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            account_actors={account_a: account_actor_a, account_b: account_actor_b},
            snapshot_stores={account_a: store_a, account_b: store_b},
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    session.start()
    evidence = session.activate_kill_switch(
        RuntimeKillSwitchCommand(
            operator_id="ops-reconcile",
            reason="capture partitioned reconciliation snapshots",
            cancel_active_orders=False,
        )
    )

    assert set(evidence.snapshot_refs) == {
        "account:acct-reconcile-a",
        "account:acct-reconcile-b",
    }
    snapshot_a = store_a.load("account:acct-reconcile-a")
    snapshot_b = store_b.load("account:acct-reconcile-b")
    assert snapshot_a is not None
    assert snapshot_b is not None
    assert snapshot_a.payload["cash"] == {"USD": "9900"}
    assert snapshot_b.payload["cash"] == {"USD": "9800"}
    assert snapshot_a.payload["positions"] == {"EQUITY.US.NASDAQ.AAPL": "1"}
    assert snapshot_b.payload["positions"] == {"EQUITY.US.NASDAQ.AAPL": "2"}


def test_cash_reservation_for_account_a_never_blocks_account_b() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    account_a = AccountId("acct-cash-a")
    account_b = AccountId("acct-cash-b")
    account_actor_a = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_a)
    account_actor_b = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_b)
    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-cash-reservation-partitions"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-cash-a"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-cash-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            risk_engines={
                account_a: RiskEngine([_RejectAllRiskRule()]),
                account_b: RiskEngine([]),
            },
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            account_actors={account_a: account_actor_a, account_b: account_actor_b},
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert [intent.account_id for intent in adapter.seen] == [account_b]
    assert account_actor_a.snapshot().positions == {}
    assert account_actor_a.snapshot().cash["USD"] == Decimal("10000")
    assert account_actor_b.snapshot().positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("2")
    assert [order.intent.account_id for order in result.orders] == [account_b]


def test_runtime_session_uses_account_partition_risk_engine() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    account_a = AccountId("acct-risk-a")
    account_b = AccountId("acct-risk-b")
    account_actor_a = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_a)
    account_actor_b = AccountActor(initial_cash={"USD": Decimal("10000")}, account_id=account_b)
    topology = RuntimeTopology(
        run_id=RuntimeRunId("topology-partition-risk-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-risk-a"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-risk-b"),
                strategy_class="tests.unit.runtime.test_runtime_session._FixedTargetStrategy",
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategies=(_FixedTargetStrategy(Decimal("1")), _FixedTargetStrategy(Decimal("2"))),
            risk_engine=RiskEngine([]),
            risk_engines={
                account_a: RiskEngine([_RejectAllRiskRule()]),
                account_b: RiskEngine([]),
            },
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            account_actors={account_a: account_actor_a, account_b: account_actor_b},
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert [intent.account_id for intent in adapter.seen] == [account_b]
    assert account_actor_a.snapshot().positions == {}
    assert account_actor_b.snapshot().positions[
        InstrumentId("EQUITY.US.NASDAQ.AAPL")
    ].quantity == Decimal("2")
    assert [order.intent.account_id for order in result.orders] == [account_b]


def test_runtime_session_observation_mode_keeps_market_data_without_orders() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-default")
    session = RuntimeSession(
        RuntimeSessionDependencies(
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


def test_runtime_session_live_mode_requires_startup_decision_for_orders() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-startup")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE,
            execution_environment=ExecutionEnvironment.BROKER,
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
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert result.reason_code == "LIVE_STARTUP_NOT_ALLOWED"


def test_runtime_session_start_writes_startup_gate_evidence() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    sink = _RecordingSink()
    account_id = AccountId("acct-live-startup-evidence")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            operator_signoff_id="ops-approval-1",
        ),
        live_capital_request=_live_capital_request(account_id=account_id),
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
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
            account_id=account_id,
        )
    )

    session.start()

    startup_event = next(event for event in sink.events if event.kind == "runtime.startup_gate")
    assert startup_event.payload["checklist_hash"] == startup_decision.checklist.checklist_hash
    assert startup_event.payload["checks"][0]["evidence"]


def test_paper_broker_runtime_session_requires_startup_decision_for_orders() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-paper-broker-startup")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.PAPER_BROKER,
            execution_environment=ExecutionEnvironment.BROKER,
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
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert result.reason_code == "BROKER_STARTUP_NOT_ALLOWED"


def test_runtime_session_observation_permission_blocks_orders() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-observation-permission")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE_OBSERVATION,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
        )
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE_OBSERVATION,
            execution_environment=ExecutionEnvironment.DISABLED,
            startup_decision=startup_decision,
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
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert result.reason_code == "OBSERVATION_ONLY"


def test_runtime_session_permission_block_writes_runtime_order_result_evidence() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("acct-live-permission-block")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE_OBSERVATION,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
        )
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE_OBSERVATION,
            execution_environment=ExecutionEnvironment.DISABLED,
            startup_decision=startup_decision,
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
            sink=sink,
            account_id=account_id,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    blocked_events = [event for event in sink.events if event.kind == "order_blocked_by_permission"]
    assert adapter.seen == []
    assert result.reason_code == "OBSERVATION_ONLY"
    assert len(result.order_results) == 1
    assert result.order_results[0].accepted is False
    assert result.order_results[0].reason_code == "OBSERVATION_ONLY"
    assert len(blocked_events) == 1
    assert blocked_events[0].payload["reason_code"] == "OBSERVATION_ONLY"
    assert blocked_events[0].payload["runtime_order_result"]["accepted"] is False
    assert (
        blocked_events[0].payload["startup_checklist"]["checklist_hash"]
        == startup_decision.checklist.checklist_hash
    )


def test_runtime_session_paper_permission_does_not_permit_live_account_order() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import BrokerRuntimeStartupDecision, validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.permissions import OrderSubmissionPermission
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    sink = _RecordingSink()
    account_id = AccountId("DU1234567")
    paper_startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.PAPER_BROKER,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            broker_account_code="DUP1234567",
        )
    )
    startup_decision = BrokerRuntimeStartupDecision(
        status=paper_startup_decision.status,
        mode=RuntimeMode.LIVE,
        order_permission=OrderSubmissionPermission.PAPER_ORDERS_ALLOWED,
        real_order_submission_enabled=False,
        checklist=paper_startup_decision.checklist,
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
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
            sink=sink,
            account_id=account_id,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert adapter.seen == []
    assert result.reason_code == "LIVE_ORDER_PERMISSION_REQUIRED"
    assert len(result.order_results) == 1
    assert result.order_results[0].reason_code == "LIVE_ORDER_PERMISSION_REQUIRED"


def test_runtime_session_live_mode_allows_orders_after_startup_decision() -> None:
    from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.broker_startup import validate_live_startup
    from qts.runtime.config import BrokerRuntimeConfig
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    account_id = AccountId("acct-live-startup-allowed")
    startup_decision = validate_live_startup(
        BrokerRuntimeConfig(
            mode=RuntimeMode.LIVE,
            broker_configured=True,
            account_configured=True,
            risk_configured=True,
            calendar_configured=True,
            kill_switch_configured=True,
            allow_live_orders=True,
            broker_account_code="DU1234567",
            operator_signoff_id="ops-approval-1",
        ),
        live_capital_request=_live_capital_request(account_id=account_id),
    )
    session = RuntimeSession(
        RuntimeSessionDependencies(
            mode=RuntimeMode.LIVE,
            execution_environment=ExecutionEnvironment.BROKER,
            startup_decision=startup_decision,
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
    session.on_market_data_source_event(
        MarketDataPermissionEvent(
            source_id="ibkr-live-md",
            permission_state=MarketDataPermissionState.LIVE,
            provider_market_data_type=1,
            request_id=11,
        )
    )
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert len(adapter.seen) == 1
    assert result.reason_code is None
