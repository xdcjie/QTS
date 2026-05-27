"""Daily byte-offset indexes for ordered historical CSV files."""

from __future__ import annotations

import json
from bisect import bisect_right
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.data.historical.csv_format import parse_historical_ts_event

DEFAULT_TIMESTAMP_COLUMN = "ts_event"
INDEX_VERSION = 1


def write_historical_csv_index(
    csv_path: str | Path,
    *,
    output_path: str | Path | None = None,
    timestamp_column: str = DEFAULT_TIMESTAMP_COLUMN,
) -> Path:
    """Write a daily sidecar index for an ordered historical CSV file."""

    source_path = Path(csv_path)
    target_path = (
        Path(output_path)
        if output_path is not None
        else source_path.with_suffix(source_path.suffix + ".index.json")
    )
    timestamp_column = _required_text(timestamp_column, "timestamp_column")
    buckets: list[dict[str, Any]] = []
    previous_timestamp: datetime | None = None
    current_bucket_date: str | None = None
    row_count = 0

    with source_path.open("rb") as handle:
        header_line = handle.readline()
        if not header_line:
            raise ValueError(f"historical CSV is empty: {source_path}")
        header_offset = handle.tell()
        columns = _columns(header_line)
        if timestamp_column not in columns:
            raise ValueError(f"timestamp column not found: {timestamp_column}")
        timestamp_index = columns.index(timestamp_column)

        while True:
            row_offset = handle.tell()
            line = handle.readline()
            if not line:
                break
            if not line.strip():
                continue
            timestamp = parse_historical_ts_event(_field(line, timestamp_index))
            if previous_timestamp is not None and timestamp < previous_timestamp:
                raise ValueError(
                    "historical CSV timestamps are out of order: "
                    f"{timestamp.isoformat()} before {previous_timestamp.isoformat()}"
                )
            bucket_date = timestamp.date().isoformat()
            if bucket_date != current_bucket_date:
                buckets.append(
                    {
                        "date": bucket_date,
                        "offset": row_offset,
                        "row_index": row_count,
                    }
                )
                current_bucket_date = bucket_date
            previous_timestamp = timestamp
            row_count += 1

    payload = {
        "buckets": buckets,
        "granularity": "day",
        "header_offset": header_offset,
        "row_count": row_count,
        "source_path": str(source_path),
        "timestamp_column": timestamp_column,
        "version": INDEX_VERSION,
    }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return target_path


def indexed_start_offset(
    csv_path: str | Path,
    *,
    start: datetime | None,
    timestamp_column: str = DEFAULT_TIMESTAMP_COLUMN,
    header_offset: int,
) -> int | None:
    """Return the indexed row offset for the UTC day containing ``start``."""

    if start is None:
        return None
    index_path = Path(csv_path).with_suffix(Path(csv_path).suffix + ".index.json")
    if not index_path.exists():
        return None
    payload = _read_payload(index_path)
    if payload.get("version") != INDEX_VERSION:
        return None
    if payload.get("granularity") != "day":
        return None
    if payload.get("timestamp_column") != timestamp_column:
        return None
    if payload.get("header_offset") != header_offset:
        return None
    buckets = payload.get("buckets")
    if not isinstance(buckets, list) or not buckets:
        return None
    start_date = _start_date(start)
    dates: list[str] = []
    offsets: list[int] = []
    for bucket in buckets:
        if not isinstance(bucket, Mapping):
            return None
        date_value = bucket.get("date")
        offset_value = bucket.get("offset")
        if not isinstance(date_value, str):
            return None
        if isinstance(offset_value, bool) or not isinstance(offset_value, int):
            return None
        dates.append(date_value)
        offsets.append(offset_value)
    index = bisect_right(dates, start_date) - 1
    if index < 0:
        return offsets[0]
    return offsets[index]


def _columns(header_line: bytes) -> tuple[str, ...]:
    return tuple(column.strip() for column in header_line.decode("utf-8").strip().split(","))


def _field(line: bytes, index: int) -> str:
    fields = line.decode("utf-8").rstrip("\r\n").split(",")
    if index >= len(fields):
        raise ValueError("historical CSV row has fewer columns than header")
    return fields[index]


def _read_payload(index_path: Path) -> Mapping[str, Any]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"historical CSV index must be a JSON object: {index_path}")
    return payload


def _required_text(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _start_date(start: datetime) -> str:
    if start.tzinfo is None or start.utcoffset() is None:
        return start.date().isoformat()
    return start.astimezone(UTC).date().isoformat()


__all__ = [
    "DEFAULT_TIMESTAMP_COLUMN",
    "indexed_start_offset",
    "write_historical_csv_index",
]
