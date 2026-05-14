from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.data.live import (
    FeedCapabilities,
    FeedSubscription,
    LiveFeedFailure,
    ReconnectPolicy,
)
from qts.domain.market_data import Tick

from tests.support.live_feed import FakeLiveFeedAdapter


def test_feed_capabilities_are_typed_and_validate_limits() -> None:
    capabilities = FeedCapabilities(
        source_id="fake-live",
        supports_ticks=True,
        supports_quotes=True,
        supports_bars=True,
        max_subscriptions=2,
        supported_timeframes=frozenset({"1m", "5m"}),
    )

    assert capabilities.supports_timeframe("1m")
    assert not capabilities.supports_timeframe("1d")
    with pytest.raises(ValueError, match="max_subscriptions"):
        FeedCapabilities(source_id="bad", max_subscriptions=0)


def test_feed_capabilities_choose_source_timeframe_for_derived_bar_request() -> None:
    capabilities = FeedCapabilities(
        source_id="ibkr-live",
        supported_timeframes=frozenset({"5s"}),
    )

    assert capabilities.source_timeframe_for("1m") == "5s"
    assert capabilities.source_timeframe_for("5m") == "5s"


def test_fake_live_feed_exposes_configured_capabilities_and_subscription_count() -> None:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    adapter = FakeLiveFeedAdapter(
        source_id="fake-live",
        capabilities=FeedCapabilities(
            source_id="fake-live",
            supported_timeframes=frozenset({"5s"}),
        ),
    )

    adapter.subscribe(FeedSubscription("sub-1", instrument_id, timeframe="5s"))
    adapter.subscribe(FeedSubscription("sub-1", instrument_id, timeframe="5s"))

    assert adapter.capabilities.source_timeframe_for("1m") == "5s"
    assert adapter.subscription_count == 1


def test_fake_live_feed_subscribe_emit_and_failure_contract() -> None:
    adapter = FakeLiveFeedAdapter(source_id="fake-live")
    subscription = FeedSubscription(
        subscription_id="sub-1",
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        timeframe="tick",
    )
    tick = Tick(
        instrument_id=subscription.instrument_id,
        time=datetime(2026, 5, 10, tzinfo=UTC),
        price=Decimal("190"),
        size=Decimal("1"),
    )

    subscribed = adapter.subscribe(subscription)
    emitted = adapter.emit(tick)
    failure = adapter.fail(subscription.subscription_id, reason="disconnected")

    assert subscribed.subscription == subscription
    assert emitted.payload == tick
    assert isinstance(failure, LiveFeedFailure)
    assert failure.subscription_id == subscription.subscription_id


def test_reconnect_policy_is_deterministic_and_bounded() -> None:
    policy = ReconnectPolicy(
        initial_delay=timedelta(seconds=1),
        multiplier=Decimal("2"),
        max_delay=timedelta(seconds=5),
        max_attempts=3,
    )

    assert [policy.delay_for_attempt(attempt) for attempt in range(1, 5)] == [
        timedelta(seconds=1),
        timedelta(seconds=2),
        timedelta(seconds=4),
        None,
    ]
