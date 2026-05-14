from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal


def test_streaming_market_data_source_normalizes_callbacks_and_drains_complete_events() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.adapters.ibkr_transport import IbkrBarPayload, IbkrQuotePayload, IbkrTickPayload
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
    from qts.data.subscriptions import LogicalSubscription, SourceStreamType
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping
    from qts.runtime.market_data_flow import MarketDataFlow

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=4002,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )
    source = StreamingMarketDataSource(adapter=adapter, default_max_age=timedelta(minutes=5))

    source.subscribe(
        LogicalSubscription("strategy-a", instrument_id, "tick", SourceStreamType.TICK)
    )
    source.subscribe(
        LogicalSubscription("strategy-a", instrument_id, "quote", SourceStreamType.QUOTE)
    )
    source.subscribe(LogicalSubscription("strategy-a", instrument_id, "1m", SourceStreamType.BAR))
    tick = source.on_tick(
        IbkrTickPayload(
            broker_symbol="AAPL",
            time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            price=Decimal("101.25"),
            size=Decimal("10"),
        )
    )
    quote = source.on_quote(
        IbkrQuotePayload(
            broker_symbol="AAPL",
            time=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            bid_price=Decimal("101.20"),
            ask_price=Decimal("101.30"),
        )
    )
    complete_bar = source.on_bar(
        IbkrBarPayload(
            broker_symbol="AAPL",
            start_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            end_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("101.00"),
            high=Decimal("101.50"),
            low=Decimal("100.90"),
            close=Decimal("101.25"),
            is_complete=True,
        )
    )

    drained = source.drain(observed_at=datetime(2026, 1, 2, 14, 31, tzinfo=UTC))
    flow = MarketDataFlow(target_timeframe=None, exchange_timezone_by_instrument={})

    assert drained == (tick, quote, complete_bar)
    assert flow.publish_bar(complete_bar) == (complete_bar,)


def test_streaming_market_data_source_holds_partial_bars_until_complete() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.adapters.ibkr_transport import IbkrBarPayload
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
    from qts.data.subscriptions import LogicalSubscription
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
        )
    )
    source.subscribe(LogicalSubscription("strategy-a", instrument_id, "1m"))

    partial_bar = source.on_bar(
        IbkrBarPayload(
            broker_symbol="AAPL",
            start_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            end_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("101.00"),
            high=Decimal("101.50"),
            low=Decimal("100.90"),
            close=Decimal("101.25"),
            is_partial=True,
        )
    )

    assert partial_bar.is_partial
    assert source.drain(observed_at=datetime(2026, 1, 2, 14, 31, tzinfo=UTC)) == ()


def test_streaming_market_data_source_emits_stale_data_degradation() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.sources.streaming_market_data_source import (
        StreamingMarketDataDegradation,
        StreamingMarketDataSource,
    )
    from qts.data.subscriptions import LogicalSubscription
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    subscribed_at = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    subscription = LogicalSubscription("strategy-a", instrument_id, "1m")
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
    source.subscribe(subscription, subscribed_at=subscribed_at)

    [degradation] = source.drain(observed_at=subscribed_at + timedelta(seconds=6))

    assert isinstance(degradation, StreamingMarketDataDegradation)
    assert degradation.instrument_id == instrument_id
    assert degradation.reason == "stale_market_data"
    assert degradation.age == timedelta(seconds=6)
    assert degradation.max_age == timedelta(seconds=5)


def test_market_data_permission_event_is_visible_from_streaming_source() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
        MarketDataPermissionEvent,
        MarketDataPermissionState,
    )
    from qts.data.adapters.ibkr_transport import IbkrMarketDataTypePayload
    from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
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
        )
    )

    event = source.on_market_data_type(IbkrMarketDataTypePayload(request_id=7, market_data_type=3))

    assert isinstance(event, MarketDataPermissionEvent)
    assert event.permission_state is MarketDataPermissionState.DELAYED
    assert source.permission_state is MarketDataPermissionState.DELAYED
    assert source.drain(observed_at=datetime(2026, 1, 2, 14, 31, tzinfo=UTC)) == (event,)


def test_market_data_permission_event_enters_runtime_flow() -> None:
    from qts.data.adapters.ibkr_market_data import (
        MarketDataPermissionEvent,
        MarketDataPermissionState,
    )
    from qts.runtime.market_data_flow import MarketDataFlow

    event = MarketDataPermissionEvent(
        source_id="ibkr-paper-md",
        permission_state=MarketDataPermissionState.DELAYED,
        provider_market_data_type=3,
        request_id=7,
    )

    result = MarketDataFlow(
        target_timeframe=None,
        exchange_timezone_by_instrument={},
    ).publish_source_event(event)

    assert result.market_data == ()
    [runtime_event] = result.runtime_events
    assert runtime_event.kind == "market_data_permission_changed"
    assert runtime_event.payload["source_id"] == "ibkr-paper-md"
    assert runtime_event.payload["permission_state"] == "delayed"
    assert runtime_event.payload["provider_market_data_type"] == 3


def test_stale_market_data_degradation_enters_runtime_flow() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
    )
    from qts.data.sources.streaming_market_data_source import (
        StreamingMarketDataDegradation,
        StreamingMarketDataSource,
    )
    from qts.data.subscriptions import LogicalSubscription
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping
    from qts.runtime.market_data_flow import MarketDataFlow

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    subscribed_at = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
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
    source.subscribe(
        LogicalSubscription("strategy-a", instrument_id, "1m"),
        subscribed_at=subscribed_at,
    )
    [degradation] = source.drain(observed_at=subscribed_at + timedelta(seconds=6))
    assert isinstance(degradation, StreamingMarketDataDegradation)

    result = MarketDataFlow(
        target_timeframe=None,
        exchange_timezone_by_instrument={},
    ).publish_source_event(degradation)

    assert result.market_data == ()
    [runtime_event] = result.runtime_events
    assert runtime_event.kind == "runtime.degraded"
    assert runtime_event.payload["reason"] == "stale_market_data"
    assert runtime_event.payload["instrument_id"] == instrument_id.value
