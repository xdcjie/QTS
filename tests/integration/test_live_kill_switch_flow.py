from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import InstrumentId, OrderId
from qts.domain.market_data import Bar
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
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
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession

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
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
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


def test_live_rollback_records_operator_action_and_preserves_event_store_paths() -> None:
    from pathlib import Path

    from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
    from qts.registry.instrument_registry import InstrumentRegistry
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.live_runtime_dependencies import LiveRuntimeDependencies
    from qts.runtime.live_runtime_session import LiveRuntimeSession, RuntimeRollbackCommand

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
    session = LiveRuntimeSession(
        LiveRuntimeDependencies(
            strategy=_BuyEveryBarStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_AcceptedThenCancelledExecutionAdapter(),
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=registry,
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
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
    ) -> ExecutionReport:
        self.submitted_order_ids.append(intent.order_id)
        return ExecutionReport(
            report_id=f"{broker_order_id}-accepted",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
        )

    def cancel_order(self, order_id: OrderId, *, broker_order_id: str) -> ExecutionReport:
        self.cancelled_order_ids.append(order_id)
        return ExecutionReport(
            report_id=f"{broker_order_id}-cancelled",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


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
