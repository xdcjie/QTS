"""Integration anchor: account.position_closed reaches the backtest sink."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.domain.market_data import Bar

from tests.support.backtest_streaming import run_engine_streaming


def _bar(start: datetime, close: str) -> Bar:
    from qts.core.ids import InstrumentId

    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
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


def test_round_trip_emits_account_position_closed_runtime_event(tmp_path: Path) -> None:
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
                ctx.target_quantity(self.asset, Decimal("1"))
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
                _bar(start + timedelta(minutes=1), "101"),
                _bar(start + timedelta(minutes=2), "102"),
            ],
            initial_cash=Decimal("10000"),
        ),
        tmp_path / "round-trip",
    )

    closed_events = [
        event for event in captured.events if event.get("kind") == "account.position_closed"
    ]
    assert len(closed_events) == 1
    payload = closed_events[0]["payload"]
    assert payload["instrument_id"] == "EQUITY.US.NASDAQ.AAPL"
    assert payload["closed_quantity"] == "1"
    # Open at bar 0 close (100), close at bar 1 close (101); realized = +1.
    assert Decimal(payload["realized_pnl"]) == Decimal("1")


def test_close_reason_metadata_is_written_to_backtest_events(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestEngine
    from qts.strategy_sdk import Strategy

    class ReasonedExitStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.opened = False
            self.closed = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            assert isinstance(bar, Bar)
            if not self.opened:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.opened = True
            elif not self.closed:
                ctx.close(
                    self.asset,
                    metadata={
                        "entry_price": "100",
                        "exit_reason": "long_target_r_touched",
                        "stop_price": "98",
                        "target_price": "104",
                    },
                )
                self.closed = True

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=ReasonedExitStrategy(),
            bars=[
                _bar(start, "100"),
                _bar(start + timedelta(minutes=1), "104"),
            ],
            initial_cash=Decimal("10000"),
        ),
        tmp_path / "reasoned-exit",
    )

    close_intents = [
        event
        for event in captured.events
        if event.get("kind") == "runtime.strategy_intent"
        and event["payload"]["intent_type"] == "close"
    ]
    assert len(close_intents) == 1
    assert close_intents[0]["payload"]["metadata"] == {
        "entry_price": "100",
        "exit_reason": "long_target_r_touched",
        "stop_price": "98",
        "target_price": "104",
    }
