from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal


def test_ibkr_market_data_adapter_normalizes_tick_quote_and_bar_without_order_methods() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
        LiveMarketDataAdapter,
    )
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    mapping = BrokerSymbolMapping(BrokerId("IBKR"))
    mapping.register(instrument_id, "AAPL")
    adapter = IbkrMarketDataAdapter(
        connection=IbkrMarketDataConnection(
            host="127.0.0.1",
            port=7497,
            client_id=101,
            source_id="ibkr-paper-md",
        ),
        symbol_mapping=mapping,
    )

    subscription = adapter.subscription_for(instrument_id)
    tick = adapter.normalize_tick(
        broker_symbol="AAPL",
        time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        price=Decimal("101.25"),
        size=Decimal("10"),
    )
    quote = adapter.normalize_quote(
        broker_symbol="AAPL",
        time=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
        bid_price=Decimal("101.20"),
        ask_price=Decimal("101.30"),
        bid_size=Decimal("20"),
        ask_size=Decimal("30"),
    )
    bar = adapter.normalize_bar(
        broker_symbol="AAPL",
        start_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        end_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("101.00"),
        high=Decimal("101.50"),
        low=Decimal("100.90"),
        close=Decimal("101.25"),
        volume=Decimal("1000"),
        vwap=Decimal("101.20"),
        trade_count=42,
        is_complete=True,
        is_partial=False,
    )

    assert subscription.broker_symbol == "AAPL"
    assert tick.instrument_id == instrument_id
    assert tick.price == Decimal("101.25")
    assert quote.instrument_id == instrument_id
    assert quote.spread == Decimal("0.10")
    assert bar.instrument_id == instrument_id
    assert bar.timeframe == "1m"
    assert bar.is_complete
    assert not bar.is_partial
    assert not hasattr(adapter, "submit_order")
    assert not hasattr(adapter, "cancel_order")
    assert LiveMarketDataAdapter is IbkrMarketDataAdapter


def test_ibkr_market_data_type_sets_permission_state() -> None:
    from qts.core.ids import BrokerId, InstrumentId
    from qts.data.adapters.ibkr_market_data import (
        IbkrMarketDataAdapter,
        IbkrMarketDataConnection,
        MarketDataPermissionState,
    )
    from qts.data.adapters.ibkr_transport import IbkrMarketDataTypePayload
    from qts.registry.broker_symbol_mapping import BrokerSymbolMapping

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

    event = adapter.on_market_data_type(IbkrMarketDataTypePayload(request_id=7, market_data_type=3))

    assert event.source_id == "ibkr-paper-md"
    assert event.provider_market_data_type == 3
    assert event.permission_state is MarketDataPermissionState.DELAYED
    assert adapter.permission_state is MarketDataPermissionState.DELAYED
