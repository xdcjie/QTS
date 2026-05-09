"""Timeframe model: CLOCK for <1d, SESSION for 1d."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum


class AlignmentMode(StrEnum):
    """How bars for a timeframe align to time."""

    CLOCK = "clock"
    SESSION = "session"


_SUPPORTED_CLOCK_DURATIONS = {
    "5s": timedelta(seconds=5),
    "1m": timedelta(minutes=1),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
}


@dataclass(frozen=True, slots=True)
class Timeframe:
    """Bar timeframe with explicit alignment semantics."""

    value: str
    duration: timedelta | None
    alignment: AlignmentMode

    @classmethod
    def parse(cls, value: str) -> Timeframe:
        normalized = value.strip().lower()
        if normalized in _SUPPORTED_CLOCK_DURATIONS:
            return cls(
                value=normalized,
                duration=_SUPPORTED_CLOCK_DURATIONS[normalized],
                alignment=AlignmentMode.CLOCK,
            )
        if normalized == "1d":
            return cls(value=normalized, duration=None, alignment=AlignmentMode.SESSION)
        raise ValueError(f"unsupported timeframe: {value}")

    def __str__(self) -> str:
        return self.value


__all__ = ["AlignmentMode", "Timeframe"]
