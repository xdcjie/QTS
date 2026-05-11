"""Shared historical CSV format parsing helpers."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

EXPECTED_HISTORICAL_COLUMNS = (
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
)


@dataclass(frozen=True, slots=True)
class HistoricalCsvSchema:
    """Mapping from framework OHLCV semantics to concrete CSV columns."""

    timestamp: str = "ts_event"
    symbol: str = "symbol"
    open: str = "open"
    high: str = "high"
    low: str = "low"
    close: str = "close"
    volume: str = "volume"
    instrument_id: str | None = "instrument_id"

    def __post_init__(self) -> None:
        required = (
            self.timestamp,
            self.symbol,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
        )
        if any(not item.strip() for item in required):
            raise ValueError("historical CSV schema required fields must not be empty")
        if self.instrument_id is not None and not self.instrument_id.strip():
            raise ValueError("historical CSV schema instrument_id must not be empty")

    @property
    def required_columns(self) -> tuple[str, ...]:
        return (
            self.timestamp,
            self.symbol,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume,
        )

    def validate_columns(self, columns: Iterable[str]) -> tuple[str, ...]:
        present = tuple(columns)
        missing = tuple(column for column in self.required_columns if column not in present)
        if missing:
            raise ValueError(f"historical CSV columns missing required fields: {','.join(missing)}")
        return present

    def column_indices(self, columns: Iterable[str]) -> dict[str, int]:
        present = self.validate_columns(columns)
        index = {name: position for position, name in enumerate(present)}
        return {
            "timestamp": index[self.timestamp],
            "symbol": index[self.symbol],
            "open": index[self.open],
            "high": index[self.high],
            "low": index[self.low],
            "close": index[self.close],
            "volume": index[self.volume],
        }


DEFAULT_HISTORICAL_CSV_SCHEMA = HistoricalCsvSchema()


def validate_historical_csv_columns(
    columns: tuple[str, ...],
    *,
    schema: HistoricalCsvSchema | None = None,
) -> None:
    """Validate historical CSV columns against the configured schema."""

    if schema is not None and schema != DEFAULT_HISTORICAL_CSV_SCHEMA:
        schema.validate_columns(columns)
        return
    if columns != EXPECTED_HISTORICAL_COLUMNS:
        raise ValueError(
            "historical CSV columns must be "
            f"{','.join(EXPECTED_HISTORICAL_COLUMNS)}; got {','.join(columns)}"
        )


def parse_historical_ts_event(value: str) -> datetime:
    """Parse a historical CSV UTC timestamp, accepting nanosecond text input."""

    text = value.removesuffix("Z")
    suffix = "+00:00" if value.endswith("Z") else ""
    if "." in text:
        prefix, rest = text.split(".", maxsplit=1)
        fraction = rest[:6].ljust(6, "0")
        text = f"{prefix}.{fraction}"
    parsed = datetime.fromisoformat(f"{text}{suffix}")
    if parsed.tzinfo is None:
        raise ValueError("ts_event must be timezone-aware")
    return parsed.astimezone(UTC)


def historical_timeframe_delta(timeframe: str) -> timedelta:
    """Return the duration represented by a supported historical timeframe."""

    if timeframe == "1m":
        return timedelta(minutes=1)
    if timeframe.endswith("m"):
        return timedelta(minutes=int(timeframe[:-1]))
    if timeframe.endswith("s"):
        return timedelta(seconds=int(timeframe[:-1]))
    if timeframe.endswith("h"):
        return timedelta(hours=int(timeframe[:-1]))
    raise ValueError(f"unsupported historical timeframe: {timeframe}")


__all__ = [
    "DEFAULT_HISTORICAL_CSV_SCHEMA",
    "EXPECTED_HISTORICAL_COLUMNS",
    "HistoricalCsvSchema",
    "historical_timeframe_delta",
    "parse_historical_ts_event",
    "validate_historical_csv_columns",
]
