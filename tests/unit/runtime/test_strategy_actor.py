from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any


def test_strategy_actor_handles_completed_bar_and_emits_new_intents() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar
    from qts.runtime.actor_ref import ActorRef
    from qts.runtime.actors.strategy_actor import StrategyActor, StrategyBarEvent, StrategyBarResult
    from qts.runtime.mailbox import Mailbox
    from qts.strategy_sdk import DataView, PortfolioView, Strategy, StrategyContext

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bar = Bar(
        instrument_id=instrument_id,
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

    class Resolver:
        def resolve(self, user_symbol: str) -> InstrumentId:
            assert user_symbol == "AAPL"
            return instrument_id

    class BuyOnce(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.sma = ctx.indicator.sma(self.asset, window=1)

        def on_bar(self, ctx: Any, incoming: object) -> None:
            assert incoming == bar
            assert ctx.data.close(self.asset) == Decimal("100")
            assert ctx.portfolio.cash == Decimal("1000")
            assert self.sma.ready is True
            ctx.target_quantity(self.asset, Decimal("3"))

    outbox = Mailbox()
    actor = StrategyActor(
        strategy=BuyOnce(),
        context=StrategyContext(instrument_registry=Resolver()),
        result_ref=ActorRef(mailbox=outbox),
    )

    actor.handle(
        StrategyBarEvent(
            bar=bar,
            data=DataView(bars={instrument_id: (bar,)}, as_of=bar.end_time),
            portfolio=PortfolioView(cash=Decimal("1000"), equity=Decimal("1000")),
        )
    )

    result = outbox.get()
    assert isinstance(result, StrategyBarResult)
    assert result.bar == bar
    assert len(result.intents) == 1
    assert result.intents[0].asset.instrument_id == instrument_id
    assert result.intents[0].value == Decimal("3")
    assert outbox.empty()
