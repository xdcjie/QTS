from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, RuntimeRunId, StrategyId
from qts.domain.market_data import Bar
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
)
from qts.runtime.sinks.base import RuntimeEvent, RuntimeEventSink
from qts.runtime.state_recovery import StateSnapshot
from qts.runtime.topology import (
    AccountRuntimeSpec,
    MarketDataRouteSpec,
    RuntimeMode,
    RuntimeTopology,
    StrategyRuntimeSpec,
)
from qts.strategy_sdk import Strategy

from tests.integration.test_paper_runtime_full_chain import (
    _InstrumentContext,
    _portfolio_view,
)


def test_live_kill_switch_blocks_new_orders_and_cancels_active_orders() -> None:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.kill_switch import RuntimeKillSwitchCommand
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
    adapter = _AcceptedThenCancelledExecutionAdapter()
    account_id = AccountId("acct-kill")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    evidence = session.activate_kill_switch(
        RuntimeKillSwitchCommand(operator_id="ops-a", reason="manual halt")
    )
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 31, tzinfo=UTC)))

    assert adapter.submitted_order_ids == [OrderId("live-000001")]
    assert adapter.cancelled_order_ids == [OrderId("live-000001")]
    assert evidence.active_order_ids == ("live-000001",)
    assert evidence.cancelled_order_ids == ("live-000001",)
    assert blocked.reason_code == "KILL_SWITCH_ACTIVE"


def test_live_kill_switch_with_multi_account_topology_cancels_all_active_orders() -> None:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.kill_switch import RuntimeKillSwitchCommand
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
    account_a = AccountId("acct-kill-a")
    account_b = AccountId("acct-kill-b")
    topology = RuntimeTopology(
        run_id=RuntimeRunId("kill-switch-multi-account-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-a"),
                strategy_class="tests.integration.test_live_kill_switch_flow._BuyEveryBarStrategy",
                account_id=account_a,
                subscriptions=(instrument_id,),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-b"),
                strategy_class="tests.integration.test_live_kill_switch_flow._BuyEveryBarStrategy",
                account_id=account_b,
                subscriptions=(instrument_id,),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(instrument_id,),
            ),
        ),
    )
    adapter = _AcceptedThenCancelledExecutionAdapter()
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategies=(_BuyEveryBarStrategy(), _BuyEveryBarStrategy()),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            account_actors={
                account_a: AccountActor(
                    initial_cash={"USD": Decimal("10000")}, account_id=account_a
                ),
                account_b: AccountActor(
                    initial_cash={"USD": Decimal("10000")}, account_id=account_b
                ),
            },
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    assert len(result.orders) == 2

    evidence = session.activate_kill_switch(
        RuntimeKillSwitchCommand(operator_id="ops-b", reason="multi-account halt")
    )

    assert set(evidence.active_order_ids) == {"live-000001", "live-000002"}
    assert set(evidence.cancelled_order_ids) == {"live-000001", "live-000002"}
    assert {order_id.value for order_id in adapter.submitted_order_ids} == {
        "live-000001",
        "live-000002",
    }
    assert {order_id.value for order_id in adapter.cancelled_order_ids} == {
        "live-000001",
        "live-000002",
    }
    assert session.account_snapshot is not None


def test_live_rollback_records_operator_action_and_preserves_event_store_paths() -> None:
    from pathlib import Path

    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeRollbackCommand, RuntimeSession

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
    account_id = AccountId("acct-rollback")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_AcceptedThenCancelledExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
        )
    )

    session.start()
    evidence = session.rollback(
        RuntimeRollbackCommand(
            operator_id="ops-a",
            reason="deploy rollback",
            event_store_paths=(Path("evidence/ibkr/events.ndjson"),),
        )
    )
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert evidence.operator_id == "ops-a"
    assert evidence.event_store_paths == ("evidence/ibkr/events.ndjson",)
    assert evidence.runtime_state == "running"
    assert blocked.reason_code == "KILL_SWITCH_ACTIVE"


def test_kill_switch_keeps_event_and_snapshot_recording_after_orders_are_blocked() -> None:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.kill_switch import RuntimeKillSwitchCommand
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

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
    sink = _RecordingSink()
    snapshot_store = _RecordingSnapshotStore()
    account_id = AccountId("acct-kill-observe")
    session = RuntimeSession(
        RuntimeSessionDependencies(
            run_id=RuntimeRunId("kill-switch-observability-run"),
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_AcceptedThenCancelledExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
            sink=sink,
            snapshot_store=snapshot_store,
        )
    )

    session.start()
    evidence = session.activate_kill_switch(
        RuntimeKillSwitchCommand(
            operator_id="ops-a",
            reason="halt",
            cancel_active_orders=False,
        )
    )
    blocked = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert evidence.run_id == "kill-switch-observability-run"
    assert blocked.reason_code == "KILL_SWITCH_ACTIVE"
    assert "runtime.market_data" in [event.kind for event in sink.events]
    assert "runtime.account_snapshot" in [event.kind for event in sink.events]
    assert snapshot_store.saved
    assert snapshot_store.saved[-1].run_id == RuntimeRunId("kill-switch-observability-run")


def test_rollback_evidence_includes_run_active_orders_and_snapshot_refs() -> None:
    from pathlib import Path

    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeRollbackCommand, RuntimeSession

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
    account_id = AccountId("acct-rollback-rich")
    snapshot_store = _RecordingSnapshotStore()
    session = RuntimeSession(
        RuntimeSessionDependencies(
            run_id=RuntimeRunId("rollback-rich-run"),
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_AcceptedThenCancelledExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=account_id,
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=account_id,
            snapshot_store=snapshot_store,
        )
    )

    session.start()
    session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))
    evidence = session.rollback(
        RuntimeRollbackCommand(
            operator_id="ops-a",
            reason="deploy rollback",
            event_store_paths=(Path("evidence/ibkr/events.ndjson"),),
        )
    )

    assert evidence.run_id == "rollback-rich-run"
    assert evidence.runtime_state == "running"
    assert evidence.active_order_ids == ("live-000001",)
    assert evidence.event_store_paths == ("evidence/ibkr/events.ndjson",)
    assert evidence.snapshot_refs == ("account:acct-rollback-rich",)
    assert snapshot_store.saved[-1].snapshot_id == "account:acct-rollback-rich"


def test_runtime_session_rejects_unauthorized_kill_switch_deactivate() -> None:
    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.kill_switch import RuntimeKillSwitchCommand
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.safety import RuntimeKillSwitchDeactivateCommand
    from qts.runtime.safety_controller import RuntimeSafetyController
    from qts.runtime.session import RuntimeSession

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
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_AcceptedThenCancelledExecutionAdapter(),
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=AccountId("acct-unauth-deactivate"),
            ),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=AccountId("acct-unauth-deactivate"),
        )
    )

    session.start()
    session.activate_kill_switch(RuntimeKillSwitchCommand(operator_id="ops-a", reason="halt"))

    try:
        RuntimeSafetyController(session).deactivate_kill_switch(
            RuntimeKillSwitchDeactivateCommand(
                operator_id="ops-a",
                reason="resume",
                authorized=False,
            )
        )
    except PermissionError as exc:
        assert str(exc) == "kill switch deactivate requires safety authorization"
    else:
        raise AssertionError("unauthorized kill-switch deactivate must fail")


class _BuyEveryBarStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        ctx.target_quantity(self.asset, Decimal("1"))


class _AcceptedThenCancelledExecutionAdapter:
    def __init__(self) -> None:
        self.submitted_order_ids: list[OrderId] = []
        self.cancelled_order_ids: list[OrderId] = []

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
        self.submitted_order_ids.append(intent.order_id)
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
        _ = account_id, strategy_id, client_order_id, correlation_id
        self.cancelled_order_ids.append(order_id)
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


class _RecordingSink(RuntimeEventSink):
    def __init__(self) -> None:
        self.events: list[RuntimeEvent] = []

    def write(self, event: RuntimeEvent) -> None:
        self.events.append(event)


class _RecordingSnapshotStore:
    def __init__(self) -> None:
        self.saved: list[StateSnapshot] = []

    def save(self, snapshot: StateSnapshot) -> None:
        self.saved.append(snapshot)

    def load(self, actor_id: str) -> StateSnapshot | None:
        for snapshot in reversed(self.saved):
            if snapshot.actor_id == actor_id:
                return snapshot
        return None


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
