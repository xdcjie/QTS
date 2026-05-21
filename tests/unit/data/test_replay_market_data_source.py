from __future__ import annotations

import csv
import shutil
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
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


def test_bar_close_visible_only_at_bar_end() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    bar = _bar(instrument_id, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    source = SubscriptionReplayMarketDataSource(bars=(bar,))
    source.subscribe(LogicalSubscription("strategy-a", instrument_id, "1m"))

    assert source.poll_next(as_of=bar.start_time) is None
    assert source.current_time is None
    assert source.poll_next(as_of=bar.end_time) == bar
    assert source.current_time == bar.end_time


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
    events = sequencer.sequence((msft_first, aapl_first, later))

    assert [event.bar for event in events] == [aapl_first, msft_first, later]
    assert [event.visible_at for event in events] == [
        aapl_first.end_time,
        msft_first.end_time,
        later.end_time,
    ]
    assert sequencer.drain_diagnostic_events() == ()


def test_multi_instrument_same_timestamp_order_is_deterministic() -> None:
    from qts.data.sources.replay_market_data_source import ReplayEventSequencer

    aapl = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    msft = InstrumentId("EQUITY.US.NASDAQ.MSFT")
    same_visible_at = "2026-01-02T14:31:00+00:00"
    aapl_bar = _bar(aapl, "2026-01-02T14:30:00+00:00", same_visible_at)
    msft_bar = _bar(msft, "2026-01-02T14:30:00+00:00", same_visible_at)

    sequencer = ReplayEventSequencer(source_id="replay-source")

    assert [event.bar for event in sequencer.sequence((msft_bar, aapl_bar))] == [
        aapl_bar,
        msft_bar,
    ]
    assert [event.bar for event in sequencer.sequence((aapl_bar, msft_bar))] == [
        aapl_bar,
        msft_bar,
    ]


def test_subscription_replay_source_unsubscribe_stops_later_delivery() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    first = _bar(instrument_id, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    second = _bar(instrument_id, "2026-01-02T14:31:00+00:00", "2026-01-02T14:32:00+00:00")
    subscription = LogicalSubscription("strategy-a", instrument_id, "1m")
    source = SubscriptionReplayMarketDataSource(bars=(first, second))

    source.subscribe(subscription)
    assert source.poll_next() == first
    source.unsubscribe(subscription, observed_at=first.end_time)

    assert source.poll_next() is None


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


def test_session_boundary_next_open_bar_not_visible_before_next_bar_end() -> None:
    from qts.data.sources.replay_market_data_source import SubscriptionReplayMarketDataSource
    from qts.data.subscriptions import LogicalSubscription

    instrument_id = InstrumentId("FUT.US.COMEX.GC.202602")
    session_close = datetime(2026, 1, 6, 22, 0, tzinfo=UTC)
    next_open = datetime(2026, 1, 6, 23, 0, tzinfo=UTC)
    next_bar = Bar(
        instrument_id=instrument_id,
        start_time=next_open,
        end_time=next_open + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-07",
        open=Decimal("2050"),
        high=Decimal("2051"),
        low=Decimal("2049"),
        close=Decimal("2050.5"),
        is_complete=True,
    )
    source = SubscriptionReplayMarketDataSource(bars=(next_bar,))
    source.subscribe(LogicalSubscription("strategy-a", instrument_id, "1m"))

    assert source.poll_next(as_of=session_close) is None
    assert source.current_time is None
    assert source.poll_next(as_of=next_bar.end_time) == next_bar


def test_replay_event_sequencer_rejects_out_of_order_source_bar() -> None:
    from qts.data.provenance import ReplayDataAnomalyType
    from qts.data.sources.replay_market_data_source import ReplayEventSequencer

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    first = _bar(instrument_id, "2026-01-02T14:30:00+00:00", "2026-01-02T14:31:00+00:00")
    second = _bar(instrument_id, "2026-01-02T14:31:00+00:00", "2026-01-02T14:32:00+00:00")
    sequencer = ReplayEventSequencer(source_id="replay-source")

    events = sequencer.sequence((second, first))

    assert [event.bar for event in events] == [second]
    [diagnostic] = sequencer.drain_diagnostic_events()
    assert diagnostic.anomaly_type is ReplayDataAnomalyType.OUT_OF_ORDER_REJECTED
    assert diagnostic.previous_end == second.end_time


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
        bars=(first, duplicate, after_gap),
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


def test_replay_market_data_bundle_builder_assembles_registry_and_provenance(
    tmp_path: Path,
) -> None:
    from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
    from qts.data.sources.replay_bundle_builder import ReplayMarketDataBundleBuilder
    from qts.runtime.config import (
        BacktestMarketDataReference,
        BacktestRiskConfig,
        BacktestRuntimeConfig,
    )

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    csv_path = historical_root / "data" / "equity.csv"
    _write_fixture_csv(csv_path)
    data_config_path = tmp_path / "historical.local.yaml"
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
      defaults:
        timezone_policy: custom_exchange_policy
        normalization: vendor_adjusted
  catalogs:
    research:
      store: local_csv
      datasets:
        EQUITY:
          asset_class: equity
          bars:
            - file: equity.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )
    config = BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=data_config_path,
            catalog="research",
        ),
        roots=("EQUITY",),
        symbols=("AAPL",),
        instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 1, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.integration.test_backtest_gc_si:BuyOneAaplStrategy",
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
    )
    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            data_config_path,
            catalog="research",
            roots=config.roots,
            instrument_ids=config.instrument_ids,
            requested_timeframe=config.timeframe,
        )
    )

    bundle = ReplayMarketDataBundleBuilder(config=config, catalog=catalog).build()
    bars = tuple(bundle.bars)

    assert [bar.instrument_id for bar in bars] == [InstrumentId("EQUITY.US.NASDAQ.AAPL")]
    assert bundle.instrument_registry.resolve("AAPL") == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert bundle.contract_multipliers == {}
    assert bundle.dataset_stats["EQUITY"]["bars_emitted"] == 1
    assert bundle.dataset_metadata[0].source == str(csv_path)
    assert bundle.dataset_metadata[0].timezone_policy == "custom_exchange_policy"
    assert bundle.dataset_metadata[0].adjustment_policy == "vendor_adjusted"
    assert bundle.future_roll_registry is None


def test_replay_bundle_roll_registry_resolves_synthetic_bar_contracts(
    tmp_path: Path,
) -> None:
    from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
    from qts.data.sources.replay_bundle_builder import ReplayMarketDataBundleBuilder
    from qts.runtime.config import (
        BacktestMarketDataReference,
        BacktestRiskConfig,
        BacktestRuntimeConfig,
        RollPolicyConfig,
    )

    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), historical_root / "chains" / "GC.json")
    csv_path = historical_root / "data" / "gc.csv"
    _write_future_rows(
        csv_path,
        [
            ("2010-06-06T22:00:00.000000000Z", "GCQ0", "1200.0"),
            ("2010-06-06T22:02:00.000000000Z", "GCQ0", "1201.0"),
        ],
    )
    data_config_path = tmp_path / "historical.local.yaml"
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
      defaults:
        exchange_timezone: US/Eastern
        timezone_policy: source_utc_exchange_sessions
        normalization: raw
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )
    config = BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=data_config_path,
            catalog="research_futures",
        ),
        roots=("GC",),
        symbols=("GC",),
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 3, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("1000000"),
        strategy_class="tests.integration.test_backtest_gc_si:RollingGcStrategy",
        roll_policy=RollPolicyConfig(enabled=True),
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
    )
    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            data_config_path,
            catalog="research_futures",
            roots=config.roots,
            instrument_ids=config.instrument_ids,
            requested_timeframe=config.timeframe,
        )
    )

    bundle = ReplayMarketDataBundleBuilder(config=config, catalog=catalog).build()
    first = next(bundle.bars)
    synthetic = next(bundle.bars)

    assert first.end_time == datetime(2010, 6, 6, 22, 1, tzinfo=UTC)
    assert synthetic.is_synthetic is True
    assert synthetic.end_time == datetime(2010, 6, 6, 22, 2, tzinfo=UTC)
    assert bundle.future_roll_registry is not None
    assert bundle.future_roll_registry.resolve_contract(
        synthetic.instrument_id,
        as_of=synthetic.end_time,
    ) == InstrumentId("FUTURE.CME.GC.GCQ0")


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


def _write_fixture_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerow(
            {
                "ts_event": "2010-06-06T22:00:00.000000000Z",
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": "AAPL",
                "open": "150.0",
                "high": "150.0",
                "low": "150.0",
                "close": "150.0",
                "volume": "100",
                "symbol": "AAPL",
            }
        )


def _write_future_rows(path: Path, rows: list[tuple[str, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index, (ts_event, symbol, close) in enumerate(rows, start=1):
            writer.writerow(
                {
                    "ts_event": ts_event,
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": str(index),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "100",
                    "symbol": symbol,
                }
            )
