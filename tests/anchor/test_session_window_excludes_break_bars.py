"""Anchor: session_id reflects exchange-local session, not UTC calendar day.

Domain fact: ``docs/domain/market_calendar_and_sessions.md`` says
session_id is the exchange-local close date. For overnight futures
sessions (e.g. ``[ET 18:00, ET 17:00)``) the daily break sits inside
the same UTC calendar day; using UTC dates as session_id mislabels
break-time bars as in-session, and the
``BarTimeGridSynthesizer`` then bridges the gap with synthetic bars.

Owner: ``qts.data.historical.chains.HistoricalChain.session_window`` +
``qts.data.sources.replay_market_data_source.ReplayMarketDataSource``
(passes the chain-derived window to ``iter_historical_bars``).

Forbidden shortcut: deriving session_id from UTC date; bridging the
daily-session break with synthetic bars; emitting bars whose
timestamps fall inside the exchange-local break window.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from datetime import date, time
from pathlib import Path
from typing import Any

import pytest
from qts.backtest.pipeline import BacktestPipeline
from qts.data.historical.chains import HistoricalChain
from qts.data.historical.csv_format import EXPECTED_HISTORICAL_COLUMNS
from qts.data.sessions import RegularSessionWindow
from qts.strategy_sdk import Strategy


def _write_chain_json(
    path: Path,
    *,
    root: str = "GC",
    timezone_id: str = "US/Eastern",
    trading_hours: str = "20100606:1800-20100607:1700;20100607:1800-20100608:1700",
) -> None:
    payload = {
        "root": root,
        "market": "COMEX_FUT",
        "currency": "USD",
        "timezone_id": timezone_id,
        "tick_size": "0.1",
        "multiplier": "100",
        "trading_calendar": "CMES",
        "trading_hours": trading_hours,
        "contracts": [
            {
                "local_symbol": "GCQ0",
                "expiry": "2010-08-27T00:00:00+00:00",
                "first_notice_day": "2010-07-30",
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_csv(path: Path, *, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index, row in enumerate(rows):
            full = {
                "ts_event": row["ts_event"],
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": str(index + 1),
                "open": row["close"],
                "high": row["close"],
                "low": row["close"],
                "close": row["close"],
                "volume": str(row.get("volume", "100")),
                "symbol": row.get("symbol", "GCQ0"),
            }
            writer.writerow(full)


def _write_data_config(path: Path, *, historical_root: Path) -> None:
    path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
      bars_file_template: "{{root_lower}}.csv"
      chain_file_template: "{{root}}.json"
  catalogs:
    research:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )


def _write_backtest_config(
    path: Path,
    *,
    data_config_path: Path,
    start_iso: str,
    end_iso: str,
) -> None:
    path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research
roots: [GC]
symbols: [GC]
start: "{start_iso}"
end: "{end_iso}"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.anchor.test_session_window_excludes_break_bars:NoopStrategy"
risk_config:
  max_notional: "100000000"
roll_policy:
  enabled: true
  method: highest_volume
""",
        encoding="utf-8",
    )


class NoopStrategy(Strategy):
    """Bare strategy used so the backtest pipeline can instantiate something."""


def test_regular_session_window_marks_break_timestamps_as_none() -> None:
    """Unit-level: the session window must reject break-time timestamps."""
    window = RegularSessionWindow(
        exchange_timezone="US/Eastern",
        open_time=time(18, 0),
        close_time=time(17, 0),
    )
    # 17:30 ET on 2010-06-07 — in the daily break between sessions.
    from datetime import UTC, datetime

    break_ts = datetime(2010, 6, 7, 21, 30, tzinfo=UTC)  # 17:30 EDT
    assert window.session_id_for_timestamp(break_ts) is None
    # 18:01 ET on 2010-06-07 → session closes 2010-06-08.
    in_session_ts = datetime(2010, 6, 7, 22, 1, tzinfo=UTC)
    assert window.session_id_for_timestamp(in_session_ts) == date(2010, 6, 8).isoformat()


def test_chain_exposes_session_window_from_trading_hours(tmp_path: Path) -> None:
    """``HistoricalChain.session_window()`` parses trading_hours + timezone_id."""
    chain_path = tmp_path / "GC.json"
    _write_chain_json(chain_path)
    chain = HistoricalChain.load(chain_path)
    window = chain.session_window()
    assert window is not None
    assert window.exchange_timezone == "US/Eastern"
    assert window.open_time == time(18, 0)
    assert window.close_time == time(17, 0)


def test_backtest_pipeline_excludes_break_bars_for_overnight_future(
    tmp_path: Path,
) -> None:
    """End-to-end: GC bars whose timestamps fall in the ET 17-18 break are dropped.

    The ``BarTimeGridSynthesizer`` also no longer bridges the break,
    because the bars on either side carry distinct session_ids.
    """
    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir(parents=True)
    _write_chain_json(historical_root / "chains" / "GC.json")

    # Build a tape with 5 minutes pre-break, 5 minutes inside the break,
    # then 5 minutes after the break opens.
    rows: list[dict[str, Any]] = []
    pre_break_starts = ["20:55", "20:56", "20:57", "20:58", "20:59"]  # ET 16:55-16:59
    break_starts = ["21:00", "21:15", "21:30", "21:45", "21:59"]  # ET 17:00-17:59
    post_break_starts = ["22:00", "22:01", "22:02", "22:03", "22:04"]  # ET 18:00-18:04
    for index, hhmm in enumerate(pre_break_starts + break_starts + post_break_starts):
        hour, minute = hhmm.split(":")
        rows.append(
            {
                "ts_event": f"2010-06-07T{hour}:{minute}:00.000000000Z",
                "close": f"{1200 + index}.0",
                "symbol": "GCQ0",
                "volume": "100",
            }
        )
    _write_csv(historical_root / "data" / "gc.csv", rows=rows)

    data_config_path = tmp_path / "historical.local.yaml"
    _write_data_config(data_config_path, historical_root=historical_root)
    backtest_config_path = tmp_path / "backtest.yaml"
    _write_backtest_config(
        backtest_config_path,
        data_config_path=data_config_path,
        start_iso="2010-06-07T20:55:00Z",
        end_iso="2010-06-07T22:05:00Z",
    )

    pipeline = BacktestPipeline.from_yaml(backtest_config_path)
    _, bundle = pipeline.build_engine()
    bars = list(bundle.bars)

    pre_break = [b for b in bars if b.start_time.hour < 21]
    inside_break = [b for b in bars if b.start_time.hour == 21]
    post_break = [b for b in bars if b.start_time.hour >= 22]

    # No bar inside the daily break.
    assert inside_break == [], (
        f"break-time bars must be excluded; got {[b.start_time.isoformat() for b in inside_break]}"
    )
    # Pre- and post-break bars survive (counts depend on synthesis fill within each session).
    assert pre_break, "pre-break bars must be emitted"
    assert post_break, "post-break bars must be emitted"
    # Session_id must reflect exchange-local close date, not UTC date.
    pre_session_ids = {b.session_id for b in pre_break}
    post_session_ids = {b.session_id for b in post_break}
    assert pre_session_ids == {"2010-06-07"}, f"pre-break session: {pre_session_ids}"
    assert post_session_ids == {"2010-06-08"}, f"post-break session: {post_session_ids}"
    # No synthetic bridging across the break — synthetic bars only appear
    # within a single session (none expected for this dense fixture).
    cross_session_synthetic = [b for b in bars if b.is_synthetic and 21 <= b.start_time.hour < 22]
    assert cross_session_synthetic == [], (
        f"synthetic bars must not bridge sessions; got {cross_session_synthetic}"
    )


@pytest.fixture(autouse=True)
def _reset_module_path() -> Iterator[None]:
    """Ensure the test module is importable by class path for load_strategy."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    yield
