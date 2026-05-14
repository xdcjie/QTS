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
