"""Anchor: PositionClosed events flow from AccountActor through the runtime sink.

Domain fact: when a holding crosses through flat, exactly one
``account.position_closed`` runtime event is emitted with the realized PnL
recorded by ``HoldingBook``. The same event drives trade-level statistics so
strategy-side ``realized_pnl`` and report-side trade PnL agree.

Owner: ``AccountActor`` produces the events; ``RuntimeEventWriter`` writes
them; ``BacktestArtifactWriter`` persists them into ``closed_trades.ndjson``.

Forbidden shortcut: buffering ``PositionClosed`` events inside AccountActor
without ever draining them; computing trade-level PnL from raw fills in
parallel to the Holdings book.
"""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders import OrderSide
from qts.execution.order_manager import OrderFill
from qts.runtime.actors.account_actor import AccountActor, ApplyFill
from qts.runtime.runtime_event_writer import RuntimeEventWriter
from qts.runtime.sinks.base import RuntimeEvent


def test_account_actor_drain_returns_and_clears_position_closed_events() -> None:
    actor = AccountActor(
        initial_cash={"USD": Decimal("100000")},
        account_id=AccountId("acct-1"),
    )
    instrument = InstrumentId("EQUITY.US.NASDAQ.AAPL")

    actor.handle(
        ApplyFill(
            fill=OrderFill(
                fill_id="f-1",
                order_id=OrderId("ord-1"),
                instrument_id=instrument,
                side=OrderSide.BUY,
                quantity=Decimal("10"),
                price=Decimal("100"),
                account_id=AccountId("acct-1"),
            ),
            currency="USD",
            multiplier=Decimal("1"),
        )
    )
    assert actor.drain_position_closed_events() == ()

    actor.handle(
        ApplyFill(
            fill=OrderFill(
                fill_id="f-2",
                order_id=OrderId("ord-2"),
                instrument_id=instrument,
                side=OrderSide.SELL,
                quantity=Decimal("10"),
                price=Decimal("110"),
                account_id=AccountId("acct-1"),
            ),
            currency="USD",
            multiplier=Decimal("1"),
        )
    )

    drained = actor.drain_position_closed_events()
    assert len(drained) == 1
    assert drained[0].realized_pnl == Decimal("100")  # 10 shares * (110-100)

    # second drain is empty because the buffer was cleared
    assert actor.drain_position_closed_events() == ()


def test_runtime_event_writer_emits_position_closed_event() -> None:
    from datetime import UTC, datetime

    from qts.core.ids import CorrelationId, StrategyId
    from qts.portfolio.holdings import PositionClosed

    written: list[RuntimeEvent] = []
    writer = RuntimeEventWriter(write=written.append)

    closed = PositionClosed(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        closed_quantity=Decimal("10"),
        exit_price=Decimal("110"),
        realized_pnl=Decimal("100"),
        opened_at=None,
        closed_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
    )

    writer.write_position_closed_events(
        (closed,),
        account_id=AccountId("acct-1"),
        strategy_id=StrategyId("strat-1"),
        correlation_id=CorrelationId("corr-1"),
    )

    assert len(written) == 1
    event = written[0]
    assert event.kind == "account.position_closed"
    assert event.payload["realized_pnl"] == "100"
    assert event.payload["closed_quantity"] == "10"
    assert event.payload["instrument_id"] == "EQUITY.US.NASDAQ.AAPL"
    assert event.account_id == AccountId("acct-1")
