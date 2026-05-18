"""Anchor: annualization_factor reflects bars-per-trading-year, not bars × 252.

Domain fact: Sharpe / Sortino / Calmar / volatility annual all
multiply by ``sqrt(bars_per_year)`` to scale per-bar returns to a
yearly horizon. For an N-minute bar series with ``B`` bars per
trading day and ``D=252`` trading days per year, the correct
``bars_per_year`` is ``B × D``. The 2.25-year VWAP run surfaced a
defect: the caller passed ``bars_per_year = 252 × total_trading_bars``,
which for 805k bars produced ~2×10⁸ — inflating ``sqrt(bars_per_year)``
by ~25× and making every risk-adjusted ratio meaningless.

Owner: ``qts.reporting.statistics.StatisticsBuilder.finalize`` (auto-
derives when ``bars_per_year`` is not explicitly given) +
``qts.reporting.backtest.BacktestArtifactWriter.finalize`` (the broken
caller).

Forbidden shortcut: hard-coding 252 for non-daily bar series;
multiplying 252 by total bar count; deriving the factor from a
config knob that doesn't actually reflect the observed session
length.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.reporting.statistics import StatisticsBuilder


def test_default_annualization_uses_observed_bars_per_day() -> None:
    """5 minutes of bars over 5 distinct calendar days → 1 bar/day × 252."""
    builder = StatisticsBuilder()
    base = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    equities = [Decimal("100"), Decimal("101"), Decimal("99"), Decimal("102"), Decimal("100")]
    for index, equity in enumerate(equities):
        builder.on_equity_point(time=base + timedelta(days=index), equity=equity)

    payload = builder.finalize(trading_bars=len(equities)).to_payload()

    assert payload["annualization_factor"] == Decimal("252")


def test_default_annualization_uses_observed_bars_per_day_minute_series() -> None:
    """1380 minutes (one GC session) → 1380 bars/day × 252 = 347760."""
    builder = StatisticsBuilder()
    base = datetime(2024, 1, 2, 0, 0, tzinfo=UTC)
    for index in range(1380):
        # Slight drift to avoid stddev=0 (would short-circuit Sharpe).
        equity = Decimal("100") + Decimal(index) / Decimal("10000")
        builder.on_equity_point(time=base + timedelta(minutes=index), equity=equity)

    payload = builder.finalize(trading_bars=1380).to_payload()

    assert payload["annualization_factor"] == Decimal("347760")


def test_explicit_bars_per_year_override_still_wins() -> None:
    """Explicit bars_per_year stays the override knob (backward compat)."""
    builder = StatisticsBuilder()
    base = datetime(2024, 1, 2, 14, 30, tzinfo=UTC)
    for index in range(10):
        builder.on_equity_point(
            time=base + timedelta(days=index),
            equity=Decimal("100") + Decimal(index),
        )

    payload = builder.finalize(trading_bars=10, bars_per_year=Decimal("252")).to_payload()

    assert payload["annualization_factor"] == Decimal("252")


def test_default_annualization_does_not_grow_with_run_length() -> None:
    """Same bars-per-day must give same annualization regardless of run length.

    The 2.25y VWAP bug grew annualization_factor linearly with total
    bars because the formula was 252 × bars. After the fix, a 1-day
    and a 100-day run with identical bars/day must produce the same
    annualization_factor.
    """
    base = datetime(2024, 1, 2, 0, 0, tzinfo=UTC)

    def _build(num_days: int) -> Decimal:
        builder = StatisticsBuilder()
        total = 0
        for day in range(num_days):
            for minute in range(60):
                equity = Decimal("100") + Decimal(total) / Decimal("100000")
                builder.on_equity_point(
                    time=base + timedelta(days=day, minutes=minute),
                    equity=equity,
                )
                total += 1
        return Decimal(builder.finalize(trading_bars=total).to_payload()["annualization_factor"])

    short = _build(1)
    long = _build(20)
    assert short == long, f"annualization drifted: 1d={short}, 20d={long}"
