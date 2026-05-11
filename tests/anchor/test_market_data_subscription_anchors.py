from __future__ import annotations

import pytest
from qts.core.ids import InstrumentId
from qts.data.live_feed import FeedCapabilities
from qts.data.subscriptions import LogicalSubscription, plan_physical_subscription


def test_provider_5s_source_does_not_redefine_requested_1m_bar_semantics() -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    capabilities = FeedCapabilities(
        source_id="ibkr-live-md",
        supported_timeframes=frozenset({"5s"}),
    )

    physical = plan_physical_subscription(
        LogicalSubscription("strategy-a", instrument_id, "1m"),
        capabilities=capabilities,
    )

    assert physical.source_timeframe == "5s"


def test_multiple_derived_timeframes_share_one_5s_physical_subscription_key() -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    capabilities = FeedCapabilities(
        source_id="ibkr-live-md",
        supported_timeframes=frozenset({"5s"}),
    )

    one_minute = plan_physical_subscription(
        LogicalSubscription("strategy-a", instrument_id, "1m"),
        capabilities=capabilities,
    )
    five_minutes = plan_physical_subscription(
        LogicalSubscription("strategy-b", instrument_id, "5m"),
        capabilities=capabilities,
    )

    assert one_minute == five_minutes


def test_coarse_historical_source_rejects_finer_requested_timeframe() -> None:
    capabilities = FeedCapabilities(
        source_id="historical-1m",
        supported_timeframes=frozenset({"1m"}),
    )

    with pytest.raises(ValueError, match="cannot be derived"):
        plan_physical_subscription(
            LogicalSubscription(
                "strategy-a",
                InstrumentId("FUTURE.CME.GC.GCQ0"),
                "5s",
            ),
            capabilities=capabilities,
        )
