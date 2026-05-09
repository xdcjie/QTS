"""Momentum factor."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class FactorAsset(Protocol):
    """Minimal asset shape required by factor ranking."""

    @property
    def symbol(self) -> str:
        """Stable display symbol used for deterministic tie-breaking."""


@dataclass(frozen=True, slots=True)
class FactorScore:
    """Single asset factor score."""

    asset: FactorAsset
    value: Decimal


@dataclass(frozen=True, slots=True)
class FactorResult:
    """Ranked cross-sectional factor result."""

    ranked: tuple[FactorScore, ...]

    def score(self, asset: FactorAsset) -> Decimal:
        for item in self.ranked:
            if item.asset == asset:
                return item.value
        raise KeyError(f"missing factor score for asset: {asset.symbol}")


@dataclass(frozen=True, slots=True)
class MomentumFactor:
    """Compute simple period momentum as last / first - 1."""

    window: int

    def __post_init__(self) -> None:
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    def compute(self, prices: dict[FactorAsset, tuple[Decimal, ...]]) -> FactorResult:
        scores = tuple(
            FactorScore(asset=asset, value=_momentum(values, self.window))
            for asset, values in prices.items()
        )
        ranked = tuple(sorted(scores, key=lambda score: (-score.value, score.asset.symbol)))
        return FactorResult(ranked=ranked)


def _momentum(values: tuple[Decimal, ...], window: int) -> Decimal:
    if len(values) < window:
        raise ValueError("not enough prices for momentum window")
    window_values = values[-window:]
    first = window_values[0]
    if first == Decimal("0"):
        raise ValueError("first price must not be zero")
    return window_values[-1] / first - Decimal("1")


__all__ = ["FactorResult", "FactorScore", "MomentumFactor"]
