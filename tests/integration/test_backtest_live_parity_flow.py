from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import AccountId, CorrelationId, InstrumentId, OrderId, StrategyId
from qts.data.events import MarketDataSubscription
from qts.data.historical.adapter import HistoricalMarketDataAdapter
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.domain.market_data import Bar
from qts.domain.risk import RiskDecision
from qts.execution.order_manager import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderIntent,
    OrderSide,
)
from qts.registry.symbol_resolution import StaticSymbolResolver
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.market_data_actor import (
    MarketDataActor,
    MarketDataEvent,
    MarketDataPayload,
)
from qts.runtime.actors.order_manager_actor import OrderManagerActor, SubmitOrder
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import Strategy
from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

from tests.support.order_route import order_route_metadata


@dataclass(slots=True)
class RecordingExecutionAdapter:
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
            report_id=f"{broker_order_id}-report",
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
            report_id=f"{broker_order_id}-cancel",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
        )


def test_shared_actor_order_flow_uses_same_messages_for_execution_adapters() -> None:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    adapter = RecordingExecutionAdapter()
    account_id = AccountId("acct-parity")
    strategy_id = StrategyId("strategy-parity")
    account_actor = AccountActor(initial_cash={"USD": Decimal("1000")}, account_id=account_id)
    account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
    execution_mailbox = Mailbox()
    order_manager_mailbox = Mailbox()
    order_manager_actor = OrderManagerActor(
        execution_ref=ActorRef(mailbox=execution_mailbox),
        account_ref=account_ref,
        multiplier_by_instrument={instrument_id: Decimal("1")},
        account_id=account_id,
    )
    order_manager_ref = ActorRef(actor=order_manager_actor, mailbox=order_manager_mailbox)
    execution_ref = ActorRef(
        actor=ExecutionActor(order_manager_ref=order_manager_ref, execution_adapter=adapter),
        mailbox=execution_mailbox,
    )
    intent = OrderIntent(
        order_id=OrderId("order-1"),
        account_id=account_id,
        instrument_id=instrument_id,
        side=OrderSide.BUY,
        quantity=Decimal("2"),
    )

    order_manager_ref.tell(
        SubmitOrder(
            intent=intent,
            risk_decision=RiskDecision.approve(),
            broker_order_id="adapter-order-1",
            market_price=Decimal("100"),
            account_id=account_id,
            strategy_id=strategy_id,
            route_metadata=order_route_metadata(
                account_id=account_id,
                strategy_id=strategy_id,
                client_order_id="client-001",
                correlation_id=CorrelationId("corr-001"),
            ),
        )
    )
    order_manager_ref.process_all()
    execution_ref.process_all()
    order_manager_ref.process_all()
    account_ref.process_all()

    assert adapter.seen == [intent]
    assert order_manager_actor.get_order(OrderId("order-1")).state.value == "filled"
    assert order_manager_actor.fills[0].instrument_id == instrument_id
    assert account_actor.snapshot().positions[instrument_id].quantity == Decimal("2")
    assert account_actor.snapshot().cash["USD"] == Decimal("800")


def test_backtest_risk_rejection_does_not_submit_order_or_mutate_account(
    tmp_path: Path,
) -> None:
    from tests.support.backtest_streaming import run_engine_streaming

    class BuyOnce(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("1"))

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bar = Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )

    captured = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnce(),
            bars=[bar],
            initial_cash=Decimal("1000"),
            risk_engine=RiskEngine([MaxNotionalRule(max_notional=Decimal("50"))]),
        ),
        tmp_path / "risk-rejection",
    )
    result = captured.result

    assert captured.orders == ()
    assert captured.fills == ()
    assert result.final_account.cash["USD"] == Decimal("1000")
    assert result.final_account.positions == {}


def test_historical_and_fake_live_market_data_use_same_actor_event_contract(
    tmp_path: Path,
) -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    live_bar = Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("2000"),
        high=Decimal("2000"),
        low=Decimal("2000"),
        close=Decimal("2000"),
        volume=Decimal("1"),
        is_complete=True,
    )
    live_source = FakeStreamingMarketDataAdapter(source_id="fake-live")
    live_source.subscribe(MarketDataSubscription("live-1", instrument_id, timeframe="1m"))

    csv_path = tmp_path / "gc.csv"
    _write_historical_rows(
        csv_path,
        [
            {
                "ts_event": "2026-01-02T14:30:00.000000000Z",
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": "GCQ0",
                "open": "2000",
                "high": "2000",
                "low": "2000",
                "close": "2000",
                "volume": "1",
                "symbol": "GCQ0",
            }
        ],
    )
    historical_source = HistoricalMarketDataAdapter(
        source_id="historical-gc",
        csv_path=csv_path,
        symbol_resolver=StaticSymbolResolver({"GCQ0": instrument_id}),
        source_timeframe="1m",
        start=start,
        end=start + timedelta(minutes=1),
    )
    historical_source.subscribe(MarketDataSubscription("hist-1", instrument_id, timeframe="1m"))

    live_payload = _route_market_data_event(live_source.emit(live_bar).payload)
    historical_payload = _route_market_data_event(next(historical_source.events("hist-1")).payload)

    assert isinstance(live_payload, Bar)
    assert isinstance(historical_payload, Bar)
    assert live_payload.instrument_id == historical_payload.instrument_id == instrument_id
    assert live_payload.close == historical_payload.close == Decimal("2000")
    assert not hasattr(live_payload, "symbol")
    assert not hasattr(historical_payload, "symbol")


def _route_market_data_event(payload: MarketDataPayload) -> object:
    mailbox = Mailbox()
    actor = MarketDataActor(subscribers=(ActorRef(mailbox=mailbox),))
    actor.handle(MarketDataEvent(payload=payload))
    return mailbox.get()


def _write_historical_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
