"""Unit tests for strategy subscription registry."""

from __future__ import annotations

from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.subscription_registry import DataSubscription, StrategySubscriptionRegistry


def test_subscription_registry_keeps_subscriptions_ordered() -> None:
    registry = StrategySubscriptionRegistry()
    aapl = AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")
    gcq0 = AssetRef(InstrumentId("FUTURE.CME.GC.GCQ0"), "GCQ0")

    first = registry.subscribe(DataSubscription(asset=aapl, timeframe="1m", warmup=10))
    second = registry.subscribe(DataSubscription(asset=gcq0, timeframe="5m", warmup=1))

    assert registry.subscriptions == (first, second)
