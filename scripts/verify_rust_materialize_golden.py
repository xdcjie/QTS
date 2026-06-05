#!/usr/bin/env python3
"""Python/Rust golden diff for Phase 1 historical CSV materialization."""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from qts.data.historical.csv_format import (
    EXPECTED_HISTORICAL_COLUMNS,
    parse_historical_ts_event,
)
from qts.data.historical.csv_index import write_historical_csv_index

ROOT = "GC"
CHECKED_TIMEFRAMES = (
    "1m",
    "2m",
    "3m",
    "5m",
    "10m",
    "15m",
    "30m",
    "1h",
    "4h",
    "1d",
)
EXCHANGE_TZ = ZoneInfo("US/Eastern")
SESSION_CLOSE_DATE = date(2026, 1, 6)
INSTRUMENTS = (
    ("FUTURE.CME.GC.GCM26", "GCM26"),
    ("FUTURE.CME.SI.SIN26", "SIN26"),
)


@dataclass(frozen=True, slots=True)
class SourceRow:
    ts_event: datetime
    rtype: str
    publisher_id: str
    instrument_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    symbol: str


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    cargo = shutil.which("cargo")
    if cargo is None:
        print("cargo not found", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="qts-rs-golden-") as tmp:
        work = Path(tmp)
        checked_cases = []
        _run_golden_case(
            repo_root=repo_root,
            cargo=cargo,
            work=work,
            case_name="fixture",
            root=ROOT,
            rows=_fixture_rows(),
        )
        checked_cases.append("fixture")

        for root in ("GC", "SI"):
            real_source = repo_root / "historical" / "data" / root / "1m.csv"
            if real_source.exists():
                _run_golden_case(
                    repo_root=repo_root,
                    cargo=cargo,
                    work=work,
                    case_name=f"historical_{root.lower()}",
                    root=root,
                    rows=_read_real_slice(real_source),
                )
                checked_cases.append(f"historical_{root.lower()}")

    print(
        json.dumps(
            {
                "status": "ok",
                "cases": checked_cases,
                "checked": [f"{timeframe}.csv" for timeframe in CHECKED_TIMEFRAMES]
                + [f"{timeframe}.csv.index.json" for timeframe in CHECKED_TIMEFRAMES],
                "reference": "python",
                "candidate": "rust",
            },
            sort_keys=True,
        )
    )
    return 0


def _run_golden_case(
    *,
    repo_root: Path,
    cargo: str,
    work: Path,
    case_name: str,
    root: str,
    rows: list[SourceRow],
) -> None:
    if not rows:
        raise ValueError(f"golden case has no source rows: {case_name}")
    case_dir = work / case_name
    source_csv = case_dir / "source" / f"{root.lower()}.csv"
    python_dir = case_dir / "python"
    rust_dir = case_dir / "rust"
    source_csv.parent.mkdir(parents=True)
    python_dir.mkdir(parents=True)
    rust_dir.mkdir(parents=True)
    _write_source_csv(source_csv, rows)
    _write_python_references(python_dir, source_csv, rows)

    subprocess.run(
        [
            cargo,
            "run",
            "-q",
            "-p",
            "qts-cli",
            "--",
            "materialize",
            "--root",
            root,
            "--source-csv",
            str(source_csv),
            "--output-dir",
            str(rust_dir),
            "--timeframes",
            ",".join(CHECKED_TIMEFRAMES),
            "--exchange-timezone",
            "US/Eastern",
            "--session-open",
            "18:00",
            "--session-close",
            "17:00",
        ],
        cwd=repo_root / "rust",
        check=True,
    )

    for timeframe in CHECKED_TIMEFRAMES:
        python_csv = python_dir / f"{timeframe}.csv"
        rust_csv = rust_dir / f"{timeframe}.csv"
        rust_index = rust_csv.with_suffix(rust_csv.suffix + ".index.json")
        python_index = python_csv.with_suffix(python_csv.suffix + ".index.json")
        _assert_bytes_equal(f"{case_name}:{timeframe}.csv", python_csv, rust_csv)
        _assert_index_equal(python_index, rust_index)


def _fixture_rows() -> list[SourceRow]:
    start = datetime(2026, 1, 6, 14, 30, tzinfo=UTC)
    values_by_symbol = {
        "GCM26": [
            ("2000.00", "2001.00", "1999.00", "2000.50", "10"),
            ("2000.50", "2002.00", "2000.00", "2001.00", "11"),
            ("2001.00", "2003.00", "2000.50", "2002.00", "12"),
            ("2002.00", "2004.00", "2001.00", "2003.00", "13"),
            ("2003.00", "2004.50", "2002.00", "2004.00", "14"),
        ],
        "SIN26": [
            ("25.000", "25.050", "24.950", "25.010", "20"),
            ("25.010", "25.060", "24.990", "25.020", "21"),
            ("25.020", "25.080", "25.000", "25.040", "22"),
            ("25.040", "25.090", "25.010", "25.070", "23"),
            ("25.070", "25.120", "25.030", "25.100", "24"),
        ],
    }
    rows: list[SourceRow] = []
    for index in range(5):
        for instrument_id, symbol in INSTRUMENTS:
            open_, high, low, close, volume = values_by_symbol[symbol][index]
            rows.append(
                SourceRow(
                    ts_event=start + timedelta(minutes=index),
                    rtype="",
                    publisher_id="",
                    instrument_id=instrument_id,
                    open=Decimal(open_),
                    high=Decimal(high),
                    low=Decimal(low),
                    close=Decimal(close),
                    volume=Decimal(volume),
                    symbol=symbol,
                )
            )
    return rows


def _read_real_slice(path: Path) -> list[SourceRow]:
    rows: list[SourceRow] = []
    bucket_start: datetime | None = None
    bucket_end: datetime | None = None
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for record in reader:
            timestamp = parse_historical_ts_event(record["ts_event"])
            if bucket_start is None:
                bucket_start = _clock_bucket_start(timestamp, minutes=5)
                bucket_end = bucket_start + timedelta(minutes=5)
            if bucket_end is not None and timestamp >= bucket_end:
                break
            rows.append(
                SourceRow(
                    ts_event=timestamp,
                    rtype=record["rtype"],
                    publisher_id=record["publisher_id"],
                    instrument_id=record["instrument_id"],
                    open=Decimal(record["open"]),
                    high=Decimal(record["high"]),
                    low=Decimal(record["low"]),
                    close=Decimal(record["close"]),
                    volume=Decimal(record["volume"]),
                    symbol=record["symbol"],
                )
            )
    return rows


def _write_source_csv(path: Path, rows: list[SourceRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(EXPECTED_HISTORICAL_COLUMNS)
        for row in rows:
            writer.writerow(
                [
                    _timestamp_text(row.ts_event),
                    row.rtype,
                    row.publisher_id,
                    row.instrument_id,
                    _decimal_text(row.open),
                    _decimal_text(row.high),
                    _decimal_text(row.low),
                    _decimal_text(row.close),
                    _decimal_text(row.volume),
                    row.symbol,
                ]
            )


def _write_python_references(
    output_dir: Path,
    source_csv: Path,
    rows: list[SourceRow],
) -> None:
    one_minute = output_dir / "1m.csv"
    shutil.copyfile(source_csv, one_minute)
    write_historical_csv_index(one_minute)
    for timeframe in CHECKED_TIMEFRAMES:
        if timeframe == "1m":
            continue
        path = output_dir / f"{timeframe}.csv"
        if timeframe == "1d":
            _write_python_reference_1d(path, rows)
        else:
            _write_python_reference_clock(path, rows, minutes=_timeframe_minutes(timeframe))
        write_historical_csv_index(path)


def _write_python_reference_clock(path: Path, rows: list[SourceRow], *, minutes: int) -> None:
    _write_aggregate_rows(path, _aggregate_clock_fixture_rows(rows, minutes=minutes))


def _write_python_reference_1d(path: Path, rows: list[SourceRow]) -> None:
    session_start, _session_end = _session_interval_for(_session_close_date_for(rows[0].ts_event))
    _write_aggregate_rows(path, _aggregate_fixture_rows(rows, start_time=session_start))


def _write_aggregate_rows(path: Path, rows: list[SourceRow]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(EXPECTED_HISTORICAL_COLUMNS)
        for row in rows:
            writer.writerow(
                [
                    _timestamp_text(row.ts_event),
                    "",
                    "",
                    row.instrument_id,
                    _decimal_text(row.open),
                    _decimal_text(row.high),
                    _decimal_text(row.low),
                    _decimal_text(row.close),
                    _decimal_text(row.volume),
                    row.symbol,
                ]
            )


def _aggregate_fixture_rows(
    rows: list[SourceRow],
    *,
    start_time: datetime,
) -> list[SourceRow]:
    grouped: dict[str, list[SourceRow]] = {}
    for row in rows:
        grouped.setdefault(row.instrument_id, []).append(row)
    output: list[SourceRow] = []
    for instrument_id, group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: row.ts_event)
        first = ordered[0]
        last = ordered[-1]
        output.append(
            SourceRow(
                ts_event=start_time,
                rtype="",
                publisher_id="",
                instrument_id=instrument_id,
                open=first.open,
                high=max(row.high for row in ordered),
                low=min(row.low for row in ordered),
                close=last.close,
                volume=sum((row.volume for row in ordered), Decimal("0")),
                symbol=first.symbol,
            )
        )
    return sorted(output, key=lambda row: (row.ts_event, row.instrument_id, row.symbol))


def _aggregate_clock_fixture_rows(rows: list[SourceRow], *, minutes: int) -> list[SourceRow]:
    grouped: dict[tuple[datetime, str], list[SourceRow]] = {}
    for row in rows:
        bucket_start = _clock_bucket_start(row.ts_event, minutes=minutes)
        grouped.setdefault((bucket_start, row.instrument_id), []).append(row)
    output: list[SourceRow] = []
    for (bucket_start, _instrument_id), group in sorted(grouped.items()):
        output.extend(_aggregate_fixture_rows(group, start_time=bucket_start))
    return sorted(output, key=lambda row: (row.ts_event, row.instrument_id, row.symbol))


def _timeframe_minutes(timeframe: str) -> int:
    match timeframe:
        case "2m":
            return 2
        case "3m":
            return 3
        case "5m":
            return 5
        case "10m":
            return 10
        case "15m":
            return 15
        case "30m":
            return 30
        case "1h":
            return 60
        case "4h":
            return 240
        case _:
            raise ValueError(f"unsupported golden timeframe: {timeframe}")


def _clock_bucket_start(value: datetime, *, minutes: int) -> datetime:
    local = value.astimezone(EXCHANGE_TZ)
    local_midnight = datetime.combine(local.date(), time.min, tzinfo=EXCHANGE_TZ)
    bucket_seconds = minutes * 60
    elapsed_seconds = int((value.astimezone(UTC) - local_midnight.astimezone(UTC)).total_seconds())
    bucket_offset = elapsed_seconds // bucket_seconds * bucket_seconds
    return local_midnight.astimezone(UTC) + timedelta(seconds=bucket_offset)


def _session_close_date_for(value: datetime) -> date:
    local = value.astimezone(EXCHANGE_TZ)
    if local.time() >= time(18, 0):
        return local.date() + timedelta(days=1)
    return local.date()


def _session_interval_for(session_close_date: date) -> tuple[datetime, datetime]:
    session_open = datetime.combine(
        session_close_date - timedelta(days=1),
        time(18, 0),
        tzinfo=EXCHANGE_TZ,
    )
    session_close = datetime.combine(
        session_close_date,
        time(17, 0),
        tzinfo=EXCHANGE_TZ,
    )
    return session_open.astimezone(UTC), session_close.astimezone(UTC)


def _timestamp_text(value: datetime) -> str:
    utc_value = value.astimezone(UTC)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S") + ".000000000Z"


def _decimal_text(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


def _assert_bytes_equal(label: str, expected: Path, actual: Path) -> None:
    if not actual.exists():
        raise AssertionError(f"missing Rust output for {label}: {actual}")
    expected_bytes = expected.read_bytes()
    actual_bytes = actual.read_bytes()
    if expected_bytes != actual_bytes:
        raise AssertionError(
            f"{label} mismatch\n"
            f"expected: {expected.read_text(encoding='utf-8')}\n"
            f"actual: {actual.read_text(encoding='utf-8')}"
        )


def _assert_index_equal(expected: Path, actual: Path) -> None:
    if not actual.exists():
        raise AssertionError(f"missing Rust index output: {actual}")
    expected_payload = json.loads(expected.read_text(encoding="utf-8"))
    actual_payload = json.loads(actual.read_text(encoding="utf-8"))
    expected_payload.pop("source_path", None)
    actual_payload.pop("source_path", None)
    if expected_payload != actual_payload:
        raise AssertionError(
            "index mismatch\n"
            f"expected: {json.dumps(expected_payload, sort_keys=True)}\n"
            f"actual: {json.dumps(actual_payload, sort_keys=True)}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
