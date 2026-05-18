"""Anchor: holding period bars reflect actual bar count from open to close.

Domain fact: ``account.position_closed`` events must carry real
``opened_at`` and ``closed_at`` timestamps derived from the bar at
which each fill occurred. The 2.25-year VWAP run surfaced a defect:
every position_closed event had ``opened_at=null`` and
``closed_at=1970-01-01`` (epoch), because ``AccountActor._apply_fill``
hardcoded ``fill_time=None`` and the rest of the execution chain
(``ApplyFill`` → ``ExecutionReport`` → ``OrderExecutionRequest`` →
``SubmitOrder``) had no field to carry the bar's wall-clock time.

Owner: chain ``intent_processing.process_intent`` → ``SubmitOrder``
→ ``OrderExecutionRequest`` → ``SimulatedExecutionAdapter`` →
``ExecutionReport`` → ``ExecutionReportHandler`` → ``ApplyFill`` →
``AccountActor`` → ``HoldingBook.apply_fill``.

Forbidden shortcut: defaulting fill_time to None; defaulting
opened_at to None for backtest fills; computing holding_bars from
event sequence numbers (deterministic timestamps in the envelope
don't reflect real bar wall-clock).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import AccountId, InstrumentId, OrderId
from qts.domain.orders.value_objects import (
    ExecutionReport,
    ExecutionReportStatus,
    OrderFill,
    OrderSide,
)
from qts.portfolio.holdings import HoldingBook
from qts.runtime.actors.account_actor import AccountActor, ApplyFill


def test_holding_book_records_open_and_close_times_from_fills() -> None:
    """When fills carry bar timestamps, opened_at / closed_at propagate."""
    book = HoldingBook()
    instrument = InstrumentId("FUTURE.CME.GC.GCG4")
    open_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    close_time = open_time + timedelta(minutes=5)

    book.apply_fill(
        instrument_id=instrument,
        signed_quantity=Decimal("1"),
        price=Decimal("2000"),
        multiplier=Decimal("100"),
        fill_time=open_time,
    )
    closes = book.apply_fill(
        instrument_id=instrument,
        signed_quantity=Decimal("-1"),
        price=Decimal("2010"),
        multiplier=Decimal("100"),
        fill_time=close_time,
    )

    assert len(closes) == 1
    closed = closes[0]
    assert closed.opened_at == open_time, f"opened_at should be {open_time}, got {closed.opened_at}"
    assert closed.closed_at == close_time


def test_execution_report_can_carry_fill_time() -> None:
    """ExecutionReport must expose a fill_time field for downstream actors."""
    report = ExecutionReport(
        report_id="r1",
        broker_order_id="b1",
        status=ExecutionReportStatus.FILLED,
        filled_quantity=Decimal("1"),
        fill_price=Decimal("2000"),
        fill_id="f1",
        fill_time=datetime(2024, 1, 2, 14, 30, tzinfo=UTC),
    )
    assert report.fill_time == datetime(2024, 1, 2, 14, 30, tzinfo=UTC)


def test_apply_fill_message_can_carry_fill_time() -> None:
    """ApplyFill must expose a fill_time field for AccountActor."""
    fill_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    msg = ApplyFill(
        fill=OrderFill(
            fill_id="f1",
            order_id=OrderId("o1"),
            instrument_id=InstrumentId("FUTURE.CME.GC.GCG4"),
            side=OrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("2000"),
            account_id=AccountId("a1"),
        ),
        currency="USD",
        multiplier=Decimal("100"),
        fill_time=fill_time,
    )
    assert msg.fill_time == fill_time


def test_account_actor_forwards_fill_time_to_holdings() -> None:
    """End-to-end: AccountActor records opened_at from ApplyFill.fill_time."""
    instrument = InstrumentId("FUTURE.CME.GC.GCG4")
    account_id = AccountId("a1")
    actor = AccountActor(initial_cash={"USD": Decimal("100000")}, account_id=account_id)
    open_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    close_time = open_time + timedelta(minutes=5)

    actor.handle(
        ApplyFill(
            fill=OrderFill(
                fill_id="f1",
                order_id=OrderId("o1"),
                instrument_id=instrument,
                side=OrderSide.BUY,
                quantity=Decimal("1"),
                price=Decimal("2000"),
                account_id=account_id,
            ),
            currency="USD",
            multiplier=Decimal("100"),
            fill_time=open_time,
        )
    )
    actor.handle(
        ApplyFill(
            fill=OrderFill(
                fill_id="f2",
                order_id=OrderId("o2"),
                instrument_id=instrument,
                side=OrderSide.SELL,
                quantity=Decimal("1"),
                price=Decimal("2010"),
                account_id=account_id,
            ),
            currency="USD",
            multiplier=Decimal("100"),
            fill_time=close_time,
        )
    )

    events = actor.drain_position_closed_events()
    assert len(events) == 1
    closed = events[0]
    assert closed.opened_at == open_time
    assert closed.closed_at == close_time


@pytest.mark.parametrize(
    ("delta_minutes", "expected_bars"),
    [(1, 1), (5, 5), (60, 60)],
)
def test_holding_bars_from_payload_returns_minute_delta(
    delta_minutes: int, expected_bars: int
) -> None:
    """``BacktestArtifactWriter._holding_bars_from_payload`` converts ISO times to bar count."""
    from qts.reporting.backtest import BacktestArtifactWriter

    open_time = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    close_time = open_time + timedelta(minutes=delta_minutes)

    # The helper is currently a method on the writer; reach into it for the
    # contract test. The exact API may move; the rule is:
    # holding_bars(open ISO, close ISO) == (close - open).total_seconds() // 60.
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        from pathlib import Path

        writer = BacktestArtifactWriter(Path(tmpdir))
        bars = writer._holding_bars_from_payload(open_time.isoformat(), close_time.isoformat())
        assert bars == expected_bars
