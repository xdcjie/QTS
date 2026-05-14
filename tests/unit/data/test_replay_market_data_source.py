from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def test_subscription_replay_source_emits_only_active_subscriptions_at_bar_end() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    aapl = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    msft = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    aapl_bar = _bar(aapl, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    msft_bar = _bar(msft, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    source = SubscriptionReplayMarketDataSource(bars=(msft_bar, aapl_bar))
    observed: list[Bar] = []
    source.on_event(observed.append)

    source.subscribe(LogicalSubscription("strategy-a", aapl, "1m"))

    event = source.poll_next()
    drained = source.poll_next()

    assert event == aapl_bar
    assert source.current_time == aapl_bar.end_time
    assert observed == [aapl_bar]
    assert drained is None


def test_replay_clock_advances_monotonically_to_event_visibility_time() -> None:
    import pytest
    from qts.data.sources.replay_market_data_source import ReplayClock

    clock = ReplayClock()
    first = datetime(2026, 1, 2, 14, 31, tzinfo=UTC)
    second = datetime(2026, 1, 2, 14, 32, tzinfo=UTC)

    assert clock.current_time is None
    assert clock.advance_to_next_event(first) == first
    assert clock.advance_to_next_event(second) == second
    assert clock.current_time == second
    with pytest.raises(ValueError, match="cannot move backwards"):
        clock.advance_to_next_event(first)


def test_replay_event_sequencer_orders_by_visible_time_and_tie_breaker() -> None:
    from qts.data.sources.replay_market_data_source import ReplayEventSequencer

    aapl = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    msft = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    later = _bar(aapl, "2026-01-02T14:31:00+00:00", "2026-01-02T14:32:00+00:00")
    aapl_first = _bar(aapl, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    msft_first = _bar(msft, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")

    sequencer = ReplayEventSequencer(source_id="replay-source")
    events = sequencer.sequence((msft_first, later, aapl_first))

    assert [event.bar for event in events] == [aapl_first, msft_first, later]
    assert [event.visible_at for event in events] == [
        aapl_first.end_time,
        msft_first.end_time,
        later.end_time,
    ]
    assert sequencer.drain_diagnostic_events() == ()


def test_subscription_replay_source_mid_run_subscribe_only_emits_future_bars() -> None:
    from qts.core.ids import InstrumentId
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    first = _bar(instrument_id, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    second = _bar(instrument_id, "2026-01-02T14:31:00+00:00", "2026-01-02T14:32:00+00:00")
    source = SubscriptionReplayMarketDataSource(bars=(first, second))

    source.subscribe(
        LogicalSubscription("strategy-a", instrument_id, "1m"),
        subscribed_at=second.end_time,
    )

    assert source.poll_next() == second
    assert source.poll_next() is None


def test_subscription_replay_source_emits_subscription_lifecycle_events() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import (
        LogicalSubscription,
        MarketDataSubscriptionEventType,
    )

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    subscribed_at = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    unsubscribed_at = datetime(2026, 1, 2, 14, 31, tzinfo=UTC)
    subscription = LogicalSubscription("strategy-a", instrument_id, "1m")
    source = SubscriptionReplayMarketDataSource(
        bars=(
            _bar(
                instrument_id,
                "2026-01-02T14:30:00+00:00",
                "2026-01-02T14:31:00+00:00",
            ),
        ),
        source_id="replay-source",
    )

    source.subscribe(subscription, subscribed_at=subscribed_at)
    [subscribed] = source.drain_control_events()
    source.unsubscribe(subscription, observed_at=unsubscribed_at)
    [unsubscribed] = source.drain_control_events()

    assert subscribed.event_type is MarketDataSubscriptionEventType.SUBSCRIBED
    assert subscribed.source_id == "replay-source"
    assert subscribed.instrument_id == instrument_id
    assert subscribed.broker_symbol == instrument_id.value
    assert subscribed.observed_at == subscribed_at
    assert unsubscribed.event_type is MarketDataSubscriptionEventType.UNSUBSCRIBED
    assert unsubscribed.subscription == subscribed.subscription
    assert unsubscribed.observed_at == unsubscribed_at


def test_subscription_replay_source_drops_duplicates_and_reports_gaps() -> None:
    from qts.data.provenance import ReplayDataAnomalyType
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    first = _bar(instrument_id, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    duplicate = _bar(
        instrument_id,
        "2026-01-02T14:30:00+00:00",
        "2026-01-02T14:31:00+00:00",
    )
    after_gap = _bar(
        instrument_id,
        "2026-01-02T14:33:00+00:00",
        "2026-01-02T14:34:00+00:00",
    )
    source = SubscriptionReplayMarketDataSource(
        bars=(duplicate, after_gap, first),
        source_id="replay-source",
    )

    source.subscribe(LogicalSubscription("strategy-a", instrument_id, "1m"))

    assert source.poll_next() == first
    assert source.poll_next() == after_gap
    assert source.poll_next() is None
    assert [event.anomaly_type for event in source.drain_diagnostic_events()] == [
        ReplayDataAnomalyType.DUPLICATE_DROPPED,
        ReplayDataAnomalyType.GAP_DETECTED,
    ]


def _bar(instrument_id: InstrumentId, start: str, end: str) -> Bar:
    return Bar(
        instrument_id=instrument_id,
        start_time=datetime.fromisoformat(start).astimezone(UTC),
        end_time=datetime.fromisoformat(end).astimezone(UTC),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
        is_complete=True,
    )
