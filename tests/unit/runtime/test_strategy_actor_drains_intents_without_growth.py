"""StrategyActor drains emissions per event so context buffers stay bounded (QTS-FINAL-005).

Before the split the emitter accumulated every intent for the lifetime of the
session and the actor sliced ``ctx.intents[before:]``; a long-running live
session leaked memory monotonically. The actor now drains the context each
event, so the undrained buffer returns to empty after every bar/finalize and the
``StrategyBarResult`` still carries exactly that event's intents.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.strategy_actor import (
    StrategyActor,
    StrategyBarEvent,
    StrategyBarResult,
    StrategyFinalize,
    StrategyFinalized,
)
from qts.runtime.mailbox import Mailbox
from qts.strategy_sdk import DataView, PortfolioView, Strategy, StrategyContext

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


class _EmitEachBar(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, incoming: object) -> None:
        ctx.target_quantity(self.asset, Decimal("1"))

    def finalize(self, ctx: Any) -> None:
        ctx.close(self.asset)


class _Resolver:
    def resolve(self, user_symbol: str) -> InstrumentId:
        return _INSTRUMENT


def _bar(index: int) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=index)
    return Bar(
        instrument_id=_INSTRUMENT,
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


def _make_actor() -> tuple[StrategyActor, StrategyContext, Mailbox]:
    context = StrategyContext(instrument_registry=_Resolver())
    outbox = Mailbox()
    actor = StrategyActor(
        strategy=_EmitEachBar(),
        context=context,
        result_ref=ActorRef(mailbox=outbox),
    )
    return actor, context, outbox


def test_each_bar_result_carries_only_that_bars_intents() -> None:
    actor, context, outbox = _make_actor()
    bars = 50
    for i in range(bars):
        actor.handle(
            StrategyBarEvent(
                bar=_bar(i),
                data=DataView(bars={_INSTRUMENT: (_bar(i),)}, as_of=_bar(i).end_time),
                portfolio=PortfolioView(cash=Decimal("1000"), equity=Decimal("1000")),
            )
        )
        # The actor drained: the undrained context buffer is empty after handling.
        assert context.intents == ()

    for _ in range(bars):
        result = outbox.get()
        assert isinstance(result, StrategyBarResult)
        # Every event produced exactly one intent -- no accumulation across bars.
        assert len(result.intents) == 1


def test_context_buffer_does_not_grow_across_many_bars() -> None:
    actor, context, _ = _make_actor()
    for i in range(200):
        actor.handle(
            StrategyBarEvent(
                bar=_bar(i),
                data=DataView(bars={_INSTRUMENT: (_bar(i),)}, as_of=_bar(i).end_time),
                portfolio=PortfolioView(cash=Decimal("1000"), equity=Decimal("1000")),
            )
        )
    # After 200 bars the live emitter holds nothing -- the buffer is bounded.
    assert context.intents == ()
    assert context.cancel_intents == ()


def test_finalize_drains_independently_of_bars() -> None:
    actor, context, outbox = _make_actor()
    actor.handle(
        StrategyBarEvent(
            bar=_bar(0),
            data=DataView(bars={_INSTRUMENT: (_bar(0),)}, as_of=_bar(0).end_time),
            portfolio=PortfolioView(cash=Decimal("1000"), equity=Decimal("1000")),
        )
    )
    outbox.get()  # discard bar result
    actor.handle(StrategyFinalize())
    finalized = outbox.get()
    assert isinstance(finalized, StrategyFinalized)
    assert len(finalized.intents) == 1  # only the finalize close, not the bar's intent
    assert context.intents == ()
