from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.events import (
    MarketDataSourceFailure,
    MarketDataSubscription,
)
from qts.data.live.reconnect import ReconnectPolicy
from qts.domain.market_data import Tick
from qts.testing.fakes.market_data import FakeStreamingMarketDataAdapter


def test_feed_capabilities_are_typed_and_validate_limits() -> None:
    capabilities = MarketDataFeedCapabilities(
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
        MarketDataFeedCapabilities(source_id="bad", max_subscriptions=0)


def test_feed_capabilities_choose_source_timeframe_for_derived_bar_request() -> None:
    capabilities = MarketDataFeedCapabilities(
        source_id="ibkr-live",
        supported_timeframes=frozenset({"5s"}),
    )

    assert capabilities.source_timeframe_for("1m") == "5s"
    assert capabilities.source_timeframe_for("2m") == "5s"
    assert capabilities.source_timeframe_for("3m") == "5s"
    assert capabilities.source_timeframe_for("5m") == "5s"


def test_one_minute_source_can_derive_two_and_three_minute_bars() -> None:
    capabilities = MarketDataFeedCapabilities(
        source_id="historical-1m",
        supports_bars=True,
        supported_timeframes=frozenset({"1m"}),
    )

    assert capabilities.source_timeframe_for("2m") == "1m"
    assert capabilities.source_timeframe_for("3m") == "1m"


def test_one_minute_source_can_derive_session_daily_bars() -> None:
    capabilities = MarketDataFeedCapabilities(
        source_id="historical-1m",
        supports_bars=True,
        supported_timeframes=frozenset({"1m"}),
    )

    assert capabilities.source_timeframe_for("1d") == "1m"


def test_fake_live_feed_exposes_configured_capabilities_and_subscription_count() -> None:
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    adapter = FakeStreamingMarketDataAdapter(
        source_id="fake-live",
        capabilities=MarketDataFeedCapabilities(
            source_id="fake-live",
            supported_timeframes=frozenset({"5s"}),
        ),
    )

    adapter.subscribe(MarketDataSubscription("sub-1", instrument_id, timeframe="5s"))
    adapter.subscribe(MarketDataSubscription("sub-1", instrument_id, timeframe="5s"))

    assert adapter.capabilities.source_timeframe_for("1m") == "5s"
    assert adapter.subscription_count == 1


def test_fake_live_feed_subscribe_emit_and_failure_contract() -> None:
    adapter = FakeStreamingMarketDataAdapter(source_id="fake-live")
    subscription = MarketDataSubscription(
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
    assert isinstance(failure, MarketDataSourceFailure)
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
