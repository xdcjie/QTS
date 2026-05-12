"""Map historical CSV rows into domain bars."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC
from decimal import Decimal

from qts.data.historical.csv_format import (
    DEFAULT_HISTORICAL_CSV_SCHEMA,
    HistoricalCsvSchema,
    historical_timeframe_delta,
    parse_historical_ts_event,
)
from qts.domain.market_data import Bar
from qts.registry.symbol_resolution import SourceSymbolResolver


@dataclass(frozen=True, slots=True)
class HistoricalCsvRowMapper:
    """Map one validated CSV row to an OHLCV bar."""

    timeframe: str = "1m"
    schema: HistoricalCsvSchema = DEFAULT_HISTORICAL_CSV_SCHEMA

    def to_bar(self, row: Mapping[str, str], *, symbol_resolver: SourceSymbolResolver) -> Bar:
        """Map a mapped row dict into a typed bar."""

        start_time = parse_historical_ts_event(self._field(row, "timestamp"))
        end_time = start_time + historical_timeframe_delta(self.timeframe)
        symbol = self._field(row, "symbol")
        open_, high, low, close, volume = self.extract_ohlcv(row)
        return Bar(
            instrument_id=symbol_resolver.instrument_id_for_symbol(symbol),
            start_time=start_time,
            end_time=end_time,
            timeframe=self.timeframe,
            session_id=start_time.astimezone(UTC).date().isoformat(),
            open=open_,
            high=high,
            low=low,
            close=close,
            volume=volume,
            is_complete=True,
        )

    def extract_ohlcv(
        self, row: Mapping[str, str]
    ) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        """Extract and validate OHLCV fields from a mapped row."""

        return self._parse_ohlcv_values(
            open_value=self._field(row, "open"),
            high_value=self._field(row, "high"),
            low_value=self._field(row, "low"),
            close_value=self._field(row, "close"),
            volume_value=self._field(row, "volume"),
        )

    def _field(self, row: Mapping[str, str], semantic_name: str) -> str:
        """Perform _field."""
        return row[self.schema.resolve_column(semantic_name)]

    @staticmethod
    def _parse_ohlcv_values(
        *,
        open_value: str,
        high_value: str,
        low_value: str,
        close_value: str,
        volume_value: str,
    ) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
        """Perform _parse_ohlcv_values."""
        open_ = Decimal(open_value)
        high = Decimal(high_value)
        low = Decimal(low_value)
        close = Decimal(close_value)
        volume = Decimal(volume_value)
        if high < max(open_, close):
            raise ValueError("high must be greater than or equal to open and close")
        if low > min(open_, close):
            raise ValueError("low must be less than or equal to open and close")
        if low > high:
            raise ValueError("low must be less than or equal to high")
        if volume < Decimal("0"):
            raise ValueError("volume must be non-negative")
        return open_, high, low, close, volume


__all__ = ["HistoricalCsvRowMapper"]
