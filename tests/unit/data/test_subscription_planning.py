from __future__ import annotations

import pytest

from qts.core.ids import InstrumentId
from qts.data.live_feed import FeedCapabilities
from qts.data.subscriptions import (
    LogicalSubscription,
    PhysicalSubscriptionKey,
    SourceStreamType,
    plan_physical_subscription,
)


def test_ibkr_style_capability_maps_requested_minutes_to_single_5s_source() -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    capabilities = FeedCapabilities(
        source_id="ibkr-live-md",
        supports_bars=True,
        supported_timeframes=frozenset({"5s"}),
    )

    one_minute = plan_physical_subscription(
        LogicalSubscription(
            subscriber_id="strategy-a",
            instrument_id=instrument_id,
            requested_timeframe="1m",
        ),
        capabilities=capabilities,
    )
    five_minutes = plan_physical_subscription(
        LogicalSubscription(
            subscriber_id="strategy-b",
            instrument_id=instrument_id,
            requested_timeframe="5m",
        ),
        capabilities=capabilities,
    )

    expected = PhysicalSubscriptionKey(
        source_id="ibkr-live-md",
        instrument_id=instrument_id,
        stream_type=SourceStreamType.BAR,
        source_timeframe="5s",
    )
    assert one_minute == expected
    assert five_minutes == expected


def test_coarse_source_rejects_finer_requested_timeframe() -> None:
    capabilities = FeedCapabilities(
        source_id="historical-1m",
        supports_bars=True,
        supported_timeframes=frozenset({"1m"}),
    )

    with pytest.raises(ValueError, match="cannot be derived"):
        plan_physical_subscription(
            LogicalSubscription(
                subscriber_id="strategy-a",
                instrument_id=InstrumentId("FUTURE.CME.GC.GCQ0"),
                requested_timeframe="5s",
            ),
            capabilities=capabilities,
        )
