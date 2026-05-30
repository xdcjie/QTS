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
        "total_commission",
        "total_slippage",
        "commission_per_trade",
        "slippage_per_trade",
        "observed_sharpe",
        "return_observation_count",
        "return_skewness",
        "return_kurtosis",
    }
    assert expected_keys <= payload.keys()
    assert "alpha_annual" not in payload
    assert "beta" not in payload
    assert "avg_gross_exposure" not in payload
    assert "avg_net_exposure" not in payload
    assert payload["total_orders"] == 2
    # Trades are sourced from on_position_close (i.e. account.position_closed
    # runtime events), not derived from fill streams; this fixture only feeds
    # fills, so total_trades is zero.
    assert payload["total_trades"] == 0


def test_statistics_builder_emits_per_observation_moments_for_multiplicity() -> None:
    # The deflated-Sharpe / multiple-testing correction consumes the
    # per-observation (non-annualized) Sharpe, the return count, and the
    # higher moments of the per-period return series.
    from qts.reporting.statistics import StatisticsBuilder

    builder = StatisticsBuilder()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    equities = (Decimal("100000"), Decimal("101000"), Decimal("100500"), Decimal("102000"))
    for index, equity in enumerate(equities):
        builder.on_equity_point(time=start + timedelta(minutes=index), equity=equity)

    payload = builder.finalize(trading_bars=4, bars_per_year=Decimal("98280")).to_payload()

    # Three returns from four equity points.
    assert payload["return_observation_count"] == 3
    # observed_sharpe is the non-annualized mean/std; the annualized sharpe_ratio
    # is observed_sharpe * sqrt(annualization), so they differ in scale.
    assert payload["observed_sharpe"] != payload["sharpe_ratio"]
    assert Decimal("0") <= payload["return_kurtosis"]
    # Skewness/kurtosis are finite Decimals (defaults 0/3 only on degenerate input).
    assert payload["return_skewness"] is not None
