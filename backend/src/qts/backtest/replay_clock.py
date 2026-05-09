"""Deterministic replay clock."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from qts.core.time import require_aware_datetime


class ReplayClock:
    """Advances over a fixed sorted sequence of timestamps."""

    def __init__(self, timestamps: Iterable[datetime]) -> None:
        ordered = tuple(sorted(timestamps))
        for timestamp in ordered:
            require_aware_datetime(timestamp, name="timestamp")
        self._timestamps = ordered
        self._index = 0
        self.current_time: datetime | None = None

    @property
    def done(self) -> bool:
        return self._index >= len(self._timestamps)

    def advance(self) -> datetime | None:
        if self.done:
            return None
        self.current_time = self._timestamps[self._index]
        self._index += 1
        return self.current_time


__all__ = ["ReplayClock"]
