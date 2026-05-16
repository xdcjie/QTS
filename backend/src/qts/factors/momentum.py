"""Momentum factor."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

import qts.factors.contract as factor_contract


@dataclass(frozen=True, slots=True)
class MomentumFactor:
    """Compute simple period momentum as last / first - 1."""

    window: int
    name: ClassVar[str] = "momentum"
    version: ClassVar[str] = "1"

    def __post_init__(self) -> None:
        """Validate momentum configuration."""
        if self.window <= 1:
            raise ValueError("window must be greater than 1")

    @property
    def lookback(self) -> int:
        """Return the required trailing observation count."""
        return self.window

    def compute(self, window: factor_contract.FactorWindow) -> factor_contract.FactorResult:
        """Compute ranked momentum scores over the provided factor window."""
        if window.lookback < self.window:
            raise ValueError("factor window lookback is shorter than momentum window")

        scores: list[factor_contract.FactorScore] = []
        for asset in window.assets():
            values = window.trailing_prices(asset)
            if values is None:
                continue
            scores.append(factor_contract.FactorScore(asset=asset, value=self._momentum(values)))
        ranked = tuple(sorted(scores, key=lambda score: (-score.value, score.asset.symbol)))
        return factor_contract.FactorResult(ranked=ranked)

    @staticmethod
    def _momentum(values: tuple[Decimal, ...]) -> Decimal:
        """Compute simple momentum over already-windowed prices."""
        first = values[0]
        if first == Decimal("0"):
            raise ValueError("first price must not be zero")
        return values[-1] / first - Decimal("1")


__all__ = ["MomentumFactor"]
