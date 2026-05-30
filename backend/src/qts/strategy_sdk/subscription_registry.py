"""Subscription registry used by strategy context."""

from __future__ import annotations

from dataclasses import dataclass

from qts.strategy_sdk.asset_ref import AssetRef


@dataclass(frozen=True, slots=True)
class DataSubscription:
    """Strategy-declared market data requirement."""

    asset: AssetRef
    timeframe: str
    warmup: int

    def __post_init__(self) -> None:
        """Require a non-empty timeframe and a positive warmup."""
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if self.warmup <= 0:
            raise ValueError("warmup must be positive")


class StrategySubscriptionRegistry:
    """Own strategy subscriptions and enforce invariant validation."""

    def __init__(self) -> None:
        """Initialize an empty list of data subscriptions."""
        self._subscriptions: list[DataSubscription] = []

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        """Return the registered subscriptions as an immutable tuple."""
        return tuple(self._subscriptions)

    def subscribe(self, subscription: DataSubscription) -> DataSubscription:
        """Register a data subscription and return it."""
        self._subscriptions.append(subscription)
        return subscription


__all__ = ["DataSubscription", "StrategySubscriptionRegistry"]
