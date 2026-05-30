"""Cross-sectional factor families computed from trailing price windows.

Every factor in this module derives a per-asset scalar score from
``FactorWindow.trailing_prices`` only. That slice contains the last ``lookback``
observations ending at the current bar, so all scores are no-lookahead by
construction: nothing in this module can reference a price beyond the current
bar.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import qts.factors.contract as factor_contract


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    """Return the arithmetic mean of a non-empty value tuple."""
    return sum(values, Decimal("0")) / Decimal(len(values))


def _population_std(values: tuple[Decimal, ...]) -> Decimal:
    """Return the population standard deviation of a non-empty value tuple."""
    mean = _mean(values)
    variance = sum(((item - mean) * (item - mean) for item in values), Decimal("0")) / Decimal(
        len(values)
    )
    return variance.sqrt()


def _simple_returns(values: tuple[Decimal, ...]) -> tuple[Decimal, ...]:
    """Return period-over-period simple returns, skipping zero-price denominators."""
    returns: list[Decimal] = []
    for previous, current in itertools.pairwise(values):
        if previous == Decimal("0"):
            raise ValueError("price must not be zero when computing returns")
        returns.append(current / previous - Decimal("1"))
    return tuple(returns)


def _rank_scores(
    window: factor_contract.FactorWindow,
    score_fn: Callable[[tuple[Decimal, ...]], Decimal],
    required: int,
) -> factor_contract.FactorResult:
    """Build a ranked FactorResult from a per-asset trailing-window score function."""
    if window.lookback < required:
        raise ValueError("factor window lookback is shorter than required lookback")
    scores: list[factor_contract.FactorScore] = []
    for asset in window.assets():
        values = window.trailing_prices(asset)
        if values is None:
            continue
        scores.append(factor_contract.FactorScore(asset=asset, value=score_fn(values)))
    ranked = tuple(sorted(scores, key=lambda score: (-score.value, score.asset.symbol)))
    return factor_contract.FactorResult(ranked=ranked)


@dataclass(frozen=True, slots=True)
class MeanReversionFactor:
    """Negative z-score of the last price within its trailing window.

    A high score means the latest price is far *below* its trailing mean, i.e.
    an oversold asset expected to revert upward.
    """

    window: int
    name: ClassVar[str] = "mean_reversion"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate mean-reversion configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked mean-reversion scores over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    @staticmethod
    def _score(values: tuple[Decimal, ...]) -> Decimal:
        mean = _mean(values)
        std = _population_std(values)
        if std == Decimal("0"):
            return Decimal("0")
        return (mean - values[-1]) / std


@dataclass(frozen=True, slots=True)
class VolatilityFactor:
    """Trailing realized volatility of simple returns.

    Higher score means a noisier asset over the trailing window.
    """

    window: int
    name: ClassVar[str] = "volatility"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate volatility configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked realized-volatility scores over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    @staticmethod
    def _score(values: tuple[Decimal, ...]) -> Decimal:
        returns = _simple_returns(values)
        if len(returns) < 2:
            return Decimal("0")
        return _population_std(returns)


@dataclass(frozen=True, slots=True)
class CarryFactor:
    """Annualized average trailing simple return as a carry proxy.

    Carry uses the same input series as momentum but expresses the per-bar
    average return rather than the cumulative window return, so it is robust to
    window length when comparing across factors.
    """

    window: int
    name: ClassVar[str] = "carry"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate carry configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked carry scores over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    @staticmethod
    def _score(values: tuple[Decimal, ...]) -> Decimal:
        returns = _simple_returns(values)
        return _mean(returns)


@dataclass(frozen=True, slots=True)
class SpreadZScoreFactor:
    """Z-score of the latest price relative to its trailing distribution.

    Unlike :class:`MeanReversionFactor`, the sign is preserved: a high positive
    score means the latest price is far *above* its trailing mean (rich), which
    is the canonical mean/spread-reversion divergence signal.
    """

    window: int
    name: ClassVar[str] = "spread_zscore"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate spread z-score configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked spread z-score values over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    @staticmethod
    def _score(values: tuple[Decimal, ...]) -> Decimal:
        mean = _mean(values)
        std = _population_std(values)
        if std == Decimal("0"):
            return Decimal("0")
        return (values[-1] - mean) / std


@dataclass(frozen=True, slots=True)
class BreakoutFactor:
    """Position of the latest price within its trailing high-low channel.

    Score 1 means the latest price equals the trailing maximum (upside
    breakout); 0 means it equals the trailing minimum. A flat channel scores 0.
    """

    window: int
    name: ClassVar[str] = "breakout"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate breakout configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked breakout scores over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    @staticmethod
    def _score(values: tuple[Decimal, ...]) -> Decimal:
        highest = max(values)
        lowest = min(values)
        channel = highest - lowest
        if channel == Decimal("0"):
            return Decimal("0")
        return (values[-1] - lowest) / channel


@dataclass(frozen=True, slots=True)
class SeasonalityFactor:
    """Average trailing return of the bars sharing the current bar's phase.

    The trailing window is bucketed by position modulo ``period`` (a calendar
    phase such as day-of-week or month-of-year mapped onto the bar cadence). The
    score is the average return of the bucket that the most recent bar belongs
    to, capturing a recurring seasonal tendency without looking forward.
    """

    window: int
    period: int
    name: ClassVar[str] = "seasonality"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate seasonality configuration."""
        if self.period <= 1:
            raise ValueError("period must be greater than 1")
        if self.window <= self.period:
            raise ValueError("window must be greater than period")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked seasonality scores over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    def _score(self, values: tuple[Decimal, ...]) -> Decimal:
        returns = _simple_returns(values)
        if not returns:
            return Decimal("0")
        # Phase of the most recent return within the seasonal period.
        current_phase = (len(returns) - 1) % self.period
        bucket = [ret for index, ret in enumerate(returns) if index % self.period == current_phase]
        if not bucket:
            return Decimal("0")
        return _mean(tuple(bucket))


@dataclass(frozen=True, slots=True)
class RegimeFilterFactor:
    """Gate the trailing momentum by a trend regime above/below a threshold.

    The latest price's distance from its trailing mean (as a fraction of the
    mean) is compared to ``threshold``. When the asset is in-regime the score is
    its trailing momentum; otherwise the score is 0, removing out-of-regime
    assets from the cross-section.
    """

    window: int
    threshold: Decimal = Decimal("0")
    name: ClassVar[str] = "regime_filter"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate regime-filter configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")
        object.__setattr__(self, "threshold", Decimal(str(self.threshold)))
        if not self.threshold.is_finite():
            raise ValueError("threshold must be finite")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked regime-gated momentum scores over the provided factor window."""
        return _rank_scores(window, self._score, self.window)

    def _score(self, values: tuple[Decimal, ...]) -> Decimal:
        first = values[0]
        if first == Decimal("0"):
            raise ValueError("first price must not be zero")
        momentum = values[-1] / first - Decimal("1")
        mean = _mean(values)
        if mean == Decimal("0"):
            return Decimal("0")
        regime = (values[-1] - mean) / mean
        if regime >= self.threshold:
            return momentum
        return Decimal("0")


__all__ = [
    "BreakoutFactor",
    "CarryFactor",
    "MeanReversionFactor",
    "RegimeFilterFactor",
    "SeasonalityFactor",
    "SpreadZScoreFactor",
    "VolatilityFactor",
]
