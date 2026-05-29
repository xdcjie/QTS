"""Integration gate: PositionClosed is emitted through the runtime path.

This proves the production emission contract: closing a position surfaces an
``account.position_closed`` runtime event carrying realized PnL *without the
test ever calling* ``DrainPositionClosedEvents``. The backtest actor loop drains
the AccountActor automatically after each processed intent and writes the events
through the shared runtime sink, so observing the event in the sink artifacts is
direct evidence of the auto-drain path.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar

from tests.support.backtest_streaming import run_engine_streaming

_AAPL = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _bar(start: datetime, close: str) -> Bar:
    return Bar(
        instrument_id=_AAPL,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_closing_a_position_emits_position_closed_through_runtime(tmp_path: Path) -> None:
    """A round trip surfaces account.position_closed via the auto-drain path."""
    from qts.backtest.engine import BacktestEngine
    from qts.strategy_sdk import Strategy

    class RoundTripStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.opened = False
            self.closed = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            if not self.opened:
                ctx.target_quantity(self.asset, Decimal("2"))
                self.opened = True
            elif not self.closed:
                ctx.close(self.asset)
                self.closed = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=RoundTripStrategy(),
            bars=[
                _bar(start, "100"),
                _bar(start + timedelta(minutes=1), "110"),
                _bar(start + timedelta(minutes=2), "120"),
            ],
            initial_cash=Decimal("100000"),
        ),
        tmp_path / "round-trip",
    )

    closed_events = [
        event for event in captured.events if event.get("kind") == "account.position_closed"
    ]
    assert len(closed_events) == 1
    payload = closed_events[0]["payload"]
    assert payload["instrument_id"] == _AAPL.value
    assert payload["closed_quantity"] == "2"
    # Open 2 @ bar0 close (100), close 2 @ bar1 close (110): realized = 2 * 10 = 20.
    assert Decimal(payload["realized_pnl"]) == Decimal("20")
