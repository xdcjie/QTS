from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy


def _bar(start: datetime, close: str = "100") -> Bar:
    from qts.core.ids import InstrumentId

    price = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=price,
        high=price,
        low=price,
        close=price,
        is_complete=True,
    )


class BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.done = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self.done:
            ctx.target_quantity(self.asset, Decimal("1"))
            self.done = True


class RoundTripStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self.count = 0

    def on_bar(self, ctx: Any, bar: object) -> None:
        self.count += 1
        if self.count == 1:
            ctx.target_quantity(self.asset, Decimal("1"))
        if self.count == 2:
            ctx.close(self.asset)


def test_streaming_equity_metrics_reports_return_drawdown_and_count() -> None:
    from qts.reporting.backtest import StreamingEquityMetrics

    equity_metrics = StreamingEquityMetrics()
    for value in [Decimal("100"), Decimal("110"), Decimal("105"), Decimal("120")]:
        equity_metrics.update(value)
    metrics = equity_metrics.to_payload()

    assert metrics["points"] == 4
    assert metrics["total_return"] == Decimal("0.2")
    assert metrics["max_drawdown"] == Decimal("0.04545454545454545454545454545")


def test_streaming_equity_metrics_rejects_empty_curve() -> None:
    from qts.reporting.backtest import StreamingEquityMetrics

    with pytest.raises(ValueError, match="equity curve"):
        StreamingEquityMetrics().to_payload()


def test_zero_cost_backtest_fill_preserves_existing_cash_behavior(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestCostModel, BacktestEngine

    from tests.support.backtest_streaming import run_engine_streaming

    captured = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(),
        ),
        tmp_path / "zero-cost",
    )

    assert captured.result.final_account.cash["USD"] == Decimal("9900")
    assert Decimal(captured.trade_ledger[0]["commission"]) == Decimal("0")


def test_fixed_commission_reduces_cash_and_is_recorded_in_report(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestCostModel, BacktestEngine

    from tests.support.backtest_streaming import run_engine_streaming

    captured = run_engine_streaming(
        BacktestEngine(
            strategy=BuyOnceStrategy(),
            bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(fixed_commission_per_contract=Decimal("2.50")),
        ),
        tmp_path / "fixed-commission",
    )

    assert captured.result.final_account.cash["USD"] == Decimal("9897.50")
    assert Decimal(captured.trade_ledger[0]["commission"]) == Decimal("2.50")


def test_slippage_moves_buy_fill_up_and_sell_fill_down(tmp_path: Path) -> None:
    from qts.backtest.engine import BacktestCostModel, BacktestEngine

    from tests.support.backtest_streaming import run_engine_streaming

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=RoundTripStrategy(),
            bars=[_bar(start), _bar(start + timedelta(minutes=1))],
            initial_cash=Decimal("10000"),
            cost_model=BacktestCostModel(slippage_bps=Decimal("100")),
        ),
        tmp_path / "slippage",
    )

    assert [Decimal(row["fill_price"]) for row in captured.trade_ledger] == [
        Decimal("101.00"),
        Decimal("99.00"),
    ]
    assert captured.result.final_account.cash["USD"] == Decimal("9998.00")
