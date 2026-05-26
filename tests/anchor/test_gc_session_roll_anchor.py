import hashlib
import json
from datetime import UTC, datetime, time
from decimal import Decimal
from pathlib import Path

from qts.data.historical.chains import HistoricalChain
from qts.data.sessions import RegularSessionWindow
from qts.registry.future_roll import HighestVolumeFutureContractSelector

from tests.support.historical_session_roll_anchor import (
    HistoricalSessionRollSelection,
    summarize_historical_session_rolls,
)

GC_CSV_PATH = Path("historical/data/gc.csv")
GC_CHAIN_PATH = Path("historical/chains/GC.json")
GC_SESSION_WINDOW = RegularSessionWindow(
    exchange_timezone="US/Eastern",
    open_time=time(18, 0),
    close_time=time(17, 0),
)
EXPECTED_ROLL_SUMMARY_SHA = "6fa8f08a32b51a880d42e98deb8d537d6b9623e44370ddc9d2e848b2fd1e0637"


def _decimal_to_anchor_text(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return format(value, "f")


def _session_roll_anchor_payload(
    row: HistoricalSessionRollSelection,
) -> dict[str, str | int]:
    return {
        "session_id": row.session_id,
        "selected_symbol": row.selected_symbol,
        "selected_instrument_id": str(row.selected_instrument_id),
        "selected_volume": _decimal_to_anchor_text(row.selected_volume),
        "selected_bar_count": row.selected_bar_count,
    }


def test_gc_session_id_uses_exchange_time_half_open_session() -> None:
    assert (
        GC_SESSION_WINDOW.session_id_for_timestamp(datetime(2010, 6, 6, 22, 0, tzinfo=UTC))
        == "2010-06-07"
    )
    assert (
        GC_SESSION_WINDOW.session_id_for_timestamp(datetime(2010, 6, 7, 20, 59, tzinfo=UTC))
        == "2010-06-07"
    )
    assert (
        GC_SESSION_WINDOW.session_id_for_timestamp(datetime(2010, 6, 7, 21, 0, tzinfo=UTC)) is None
    )


def test_gc_historical_session_roll_anchor_matches_full_csv() -> None:
    chain = HistoricalChain.load(GC_CHAIN_PATH)

    summary = summarize_historical_session_rolls(
        GC_CSV_PATH,
        chain,
        timeframe="1m",
        contract_selector=HighestVolumeFutureContractSelector(),
        session_window=GC_SESSION_WINDOW,
    )
    sessions = [_session_roll_anchor_payload(row) for row in summary.rows]
    summary_payload = json.dumps(
        {"sessions": sessions, "excluded": summary.stats.to_payload()},
        sort_keys=True,
        separators=(",", ":"),
    )
    actual_sha = hashlib.sha256(summary_payload.encode("utf-8")).hexdigest()

    assert actual_sha == EXPECTED_ROLL_SUMMARY_SHA
    assert len(sessions) == 4105
    assert summary.stats.to_payload() == {
        "rows_seen": 15291573,
        "spreads_excluded": 5147856,
        "unsupported_contracts_excluded": 0,
        "outside_session_rows_excluded": 24640,
    }
    assert len(sessions) > 0
    assert sessions[0] == {
        "session_id": "2010-06-07",
        "selected_symbol": "GCQ0",
        "selected_instrument_id": "FUTURE.CME.GC.GCQ0",
        "selected_volume": "136281",
        "selected_bar_count": 1349,
    }
    assert sessions[-1] == {
        "session_id": "2026-05-22",
        "selected_symbol": "GCM6",
        "selected_instrument_id": "FUTURE.CME.GC.GCM6",
        "selected_volume": "76108",
        "selected_bar_count": 1329,
    }


def test_gc_session_roll_anchor_support_stays_out_of_production_csv_dataset() -> None:
    import qts.data.historical.csv_dataset as csv_dataset

    assert not hasattr(csv_dataset, "summarize_historical_session_rolls")
