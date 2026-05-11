"""Local file-backed market data store skeleton.

The public class is named for the intended storage boundary. This MVP uses
JSON lines partitions so it does not add an optional parquet engine dependency
to the domain test path.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


class ParquetMarketDataStore:
    """File-backed bar store partitioned by instrument, timeframe, and date."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def write_bars(self, bars: Iterable[Bar]) -> None:
        grouped: dict[Path, list[Bar]] = {}
        for bar in bars:
            grouped.setdefault(self._path_for(bar), []).append(bar)
        for path, items in grouped.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            existing = list(self._read_file(path)) if path.exists() else []
            merged = sorted(
                [*existing, *items],
                key=lambda item: (item.start_time, item.end_time),
            )
            with path.open("w", encoding="utf-8") as handle:
                for bar in merged:
                    handle.write(json.dumps(self._bar_to_json(bar), sort_keys=True))
                    handle.write("\n")

    def read_bars(
        self,
        *,
        instrument_id: InstrumentId,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> tuple[Bar, ...]:
        base = self._root / instrument_id.value / timeframe
        if not base.exists():
            return ()
        bars: list[Bar] = []
        for path in sorted(base.glob("*.jsonl")):
            bars.extend(self._read_file(path))
        return tuple(
            bar
            for bar in sorted(bars, key=lambda item: (item.start_time, item.end_time))
            if start <= bar.start_time and bar.end_time <= end
        )

    def _path_for(self, bar: Bar) -> Path:
        return (
            self._root
            / bar.instrument_id.value
            / bar.timeframe
            / f"{bar.start_time.date().isoformat()}.jsonl"
        )

    def _read_file(self, path: Path) -> tuple[Bar, ...]:
        with path.open(encoding="utf-8") as handle:
            return tuple(self._bar_from_json(json.loads(line)) for line in handle if line.strip())

    @staticmethod
    def _bar_to_json(bar: Bar) -> dict[str, Any]:
        return {
            "instrument_id": bar.instrument_id.value,
            "start_time": bar.start_time.isoformat(),
            "end_time": bar.end_time.isoformat(),
            "timeframe": bar.timeframe,
            "session_id": bar.session_id,
            "open": str(bar.open),
            "high": str(bar.high),
            "low": str(bar.low),
            "close": str(bar.close),
            "volume": str(bar.volume),
            "vwap": None if bar.vwap is None else str(bar.vwap),
            "open_interest": None if bar.open_interest is None else str(bar.open_interest),
            "trade_count": bar.trade_count,
            "is_complete": bar.is_complete,
            "is_partial": bar.is_partial,
        }

    @staticmethod
    def _bar_from_json(payload: dict[str, Any]) -> Bar:
        return Bar(
            instrument_id=InstrumentId(str(payload["instrument_id"])),
            start_time=datetime.fromisoformat(str(payload["start_time"])),
            end_time=datetime.fromisoformat(str(payload["end_time"])),
            timeframe=str(payload["timeframe"]),
            session_id=str(payload["session_id"]),
            open=Decimal(str(payload["open"])),
            high=Decimal(str(payload["high"])),
            low=Decimal(str(payload["low"])),
            close=Decimal(str(payload["close"])),
            volume=Decimal(str(payload["volume"])),
            vwap=None if payload["vwap"] is None else Decimal(str(payload["vwap"])),
            open_interest=(
                None if payload["open_interest"] is None else Decimal(str(payload["open_interest"]))
            ),
            trade_count=None if payload["trade_count"] is None else int(payload["trade_count"]),
            is_complete=bool(payload["is_complete"]),
            is_partial=bool(payload["is_partial"]),
        )


__all__ = ["ParquetMarketDataStore"]
