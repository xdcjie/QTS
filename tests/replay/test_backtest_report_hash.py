from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


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
        is_complete=True,
    )


class BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.has_ordered = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.has_ordered:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.has_ordered = True


def test_same_backtest_inputs_produce_same_report_hash() -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    bars = [_bar(start), _bar(start + timedelta(minutes=1))]

    left = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=bars,
        initial_cash=Decimal("10000"),
        config={"seed": 42},
        strategy_version="buy-once-v1",
    ).run()
    right = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=bars,
        initial_cash=Decimal("10000"),
        config={"seed": 42},
        strategy_version="buy-once-v1",
    ).run()

    assert left.report_hash == right.report_hash
