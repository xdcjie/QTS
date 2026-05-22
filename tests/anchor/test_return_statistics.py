from __future__ import annotations

from decimal import Decimal


def test_compound_return_multiplies_period_returns() -> None:
    from qts.domain.return_statistics import compound_return

    assert compound_return((Decimal("0.02"), Decimal("0.03"), Decimal("-0.01"))) == Decimal(
        "0.040094"
    )


def test_compound_return_handles_empty_series_as_flat_return() -> None:
    from qts.domain.return_statistics import compound_return

    assert compound_return(()) == Decimal("0")


def test_realized_volatility_uses_population_variance() -> None:
    from qts.domain.return_statistics import realized_volatility

    returns = (Decimal("0.01"), Decimal("-0.01"))
    assert realized_volatility(returns).quantize(Decimal("0.00000001")) == Decimal("0.01000000")


def test_realized_volatility_is_zero_for_short_series() -> None:
    from qts.domain.return_statistics import realized_volatility

    assert realized_volatility((Decimal("0.02"),)) == Decimal("0")


def test_mean_return_handles_empty_series() -> None:
    from qts.domain.return_statistics import mean_return

    assert mean_return(()) == Decimal("0")
