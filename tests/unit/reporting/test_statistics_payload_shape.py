from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


def test_statistics_builder_emits_platform_readiness_metric_set() -> None:
    from qts.reporting.statistics import StatisticsBuilder

    builder = StatisticsBuilder()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    for index, equity in enumerate(
        (Decimal("100000"), Decimal("101000"), Decimal("100500"), Decimal("102000"))
    ):
        builder.on_equity_point(time=start + timedelta(minutes=index), equity=equity)
    builder.on_fill(
        order_id="ord-1",
        instrument_id="EQUITY.US.NASDAQ.AAPL",
        side="buy",
        quantity=Decimal("1"),
        price=Decimal("100"),
        commission=Decimal("1"),
        slippage=Decimal("0.25"),
        fill_time=start,
    )
    builder.on_fill(
        order_id="ord-2",
        instrument_id="EQUITY.US.NASDAQ.AAPL",
        side="sell",
        quantity=Decimal("1"),
        price=Decimal("110"),
        commission=Decimal("1"),
        slippage=Decimal("0.25"),
        fill_time=start + timedelta(minutes=2),
    )

    payload = builder.finalize(trading_bars=4, bars_per_year=Decimal("98280")).to_payload()

    expected_keys = {
        "points",
        "annualization_factor",
        "total_return",
        "compounding_annual_return",
        "volatility_annual",
        "max_drawdown",
        "max_drawdown_duration_bars",
        "calmar_ratio",
        "sharpe_ratio",
        "sortino_ratio",
        "probabilistic_sharpe_ratio",
        "total_trades",
        "total_orders",
        "win_rate",
        "loss_rate",
        "avg_win",
        "avg_loss",
        "largest_win",
        "largest_loss",
        "profit_factor",
        "expectancy",
        "avg_holding_period_bars",
        "time_in_market",
        "avg_gross_exposure",
        "avg_net_exposure",
        "total_commission",
        "total_slippage",
        "commission_per_trade",
        "slippage_per_trade",
    }
    assert expected_keys <= payload.keys()
    assert "alpha_annual" not in payload
    assert "beta" not in payload
    assert payload["total_orders"] == 2
    assert payload["total_trades"] == 1
