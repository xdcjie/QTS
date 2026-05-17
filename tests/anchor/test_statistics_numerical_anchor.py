"""Anchor: every shipped statistic is computed from real data, not a sentinel.

Domain fact: PSR, alpha, beta, information ratio, tracking error are
computed from a closed-form formula over the returns / benchmark series.
``time_in_market`` is the fraction of bars during which any trade was open.
Exposure metrics are absent unless the caller fed ``on_holdings_snapshot``.

Owner: ``qts.reporting.statistics.StatisticsBuilder``.

Forbidden shortcut: ``Decimal("0.5")``/``Decimal("1")`` for PSR,
``Decimal("0")`` for alpha/beta/IR, ``total_trades / trading_bars`` for
``time_in_market``.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.reporting.statistics import StatisticsBuilder


def _phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


_EQUITY: tuple[Decimal, ...] = (
    Decimal("100"),
    Decimal("102"),
    Decimal("101"),
    Decimal("103"),
    Decimal("105"),
)
_BENCH_RETURNS: tuple[Decimal, ...] = (
    Decimal("0.01"),
    Decimal("0.005"),
    Decimal("0.015"),
    Decimal("0.02"),
)


def _expected_returns() -> list[float]:
    return [float((_EQUITY[i + 1] - _EQUITY[i]) / _EQUITY[i]) for i in range(len(_EQUITY) - 1)]


def _populate(builder: StatisticsBuilder) -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    for index, equity in enumerate(_EQUITY):
        builder.on_equity_point(time=start + timedelta(minutes=index), equity=equity)


def test_probabilistic_sharpe_ratio_matches_lopez_de_prado_formula() -> None:
    builder = StatisticsBuilder()
    _populate(builder)

    payload = builder.finalize(trading_bars=4, bars_per_year=Decimal("252")).to_payload()

    returns = _expected_returns()
    n = len(returns)
    mean = sum(returns) / n
    variance = sum((r - mean) ** 2 for r in returns) / (n - 1)
    std = math.sqrt(variance)
    sharpe = mean / std
    skew = sum(((r - mean) / std) ** 3 for r in returns) / n
    kurt = sum(((r - mean) / std) ** 4 for r in returns) / n
    sigma_sharpe = math.sqrt((1.0 - skew * sharpe + (kurt - 1.0) / 4.0 * sharpe**2) / (n - 1))
    expected_psr = _phi(sharpe / sigma_sharpe)

    actual = float(payload["probabilistic_sharpe_ratio"])
    assert actual == pytest.approx(expected_psr, rel=1e-6)
    assert actual not in (0.5, 1.0)  # placeholder sentinels are gone


def test_alpha_beta_information_ratio_match_ols_regression() -> None:
    builder = StatisticsBuilder()
    _populate(builder)

    payload = builder.finalize(
        trading_bars=4,
        bars_per_year=Decimal("252"),
        benchmark_returns=_BENCH_RETURNS,
    ).to_payload()

    returns = _expected_returns()
    bench = [float(b) for b in _BENCH_RETURNS]
    n = len(returns)
    mean_r = sum(returns) / n
    mean_b = sum(bench) / n
    cov = sum((returns[i] - mean_r) * (bench[i] - mean_b) for i in range(n)) / (n - 1)
    var_b = sum((b - mean_b) ** 2 for b in bench) / (n - 1)
    beta = cov / var_b
    alpha_per_period = mean_r - beta * mean_b
    diffs = [returns[i] - bench[i] for i in range(n)]
    mean_diff = sum(diffs) / n
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    te_period = math.sqrt(var_diff)
    annualization = 252.0

    assert float(payload["beta"]) == pytest.approx(beta, rel=1e-6)
    assert float(payload["alpha_annual"]) == pytest.approx(
        alpha_per_period * annualization, rel=1e-6
    )
    assert float(payload["tracking_error_annual"]) == pytest.approx(
        te_period * math.sqrt(annualization), rel=1e-6
    )
    assert float(payload["information_ratio"]) == pytest.approx(
        (mean_diff / te_period) * math.sqrt(annualization), rel=1e-6
    )


def test_time_in_market_counts_bars_with_open_position() -> None:
    builder = StatisticsBuilder()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    # 6 equity points; open between bar 1 and bar 3 inclusive → 3 occupied bars / 6 bars
    for index, equity in enumerate(
        (
            Decimal("100"),
            Decimal("101"),
            Decimal("102"),
            Decimal("100"),
            Decimal("101"),
            Decimal("103"),
        )
    ):
        builder.on_equity_point(time=start + timedelta(minutes=index), equity=equity)
        if index == 1:
            builder.on_fill(
                order_id="o-1",
                instrument_id="AAPL",
                side="buy",
                quantity=Decimal("1"),
                price=Decimal("100"),
                commission=Decimal("0"),
                slippage=Decimal("0"),
                fill_time=start + timedelta(minutes=index),
            )
        if index == 3:
            builder.on_fill(
                order_id="o-2",
                instrument_id="AAPL",
                side="sell",
                quantity=Decimal("1"),
                price=Decimal("100"),
                commission=Decimal("0"),
                slippage=Decimal("0"),
                fill_time=start + timedelta(minutes=index),
            )

    payload = builder.finalize(trading_bars=6, bars_per_year=Decimal("252")).to_payload()

    # Open at bar index 1, closed at bar index 3, so bars 2,3 had open position.
    # Definition: count bars where any open trade existed at the start of the
    # bar; that's bars 2 and 3 → 2 / 6 ≈ 0.333.
    assert float(payload["time_in_market"]) == pytest.approx(2.0 / 6.0, abs=1e-6)


def test_exposure_metrics_absent_until_snapshots_fed() -> None:
    builder = StatisticsBuilder()
    _populate(builder)
    payload = builder.finalize(trading_bars=4, bars_per_year=Decimal("252")).to_payload()

    # Until on_holdings_snapshot is wired and called, exposure metrics must be
    # absent rather than fabricated as zero.
    assert "avg_gross_exposure" not in payload
    assert "avg_net_exposure" not in payload


def test_exposure_metrics_present_when_snapshots_supplied() -> None:
    builder = StatisticsBuilder()
    _populate(builder)
    # Per-bar gross/net notional snapshots paired with equity from _EQUITY.
    builder.on_holdings_snapshot(gross_notional=Decimal("0"), net_notional=Decimal("0"))
    builder.on_holdings_snapshot(gross_notional=Decimal("100"), net_notional=Decimal("100"))
    builder.on_holdings_snapshot(gross_notional=Decimal("100"), net_notional=Decimal("100"))
    builder.on_holdings_snapshot(gross_notional=Decimal("0"), net_notional=Decimal("0"))
    builder.on_holdings_snapshot(gross_notional=Decimal("0"), net_notional=Decimal("0"))

    payload = builder.finalize(trading_bars=4, bars_per_year=Decimal("252")).to_payload()

    # Equity at corresponding bars is [100,102,101,103,105].
    # Gross fractions: 0, 100/102, 100/101, 0, 0
    # avg = (0 + 100/102 + 100/101 + 0 + 0) / 5 ≈ 0.39604
    expected_gross = (0.0 + 100.0 / 102.0 + 100.0 / 101.0 + 0.0 + 0.0) / 5.0
    assert float(payload["avg_gross_exposure"]) == pytest.approx(expected_gross, rel=1e-6)
    assert float(payload["avg_net_exposure"]) == pytest.approx(expected_gross, rel=1e-6)
