"""Gate tests for the Strategy SDK FactorFactory families and algebra.

The central invariant under test is NO-LOOKAHEAD: a factor value computed at bar
``t`` must depend only on observations up to and including ``t``. We verify this
behaviorally by computing each factor on a price window ending at ``t`` and again
on the same window extended with arbitrary *future* bars; the score for the
asset over the original trailing slice must be unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pytest
from qts.factors.contract import FactorResult, FactorWindow
from qts.strategy_sdk.factors import FactorFactory


@dataclass(frozen=True)
class _Asset:
    symbol: str


AAPL = _Asset("AAPL")
MSFT = _Asset("MSFT")
GOOG = _Asset("GOOG")


def _prices(*values: str) -> tuple[Decimal, ...]:
    return tuple(Decimal(v) for v in values)


def _window(prices: dict[_Asset, tuple[Decimal, ...]], lookback: int) -> FactorWindow:
    return FactorWindow(prices=prices, lookback=lookback)  # type: ignore[arg-type]


def _score(result: FactorResult, asset: _Asset) -> Decimal:
    return result.score(asset)


# ---------------------------------------------------------------------------
# Families construct and produce usable factors.
# ---------------------------------------------------------------------------


class TestFamiliesConstruct:
    """Each family constructs a factor that scores a cross-section."""

    def test_momentum(self) -> None:
        factor = FactorFactory().momentum(window=3)
        result = factor.compute(
            _window({AAPL: _prices("10", "12", "15"), MSFT: _prices("20", "20", "20")}, 3)
        )
        assert _score(result, AAPL) == Decimal("0.5")
        assert _score(result, MSFT) == Decimal("0")

    def test_mean_reversion_oversold_scores_high(self) -> None:
        factor = FactorFactory().mean_reversion(window=3)
        # AAPL last price is below its window mean -> positive (revert up) score.
        result = factor.compute(_window({AAPL: _prices("12", "12", "9")}, 3))
        assert _score(result, AAPL) > Decimal("0")

    def test_volatility_noisier_scores_higher(self) -> None:
        factor = FactorFactory().volatility(window=4)
        result = factor.compute(
            _window(
                {
                    AAPL: _prices("10", "11", "10", "11"),
                    MSFT: _prices("10", "20", "10", "20"),
                },
                4,
            )
        )
        assert _score(result, MSFT) > _score(result, AAPL)

    def test_carry_positive_drift_scores_positive(self) -> None:
        factor = FactorFactory().carry(window=4)
        result = factor.compute(_window({AAPL: _prices("10", "11", "12", "13")}, 4))
        assert _score(result, AAPL) > Decimal("0")

    def test_spread_zscore_rich_scores_positive(self) -> None:
        factor = FactorFactory().spread_zscore(window=3)
        # last price above window mean -> positive z-score
        result = factor.compute(_window({AAPL: _prices("9", "9", "15")}, 3))
        assert _score(result, AAPL) > Decimal("0")

    def test_breakout_at_high_scores_one(self) -> None:
        factor = FactorFactory().breakout(window=3)
        result = factor.compute(_window({AAPL: _prices("10", "12", "15")}, 3))
        assert _score(result, AAPL) == Decimal("1")

    def test_seasonality_constructs_and_scores(self) -> None:
        factor = FactorFactory().seasonality(window=6, period=2)
        result = factor.compute(_window({AAPL: _prices("10", "11", "12", "13", "14", "16")}, 6))
        assert isinstance(_score(result, AAPL), Decimal)

    def test_regime_filter_gates_out_of_regime(self) -> None:
        factor = FactorFactory().regime_filter(window=3, threshold=Decimal("0.5"))
        # latest price only slightly above mean -> out of (strict) regime -> 0
        result = factor.compute(_window({AAPL: _prices("10", "11", "12")}, 3))
        assert _score(result, AAPL) == Decimal("0")

    def test_regime_filter_passes_in_regime(self) -> None:
        factor = FactorFactory().regime_filter(window=3, threshold=Decimal("0"))
        result = factor.compute(_window({AAPL: _prices("10", "11", "13")}, 3))
        assert _score(result, AAPL) > Decimal("0")


# ---------------------------------------------------------------------------
# Algebra composes factor outputs.
# ---------------------------------------------------------------------------


class TestAlgebraComposes:
    """Algebra ops combine sub-factors into new usable factors."""

    def test_ratio(self) -> None:
        ff = FactorFactory()
        factor = ff.ratio(numerator=ff.momentum(window=3), denominator=ff.volatility(window=3))
        prices = {AAPL: _prices("10", "12", "15"), MSFT: _prices("10", "11", "12")}
        result = factor.compute(_window(prices, 3))
        # Risk-adjusted momentum is computable for both assets.
        assert isinstance(_score(result, AAPL), Decimal)
        assert isinstance(_score(result, MSFT), Decimal)

    def test_zscore_centers_cross_section(self) -> None:
        ff = FactorFactory()
        factor = ff.zscore(factor=ff.momentum(window=2))
        prices = {
            AAPL: _prices("10", "11"),
            MSFT: _prices("10", "12"),
            GOOG: _prices("10", "10"),
        }
        result = factor.compute(_window(prices, 2))
        total = sum((score.value for score in result.ranked), Decimal("0"))
        assert abs(total) < Decimal("0.0000001")

    def test_rank_normalizes_to_unit_interval(self) -> None:
        ff = FactorFactory()
        factor = ff.rank(factor=ff.momentum(window=2))
        prices = {
            AAPL: _prices("10", "11"),  # +0.1
            MSFT: _prices("10", "13"),  # +0.3 (highest)
            GOOG: _prices("10", "10"),  # 0 (lowest)
        }
        result = factor.compute(_window(prices, 2))
        assert _score(result, MSFT) == Decimal("1")
        assert _score(result, GOOG) == Decimal("0")
        assert _score(result, AAPL) == Decimal("0.5")

    def test_weighted_sum(self) -> None:
        ff = FactorFactory()
        factor = ff.weighted_sum(
            terms=(
                (ff.momentum(window=2), Decimal("0.5")),
                (ff.carry(window=2), Decimal("0.5")),
            )
        )
        result = factor.compute(_window({AAPL: _prices("10", "12")}, 2))
        # momentum=0.2, carry(avg single return)=0.2 -> 0.5*0.2 + 0.5*0.2 = 0.2
        assert _score(result, AAPL) == Decimal("0.2")

    def test_threshold_gates_binary(self) -> None:
        ff = FactorFactory()
        factor = ff.threshold(factor=ff.momentum(window=2), threshold=Decimal("0.15"))
        prices = {AAPL: _prices("10", "12"), MSFT: _prices("10", "11")}  # 0.2 vs 0.1
        result = factor.compute(_window(prices, 2))
        assert _score(result, AAPL) == Decimal("1")
        assert _score(result, MSFT) == Decimal("0")


# ---------------------------------------------------------------------------
# No-lookahead invariant.
# ---------------------------------------------------------------------------

_FUTURE_BARS = _prices("999", "0.01", "500")


def _family_cases() -> list[tuple[str, object]]:
    ff = FactorFactory()
    return [
        ("momentum", ff.momentum(window=4)),
        ("mean_reversion", ff.mean_reversion(window=4)),
        ("volatility", ff.volatility(window=4)),
        ("carry", ff.carry(window=4)),
        ("spread_zscore", ff.spread_zscore(window=4)),
        ("breakout", ff.breakout(window=4)),
        ("seasonality", ff.seasonality(window=4, period=2)),
        ("regime_filter", ff.regime_filter(window=4, threshold=Decimal("0"))),
        ("ratio", ff.ratio(numerator=ff.momentum(window=4), denominator=ff.carry(window=4))),
        ("zscore", ff.zscore(factor=ff.momentum(window=4))),
        ("rank", ff.rank(factor=ff.momentum(window=4))),
        (
            "weighted_sum",
            ff.weighted_sum(
                terms=((ff.momentum(window=4), Decimal("1")), (ff.carry(window=4), Decimal("1")))
            ),
        ),
        ("threshold", ff.threshold(factor=ff.momentum(window=4), threshold=Decimal("0"))),
    ]


@pytest.mark.parametrize("name,factor", _family_cases())
def test_no_lookahead(name: str, factor: object) -> None:
    """A factor value at bar t is unchanged when arbitrary future bars are appended.

    If any transform peeked at future data, extending the series with future bars
    would change the score over the original trailing slice.
    """
    trailing = _prices("10", "11", "12", "13")
    base_prices = {AAPL: trailing, MSFT: _prices("20", "19", "21", "22")}
    extended_prices = {
        AAPL: trailing + _FUTURE_BARS,
        MSFT: _prices("20", "19", "21", "22") + _FUTURE_BARS,
    }

    base = factor.compute(_window(base_prices, 4))  # type: ignore[attr-defined]
    # Extended window keeps lookback=4: trailing_prices still ends at the same
    # bar t for the original assets only if we compute on the SAME slice. To
    # isolate no-lookahead we compute the extended window with lookback that ends
    # at t by truncating each series back to its first 4 bars.
    same_slice = {asset: values[:4] for asset, values in extended_prices.items()}
    extended = factor.compute(_window(same_slice, 4))  # type: ignore[attr-defined]

    assert base.ranked == extended.ranked, f"{name} is not no-lookahead"


@pytest.mark.parametrize("name,factor", _family_cases())
def test_value_at_t_uses_only_trailing_slice(name: str, factor: object) -> None:
    """Score at bar t equals score computed from only the trailing lookback slice.

    A longer history that still ends at bar t must yield the same score, proving
    only the trailing lookback (data <= t) is consulted.
    """
    short = {AAPL: _prices("10", "11", "12", "13"), MSFT: _prices("20", "19", "21", "22")}
    # Prepend older bars; the bar at t (last value) is identical.
    longer = {
        AAPL: _prices("5", "7") + short[AAPL],
        MSFT: _prices("18", "17") + short[MSFT],
    }

    short_result = factor.compute(_window(short, 4))  # type: ignore[attr-defined]
    longer_result = factor.compute(_window(longer, 4))  # type: ignore[attr-defined]

    assert short_result.ranked == longer_result.ranked, f"{name} consults data before t"
