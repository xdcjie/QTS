"""Versioned factor research contract."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Literal, Protocol, runtime_checkable


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
        """Return the score for an asset in this result."""
        for item in self.ranked:
            if item.asset == asset:
                return item.value
        raise KeyError(f"missing factor score for asset: {asset.symbol}")


@dataclass(frozen=True, slots=True)
class FactorWindow:
    """Time-sliced cross-sectional input window for factor computation."""

    prices: dict[FactorAsset, tuple[Decimal | None, ...]]
    lookback: int
    universe: tuple[FactorAsset, ...] | None = None
    missing_data: Literal["raise", "drop"] = "raise"

    def __post_init__(self) -> None:
        """Validate factor window semantics."""
        if self.lookback <= 0:
            raise ValueError("lookback must be positive")
        if self.missing_data not in {"raise", "drop"}:
            raise ValueError("missing_data must be 'raise' or 'drop'")

    def assets(self) -> tuple[FactorAsset, ...]:
        """Return the assets that should be considered by a factor."""
        if self.universe is not None:
            return self.universe
        return tuple(sorted(self.prices, key=lambda asset: asset.symbol))

    def trailing_prices(self, asset: FactorAsset) -> tuple[Decimal, ...] | None:
        """Return trailing lookback prices, or None when missing data is dropped."""
        if asset not in self.prices:
            if self.missing_data == "drop":
                return None
            raise ValueError(f"missing price history for asset: {asset.symbol}")
        values = self.prices[asset]
        if len(values) < self.lookback:
            if self.missing_data == "drop":
                return None
            raise ValueError(f"not enough prices for asset: {asset.symbol}")
        trailing = values[-self.lookback :]
        if any(value is None for value in trailing):
            if self.missing_data == "drop":
                return None
            raise ValueError(f"missing price for asset: {asset.symbol}")
        return tuple(value for value in trailing if value is not None)


@runtime_checkable
class Factor(Protocol):
    """Versioned factor contract."""

    name: ClassVar[str]
    version: ClassVar[str]

    @property
    def lookback(self) -> int:
        """Return the trailing observation count required by this factor."""
        ...

    def compute(self, window: FactorWindow) -> FactorResult:
        """Compute factor scores for a time-sliced input window."""


__all__ = ["Factor", "FactorAsset", "FactorResult", "FactorScore", "FactorWindow"]
