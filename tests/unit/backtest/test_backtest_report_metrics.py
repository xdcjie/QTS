from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
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


def test_compute_equity_metrics_reports_return_drawdown_and_count() -> None:
    from qts.backtest.metrics import compute_equity_metrics

    metrics = compute_equity_metrics(
        [Decimal("100"), Decimal("110"), Decimal("105"), Decimal("120")]
    )

    assert metrics["points"] == 4
    assert metrics["total_return"] == Decimal("0.2")
    assert metrics["max_drawdown"] == Decimal("0.04545454545454545454545454545")


def test_compute_equity_metrics_rejects_empty_curve() -> None:
    from qts.backtest.metrics import compute_equity_metrics

    with pytest.raises(ValueError, match="equity curve"):
        compute_equity_metrics([])


def test_backtest_report_serializes_deterministically() -> None:
    from qts.backtest.report import BacktestReport, EquityCurvePoint
    from qts.core.ids import BacktestRunId

    point = EquityCurvePoint(
        time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        equity=Decimal("1000.50"),
    )
    report = BacktestReport(
        run_id=BacktestRunId("bt-test"),
        config_hash="sha256:config",
        dataset_metadata=({"root": "GC"},),
        cost_model={"fixed_commission_per_contract": "0", "slippage_bps": "0"},
        processed_bars=1,
        warmup_bars=0,
        trading_bars=1,
        orders=({"order_id": "bt-000001"},),
        fills=({"fill_id": "fill-001"},),
        trade_ledger=(),
        equity_curve=(point,),
        metrics={"total_return": Decimal("0.1"), "points": 1},
    )

    assert report.to_json() == report.to_json()
    assert '"equity":"1000.50"' in report.to_json()
    assert report.report_hash.startswith("sha256:")


def test_zero_cost_backtest_fill_preserves_existing_cash_behavior() -> None:
    from qts.backtest.engine import BacktestCostModel, BacktestEngine

    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
        initial_cash=Decimal("10000"),
        cost_model=BacktestCostModel(),
    ).run()

    assert result.final_account.cash["USD"] == Decimal("9900")
    assert result.report.trade_ledger[0].commission == Decimal("0")


def test_fixed_commission_reduces_cash_and_is_recorded_in_report() -> None:
    from qts.backtest.engine import BacktestCostModel, BacktestEngine

    result = BacktestEngine(
        strategy=BuyOnceStrategy(),
        bars=[_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))],
        initial_cash=Decimal("10000"),
        cost_model=BacktestCostModel(fixed_commission_per_contract=Decimal("2.50")),
    ).run()

    assert result.final_account.cash["USD"] == Decimal("9897.50")
    assert result.report.trade_ledger[0].commission == Decimal("2.50")


def test_slippage_moves_buy_fill_up_and_sell_fill_down() -> None:
    from qts.backtest.engine import BacktestCostModel, BacktestEngine

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    result = BacktestEngine(
        strategy=RoundTripStrategy(),
        bars=[_bar(start), _bar(start + timedelta(minutes=1))],
        initial_cash=Decimal("10000"),
        cost_model=BacktestCostModel(slippage_bps=Decimal("100")),
    ).run()

    assert [row.fill_price for row in result.report.trade_ledger] == [
        Decimal("101.00"),
        Decimal("99.00"),
    ]
    assert result.final_account.cash["USD"] == Decimal("9998.00")
