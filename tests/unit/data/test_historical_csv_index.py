from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.data.historical.csv_index import indexed_start_offset, write_historical_csv_index


def test_build_historical_csv_index_records_daily_row_offsets(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(
        path,
        [
            _row("2026-01-02T14:30:00.000000000Z"),
            _row("2026-01-02T14:31:00.000000000Z"),
            _row("2026-01-03T14:30:00.000000000Z"),
        ],
    )

    index_path = write_historical_csv_index(path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))

    assert payload["granularity"] == "day"
    assert [bucket["date"] for bucket in payload["buckets"]] == ["2026-01-02", "2026-01-03"]
    assert (
        indexed_start_offset(
            path,
            start=datetime(2026, 1, 3, tzinfo=UTC),
            timestamp_column="ts_event",
            header_offset=payload["header_offset"],
        )
        == payload["buckets"][1]["offset"]
    )
    assert payload["row_count"] == 3


def test_build_historical_csv_index_rejects_out_of_order_timestamps(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(
        path,
        [
            _row("2026-01-03T14:30:00.000000000Z"),
            _row("2026-01-02T14:30:00.000000000Z"),
        ],
    )

    with pytest.raises(ValueError, match="out of order"):
        write_historical_csv_index(path)


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(timestamp: str) -> dict[str, str]:
    return {
        "ts_event": timestamp,
        "rtype": "33",
        "publisher_id": "1",
        "instrument_id": "123",
        "open": "2000.0",
        "high": "2000.0",
        "low": "2000.0",
        "close": "2000.0",
        "volume": "2",
        "symbol": "GCQ0",
    }
