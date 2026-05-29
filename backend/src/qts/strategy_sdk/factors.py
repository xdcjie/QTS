"""Strategy-facing factor factory."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.factors.algebra import (
    RankFactor,
    RatioFactor,
    ThresholdFactor,
    WeightedSumFactor,
    ZScoreFactor,
)
from qts.factors.contract import Factor
from qts.factors.momentum import MomentumFactor
from qts.factors.statistical import (
    BreakoutFactor,
    CarryFactor,
    MeanReversionFactor,
    RegimeFilterFactor,
    SeasonalityFactor,
    SpreadZScoreFactor,
    VolatilityFactor,
)


@dataclass(frozen=True, slots=True)
class FactorFactory:
    """Factory for user-created factors and factor algebra.

    Every factor produced here scores assets from trailing price windows ending
    at the current bar, so all factors are no-lookahead by construction.
    """

    # --- Factor families -------------------------------------------------

    def momentum(self, *, window: int) -> MomentumFactor:
        """Create a trailing-momentum factor (window return)."""
        return MomentumFactor(window=window)

    def mean_reversion(self, *, window: int) -> MeanReversionFactor:
        """Create a mean-reversion factor (negative trailing z-score)."""
        return MeanReversionFactor(window=window)

    def volatility(self, *, window: int) -> VolatilityFactor:
        """Create a realized-volatility factor over trailing returns."""
        return VolatilityFactor(window=window)

    def carry(self, *, window: int) -> CarryFactor:
        """Create a carry factor (average trailing per-bar return)."""
        return CarryFactor(window=window)

    def spread_zscore(self, *, window: int) -> SpreadZScoreFactor:
        """Create a signed spread z-score factor over the trailing window."""
        return SpreadZScoreFactor(window=window)

    def breakout(self, *, window: int) -> BreakoutFactor:
        """Create a breakout factor (position in trailing high-low channel)."""
        return BreakoutFactor(window=window)

    def seasonality(self, *, window: int, period: int) -> SeasonalityFactor:
        """Create a seasonality factor over the current bar's seasonal phase."""
        return SeasonalityFactor(window=window, period=period)

    def regime_filter(
        self, *, window: int, threshold: Decimal = Decimal("0")
    ) -> RegimeFilterFactor:
        """Create a regime-gated momentum factor."""
        return RegimeFilterFactor(window=window, threshold=Decimal(str(threshold)))

    # --- Factor algebra --------------------------------------------------

    def ratio(self, *, numerator: Factor, denominator: Factor) -> RatioFactor:
        """Compose two factors into a per-asset ratio."""
        return RatioFactor(numerator=numerator, denominator=denominator)

    def zscore(self, *, factor: Factor) -> ZScoreFactor:
        """Compose a factor into its cross-sectional z-score."""
        return ZScoreFactor(factor=factor)

    def rank(self, *, factor: Factor) -> RankFactor:
        """Compose a factor into its normalized cross-sectional rank."""
        return RankFactor(factor=factor)

    def weighted_sum(self, *, terms: tuple[tuple[Factor, Decimal], ...]) -> WeightedSumFactor:
        """Compose several factors into a weighted sum over shared assets."""
        normalized = tuple((factor, Decimal(str(weight))) for factor, weight in terms)
        return WeightedSumFactor(terms=normalized)

    def threshold(self, *, factor: Factor, threshold: Decimal) -> ThresholdFactor:
        """Compose a factor into a binary threshold gate."""
        return ThresholdFactor(factor=factor, threshold=Decimal(str(threshold)))


__all__ = ["FactorFactory"]
