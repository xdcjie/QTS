from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import InstrumentId
from qts.data.events import MarketDataSubscription as FeedSubscription
from qts.data.historical.adapter import HistoricalMarketDataAdapter
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.domain.market_data import Bar
from qts.registry.symbol_resolution import StaticSymbolResolver


def test_historical_market_data_adapter_is_primary_historical_source_name(
    tmp_path: Path,
) -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    csv_path = tmp_path / "gc.csv"
    _write_rows(csv_path, [_row("2026-01-02T14:30:00.000000000Z", "GCQ0", "2000")])
    adapter = HistoricalMarketDataAdapter(
        source_id="historical-gc",
        csv_path=csv_path,
        symbol_resolver=StaticSymbolResolver({"GCQ0": instrument_id}),
        source_timeframe="1m",
        start=start,
        end=start + timedelta(minutes=1),
    )
    subscription = FeedSubscription(
        subscription_id="hist-1",
        instrument_id=instrument_id,
        timeframe="1m",
    )

    adapter.subscribe(subscription)

    assert tuple(adapter.events(subscription.subscription_id))[0].source_id == "historical-gc"


def test_historical_adapter_has_no_replay_or_service_aliases() -> None:
    import qts.data as data
    import qts.data.historical as historical

    assert not hasattr(data, "ReplayMarketDataAdapter")
    assert not hasattr(historical, "ReplayMarketDataAdapter")
    assert not hasattr(historical, "HistoricalMarketDataService")


def test_historical_market_data_adapter_replays_normalized_bars_for_subscription(
    tmp_path: Path,
) -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    csv_path = tmp_path / "gc.csv"
    _write_rows(
        csv_path,
        [
            _row("2026-01-02T14:30:00.000000000Z", "GCQ0", "2000"),
            _row("2026-01-02T14:31:00.000000000Z", "GCQ0", "2001"),
            _row("2026-01-02T14:32:00.000000000Z", "GCN0", "1999"),
        ],
    )
    adapter = HistoricalMarketDataAdapter(
        source_id="historical-gc",
        csv_path=csv_path,
        symbol_resolver=StaticSymbolResolver({"GCQ0": instrument_id}),
        source_timeframe="1m",
        start=start,
        end=start + timedelta(minutes=2),
    )
    subscription = FeedSubscription(
        subscription_id="hist-1",
        instrument_id=instrument_id,
        timeframe="1m",
    )

    subscribed = adapter.subscribe(subscription)
    events = tuple(adapter.events(subscription.subscription_id))

    assert subscribed.source_id == "historical-gc"
    assert [event.source_id for event in events] == ["historical-gc", "historical-gc"]
    payloads = tuple(event.payload for event in events)
    assert all(isinstance(payload, Bar) for payload in payloads)
    assert [payload.instrument_id for payload in payloads if isinstance(payload, Bar)] == [
        instrument_id,
        instrument_id,
    ]
    assert [payload.close for payload in payloads if isinstance(payload, Bar)] == [
        Decimal("2000"),
        Decimal("2001"),
    ]


def test_historical_market_data_adapter_rejects_finer_than_source_request(
    tmp_path: Path,
) -> None:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    instrument_id = InstrumentId("FUTURE.CME.GC.GCQ0")
    csv_path = tmp_path / "gc.csv"
    _write_rows(csv_path, [_row("2026-01-02T14:30:00.000000000Z", "GCQ0", "2000")])
    adapter = HistoricalMarketDataAdapter(
        source_id="historical-gc",
        csv_path=csv_path,
        symbol_resolver=StaticSymbolResolver({"GCQ0": instrument_id}),
        source_timeframe="1m",
        start=start,
        end=start + timedelta(minutes=1),
    )

    with pytest.raises(ValueError, match="cannot be derived"):
        adapter.subscribe(FeedSubscription("hist-5s", instrument_id, timeframe="5s"))


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(ts_event: str, symbol: str, close: str) -> dict[str, str]:
    return {
        "ts_event": ts_event,
        "rtype": "33",
        "publisher_id": "1",
        "instrument_id": symbol,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "volume": "1",
        "symbol": symbol,
    }
