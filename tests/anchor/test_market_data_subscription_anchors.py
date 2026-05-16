from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from qts.core.ids import InstrumentId
from qts.data.capabilities import MarketDataFeedCapabilities
from qts.data.subscriptions import LogicalSubscription, plan_physical_subscription


def test_provider_5s_source_does_not_redefine_requested_1m_bar_semantics() -> None:
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    capabilities = MarketDataFeedCapabilities(
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
    capabilities = MarketDataFeedCapabilities(
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
    capabilities = MarketDataFeedCapabilities(
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


def test_streaming_source_stale_degradation_uses_internal_instrument_id() -> None:
    from qts.core.ids import BrokerId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.sources.streaming_market_data_source import (
        StreamingMarketDataDegradation,
        StreamingMarketDataSource,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    source = StreamingMarketDataSource(
        adapter=IbkrMarketDataAdapter(
            connection=IbkrMarketDataConnection(
                host="127.0.0.1",
                port=4002,
                client_id=101,
                source_id="ibkr-paper-md",
            ),
            symbol_mapping=mapping,
        ),
        default_max_age=timedelta(seconds=5),
    )
    subscribed_at = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    source.subscribe(
        LogicalSubscription("strategy-a", instrument_id, "1m"), subscribed_at=subscribed_at
    )
    source.drain(observed_at=subscribed_at)

    [degradation] = source.drain(observed_at=subscribed_at + timedelta(seconds=6))

    assert isinstance(degradation, StreamingMarketDataDegradation)
    assert degradation.instrument_id == instrument_id
    assert not hasattr(degradation, "broker_symbol")
