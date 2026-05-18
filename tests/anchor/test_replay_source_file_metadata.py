"""Anchor: ReplayMarketDataSource file metadata stays correct + fast.

Domain fact: ``DatasetMetadata.row_count`` and ``content_hash`` must
remain deterministic across optimization passes. The OPT-70 fix
collapses two full-file scans (csv.DictReader for row count +
streaming SHA-256 for hash) into a single binary pass that counts
newlines while updating the hasher. This anchor locks the values so
future tweaks can't silently change provenance.

Owner: ``qts.data.sources.replay_market_data_source.ReplayMarketDataSource``
file-metadata helpers.

Forbidden shortcut: returning approximate row counts; using two
passes through the file when one suffices; basing the content hash
on anything other than the raw bytes.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest
from qts.data.historical.csv_format import EXPECTED_HISTORICAL_COLUMNS
from qts.data.sources.replay_market_data_source import ReplayMarketDataSource


def _write_fixture(path: Path, *, row_count: int) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index in range(row_count):
            writer.writerow(
                {
                    "ts_event": f"2026-01-02T14:{index % 60:02d}:00.000000000Z",
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": "1",
                    "open": "100.0",
                    "high": "100.0",
                    "low": "100.0",
                    "close": "100.0",
                    "volume": "1",
                    "symbol": "AAA",
                }
            )


@pytest.mark.parametrize("row_count", [0, 1, 7, 1000])
def test_file_row_count_matches_csv_dictreader(tmp_path: Path, row_count: int) -> None:
    """Optimized row count must equal what csv.DictReader would yield."""
    path = tmp_path / "rows.csv"
    _write_fixture(path, row_count=row_count)

    with path.open(encoding="utf-8", newline="") as handle:
        reference = sum(1 for _ in csv.DictReader(handle))
    assert ReplayMarketDataSource._file_row_count(path) == reference == row_count


def test_file_content_hash_matches_streaming_sha256(tmp_path: Path) -> None:
    """The content hash must remain a stable SHA-256 of the raw file bytes."""
    path = tmp_path / "rows.csv"
    _write_fixture(path, row_count=50)

    reference = hashlib.sha256(path.read_bytes()).hexdigest()
    assert ReplayMarketDataSource._file_content_hash(path) == f"sha256:{reference}"


def test_file_row_count_handles_missing_trailing_newline(tmp_path: Path) -> None:
    """Files without a trailing newline still report the correct row count."""
    path = tmp_path / "no_trailing.csv"
    _write_fixture(path, row_count=3)
    # Strip trailing newline if present.
    raw = path.read_bytes()
    if raw.endswith(b"\n"):
        path.write_bytes(raw.rstrip(b"\n"))

    with path.open(encoding="utf-8", newline="") as handle:
        reference = sum(1 for _ in csv.DictReader(handle))
    assert ReplayMarketDataSource._file_row_count(path) == reference == 3
