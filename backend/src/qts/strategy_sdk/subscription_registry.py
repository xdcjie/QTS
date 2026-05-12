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
        """Perform __post_init__."""
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if self.warmup <= 0:
            raise ValueError("warmup must be positive")


class StrategySubscriptionRegistry:
    """Own strategy subscriptions and enforce invariant validation."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._subscriptions: list[DataSubscription] = []

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        """Perform subscriptions."""
        return tuple(self._subscriptions)

    def subscribe(self, subscription: DataSubscription) -> DataSubscription:
        """Perform subscribe."""
        self._subscriptions.append(subscription)
        return subscription


__all__ = ["DataSubscription", "StrategySubscriptionRegistry"]
