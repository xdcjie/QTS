from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(start: datetime, *, close: str = "100", timeframe: str = "1m") -> Bar:
    close_value = Decimal(close)
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe=timeframe,
        session_id="2026-01-02",
        open=Decimal("100"),
        high=max(Decimal("100"), close_value),
        low=min(Decimal("100"), close_value),
        close=close_value,
        volume=Decimal("10"),
        is_complete=True,
    )


def test_market_data_flow_publishes_actor_ready_bars() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})

    assert flow.publish_bar(bar) == (bar,)


def test_market_data_flow_requires_timezone_for_target_aggregation() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    flow = MarketDataFlow(target_timeframe="5m", exchange_timezone_by_instrument={})

    with pytest.raises(RuntimeError, match="exchange timezone is required"):
        flow.publish_bar(bar)


def test_resampled_bar_close_not_visible_before_bucket_end() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    flow = MarketDataFlow(
        target_timeframe="5m",
        exchange_timezone_by_instrument={InstrumentId("EQUITY.US.NASDAQ.AAPL"): UTC},
    )

    for minute in range(4):
        assert (
            flow.publish_bar(_bar(start + timedelta(minutes=minute), close=str(100 + minute))) == ()
        )

    [resampled] = flow.publish_bar(_bar(start + timedelta(minutes=4), close="104"))

    assert resampled.start_time == start
    assert resampled.end_time == start + timedelta(minutes=5)
    assert resampled.timeframe == "5m"
    assert resampled.close == Decimal("104")


def test_market_data_flow_drops_incomplete_derived_bucket_when_next_bucket_starts() -> None:
    from qts.runtime.market_data_flow import MarketDataFlow

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    flow = MarketDataFlow(
        target_timeframe="5m",
        exchange_timezone_by_instrument={instrument_id: UTC},
    )

    for minute in range(4):
        result = flow.publish_bar(_bar(start + timedelta(minutes=minute), close=str(100 + minute)))
        assert result == ()

    assert flow.publish_bar(_bar(start + timedelta(minutes=5), close="200")) == ()


def test_market_data_flow_exposes_replay_data_anomalies_as_runtime_events() -> None:
    from qts.data.provenance import ReplayDataAnomalyEvent, ReplayDataAnomalyType
    from qts.runtime.market_data_flow import MarketDataFlow

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    start = datetime(2026, 1, 2, 14, 33, tzinfo=UTC)
    event = ReplayDataAnomalyEvent(
        anomaly_type=ReplayDataAnomalyType.GAP_DETECTED,
        source_id="replay-source",
        instrument_id=instrument_id,
        timeframe="1m",
        bar_start=start,
        bar_end=start + timedelta(minutes=1),
        observed_at=start,
        previous_end=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
    )
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})

    result = flow.publish_source_event(event)

    assert [runtime_event.kind for runtime_event in result.runtime_events] == [
        "replay_gap_detected",
        "runtime.degraded",
    ]
    assert result.runtime_events[0].payload["source_id"] == "replay-source"
    assert result.runtime_events[0].payload["instrument_id"] == instrument_id.value
    assert result.runtime_events[1].payload["reason"] == "replay_gap_detected"


def test_market_data_flow_emits_explicit_stale_data_event() -> None:
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataDegradation
    from qts.data.subscriptions import LogicalSubscriptionKey
    from qts.runtime.market_data_flow import MarketDataFlow

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    observed_at = datetime(2026, 1, 2, 14, 35, tzinfo=UTC)
    degradation = StreamingMarketDataDegradation(
        instrument_id=instrument_id,
        subscription=LogicalSubscriptionKey(instrument_id=instrument_id, requested_timeframe="1m"),
        observed_at=observed_at,
        age=timedelta(seconds=61),
        max_age=timedelta(seconds=30),
    )
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})

    result = flow.publish_source_event(degradation)

    assert [event.kind for event in result.runtime_events] == [
        "market_data_stale_detected",
        "runtime.degraded",
    ]
    assert result.runtime_events[0].payload["reason_code"] == "MARKET_DATA_STALE"
    assert result.runtime_events[1].payload["reason_code"] == "MARKET_DATA_STALE"


def test_market_data_flow_risk_context_combines_permission_and_stale_evidence() -> None:
    from qts.data.permissions import MarketDataPermissionEvent, MarketDataPermissionState
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataDegradation
    from qts.data.subscriptions import LogicalSubscriptionKey
    from qts.domain.risk import MarketDataRiskContext
    from qts.runtime.market_data_flow import MarketDataFlow

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    observed_at = datetime(2026, 1, 2, 14, 35, tzinfo=UTC)
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})

    flow.publish_source_event(
        MarketDataPermissionEvent(
            source_id="ibkr-live-md",
            permission_state=MarketDataPermissionState.DELAYED,
            provider_market_data_type=3,
            request_id=17,
        )
    )
    flow.publish_source_event(
        StreamingMarketDataDegradation(
            instrument_id=instrument_id,
            subscription=LogicalSubscriptionKey(
                instrument_id=instrument_id,
                requested_timeframe="1m",
            ),
            observed_at=observed_at,
            age=timedelta(seconds=61),
            max_age=timedelta(seconds=30),
        )
    )

    context = flow.risk_context_for(instrument_id)

    assert isinstance(context, MarketDataRiskContext)
    assert context.permission_state == "delayed"
    assert context.stale is True
    assert context.evidence_payload()["source_id"] == "ibkr-live-md"
    assert context.evidence_payload()["instrument_id"] == instrument_id.value
    assert context.evidence_payload()["age_seconds"] == 61
