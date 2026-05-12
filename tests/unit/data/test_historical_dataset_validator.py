from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.historical.validation import HistoricalDatasetValidator
from qts.data.validation_report import DataValidationIssueCode
from qts.registry.symbol_resolution import StaticSymbolResolver


def _write_rows(path: Path, rows: Sequence[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "ts_event",
                "rtype",
                "publisher_id",
                "instrument_id",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "symbol",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)


def test_dataset_validator_rejects_spread_and_invalid_ohlc(tmp_path: Path) -> None:
    path = tmp_path / "gc.csv"
    _write_rows(
        path,
        [
            {
                "ts_event": "2026-01-02T14:30:00.000000000Z",
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": "123",
                "symbol": "GCQ0",
                "open": "2000",
                "high": "1999",
                "low": "1998",
                "close": "2000",
                "volume": "2",
            },
            {
                "ts_event": "2026-01-02T14:31:00.000000000Z",
                "symbol": "GCN0-GCQ0",
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": "123",
                "open": "2001",
                "high": "2002",
                "low": "2001",
                "close": "2001.5",
                "volume": "1",
            },
            {
                "ts_event": "2026-01-02T14:32:00.000000000Z",
                "symbol": "GCM0",
                "rtype": "33",
                "publisher_id": "1",
                "instrument_id": "123",
                "open": "2001",
                "high": "2002",
                "low": "2001",
                "close": "2001.5",
                "volume": "1",
            },
        ],
    )
    resolver = StaticSymbolResolver(
        {
            "GCQ0": InstrumentId("FUTURE.CME.GC.GCQ0"),
            "GCM0": InstrumentId("FUTURE.CME.GC.GCM0"),
        }
    )

    result = HistoricalDatasetValidator().validate_sample(
        path,
        symbol_resolver=resolver,
        sample_rows=3,
        timeframe="1m",
    )

    assert result.stats.rows_seen == 3
    assert result.stats.spreads_excluded == 1
    assert result.stats.bars_emitted == 1
    assert {issue.code for issue in result.report.issues} >= {
        DataValidationIssueCode.INVALID_OHLC,
        DataValidationIssueCode.EXCLUDED_SPREAD,
    }
