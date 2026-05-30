"""Factor algebra combinators.

Each combinator wraps one or more sub-factors and derives a new cross-sectional
:class:`FactorResult` from their outputs. Because every sub-factor is computed
from a trailing window ending at the current bar, every combinator is
no-lookahead by construction: composition cannot introduce a forward reference.

Combinators only score assets present in *all* of their operands' results, so
the output cross-section is the intersection of the inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import qts.factors.contract as factor_contract


def _common_assets(
    results: tuple[factor_contract.FactorResult, ...],
) -> tuple[factor_contract.FactorAsset, ...]:
    """Return assets present in every result, ordered by symbol for determinism."""
    if not results:
        return ()
    common = set(score.asset for score in results[0].ranked)
    for result in results[1:]:
        common &= set(score.asset for score in result.ranked)
    return tuple(sorted(common, key=lambda asset: asset.symbol))


def _ranked(
    scores: list[factor_contract.FactorScore],
) -> factor_contract.FactorResult:
    """Return a FactorResult with deterministic descending-score ordering."""
    ranked = tuple(sorted(scores, key=lambda score: (-score.value, score.asset.symbol)))
    return factor_contract.FactorResult(ranked=ranked)


@dataclass(frozen=True, slots=True)
class RatioFactor:
    """Per-asset ratio of a numerator factor over a denominator factor."""

    numerator: factor_contract.Factor
    denominator: factor_contract.Factor
    name: ClassVar[str] = "ratio"
    version: ClassVar[str] = "1"

    @property
    def lookback(self) -> int:
        """Return the maximum trailing observation count of the operands."""
        return max(_factor_lookback(self.numerator), _factor_lookback(self.denominator))

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked numerator/denominator ratios over shared assets."""
        num = self.numerator.compute(window)
        den = self.denominator.compute(window)
        scores: list[factor_contract.FactorScore] = []
        for asset in _common_assets((num, den)):
            denominator = den.score(asset)
            if denominator == Decimal("0"):
                continue
            scores.append(
                factor_contract.FactorScore(asset=asset, value=num.score(asset) / denominator)
            )
        return _ranked(scores)


@dataclass(frozen=True, slots=True)
class ZScoreFactor:
    """Cross-sectional z-score of a sub-factor across the current universe."""

    factor: factor_contract.Factor
    name: ClassVar[str] = "zscore"
    version: ClassVar[str] = "1"

    @property
    def lookback(self) -> int:
        """Return the trailing observation count of the wrapped factor."""
        return _factor_lookback(self.factor)

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute the cross-sectional z-score of the wrapped factor."""
        result = self.factor.compute(window)
        values = tuple(score.value for score in result.ranked)
        if not values:
            return factor_contract.FactorResult(ranked=())
        mean = sum(values, Decimal("0")) / Decimal(len(values))
        variance = sum(((v - mean) * (v - mean) for v in values), Decimal("0")) / Decimal(
            len(values)
        )
        std = variance.sqrt()
        scores: list[factor_contract.FactorScore] = []
        for score in result.ranked:
            value = Decimal("0") if std == Decimal("0") else (score.value - mean) / std
            scores.append(factor_contract.FactorScore(asset=score.asset, value=value))
        return _ranked(scores)


@dataclass(frozen=True, slots=True)
class RankFactor:
    """Cross-sectional rank of a sub-factor in [0, 1].

    The lowest sub-factor value maps to 0 and the highest to 1. A single-asset
    cross-section scores 0.5 (neutral).
    """

    factor: factor_contract.Factor
    name: ClassVar[str] = "rank"
    version: ClassVar[str] = "1"

    @property
    def lookback(self) -> int:
        """Return the trailing observation count of the wrapped factor."""
        return _factor_lookback(self.factor)

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute the normalized cross-sectional rank of the wrapped factor."""
        result = self.factor.compute(window)
        # Ascending order so the smallest value gets rank 0.
        ascending = sorted(result.ranked, key=lambda score: (score.value, score.asset.symbol))
        count = len(ascending)
        if count == 0:
            return factor_contract.FactorResult(ranked=())
        if count == 1:
            return factor_contract.FactorResult(
                ranked=(
                    factor_contract.FactorScore(asset=ascending[0].asset, value=Decimal("0.5")),
                )
            )
        scores: list[factor_contract.FactorScore] = []
        denominator = Decimal(count - 1)
        for index, score in enumerate(ascending):
            scores.append(
                factor_contract.FactorScore(asset=score.asset, value=Decimal(index) / denominator)
            )
        return _ranked(scores)


@dataclass(frozen=True, slots=True)
class WeightedSumFactor:
    """Per-asset weighted sum of several sub-factors over their shared assets."""

    terms: tuple[tuple[factor_contract.Factor, Decimal], ...]
    name: ClassVar[str] = "weighted_sum"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate weighted-sum configuration and normalize weights to Decimal."""
        if not self.terms:
            raise ValueError("weighted_sum requires at least one term")
        normalized = tuple((factor, Decimal(str(weight))) for factor, weight in self.terms)
        for _factor, weight in normalized:
            if not weight.is_finite():
                raise ValueError("weight must be finite")
        object.__setattr__(self, "terms", normalized)

    @property
    def lookback(self) -> int:
        """Return the maximum trailing observation count across terms."""
        return max(_factor_lookback(factor) for factor, _weight in self.terms)

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute the weighted sum of the term factors over their shared assets."""
        results = tuple(factor.compute(window) for factor, _weight in self.terms)
        weights = tuple(weight for _factor, weight in self.terms)
        scores: list[factor_contract.FactorScore] = []
        for asset in _common_assets(results):
            total = sum(
                (
                    result.score(asset) * weight
                    for result, weight in zip(results, weights, strict=True)
                ),
                Decimal("0"),
            )
            scores.append(factor_contract.FactorScore(asset=asset, value=total))
        return _ranked(scores)


@dataclass(frozen=True, slots=True)
class ThresholdFactor:
    """Binary gate: score 1 when a sub-factor meets a threshold, else 0."""

    factor: factor_contract.Factor
    threshold: Decimal
    name: ClassVar[str] = "threshold"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate threshold configuration and normalize to Decimal."""
        object.__setattr__(self, "threshold", Decimal(str(self.threshold)))
        if not self.threshold.is_finite():
            raise ValueError("threshold must be finite")

    @property
    def lookback(self) -> int:
        """Return the trailing observation count of the wrapped factor."""
        return _factor_lookback(self.factor)

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute the binary threshold gate of the wrapped factor."""
        result = self.factor.compute(window)
        scores = [
            factor_contract.FactorScore(
                asset=score.asset,
                value=Decimal("1") if score.value >= self.threshold else Decimal("0"),
            )
            for score in result.ranked
        ]
        return _ranked(scores)


def _factor_lookback(factor: factor_contract.Factor) -> int:
    """Return a factor's declared lookback, defaulting to 1 when absent."""
    lookback = getattr(factor, "lookback", 1)
    return int(lookback)


__all__ = [
    "RankFactor",
    "RatioFactor",
    "ThresholdFactor",
    "WeightedSumFactor",
    "ZScoreFactor",
]
