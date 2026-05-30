"""Full paper event loop: fake market data produces fills/state through the chain.

This exercises the shared Strategy -> RiskEngine -> OrderManager -> Execution ->
Account chain end to end via a builder-constructed RuntimeSession driven by the
deterministic fake market-data adapter and the simulated execution adapter.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.application.commands.start_runtime import StartRuntimeCommand, start_runtime
from qts.application.services import RuntimeSessionBuilder, RuntimeStartConfig
from qts.core.ids import AccountId, InstrumentId
from qts.data.events import MarketDataSubscription
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.domain.orders import Order, OrderFill, OrderSide
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.mode import RuntimeMode
from qts.strategy_sdk import Strategy
from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter

_INSTRUMENT_ID = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


def _instrument_registry() -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=_INSTRUMENT_ID,
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


def _bar(start: datetime, *, close: Decimal) -> Bar:
    return Bar(
        instrument_id=_INSTRUMENT_ID,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=close,
        high=close,
        low=close,
        close=close,
        volume=Decimal("100"),
        is_complete=True,
    )


def test_paper_runtime_loop_produces_fills_and_account_state() -> None:
    builder = RuntimeSessionBuilder.from_runtime_config(
        RuntimeStartConfig(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            account_id=AccountId("acct-paper-loop"),
            initial_cash={"USD": Decimal("100000")},
        ),
        strategy=_BuyOnceStrategy(),
        instrument_registry=_instrument_registry(),
    )
    result = start_runtime(
        StartRuntimeCommand(
            runtime_mode=RuntimeMode.PAPER_SIMULATED,
            config_ref="configs/paper_simulated.yaml",
            operator_id="ops",
            idempotency_key="paper-loop-1",
            reason="market data loop",
        ),
        session_builder=builder,
    )
    session = result.session
    assert session is not None

    source = FakeStreamingMarketDataAdapter(source_id="paper-loop")
    source.subscribe(
        MarketDataSubscription(
            subscription_id="aapl-1m",
            instrument_id=_INSTRUMENT_ID,
            timeframe="1m",
        )
    )

    fills: list[OrderFill] = []
    orders: list[Order] = []
    start_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    for index in range(3):
        event = source.emit(_bar(start_time + timedelta(minutes=index), close=Decimal("100")))
        assert isinstance(event.payload, Bar)
        loop_result = session.on_market_data(event.payload)
        fills.extend(loop_result.fills)
        orders.extend(loop_result.orders)

    # Exactly one buy filled through the shared chain.
    assert len(fills) == 1
    assert {order.intent.side for order in orders} == {OrderSide.BUY}
    # Account state reflects the fill: 1 share long, cash debited by 1 * 100.
    snapshot = session.account_snapshot
    assert snapshot.positions[_INSTRUMENT_ID].quantity == Decimal("1")
    assert snapshot.cash["USD"] == Decimal("99900")
