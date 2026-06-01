"""Research timestamp providers.

Research orchestration needs deterministic timestamps for replayable evidence,
but the timestamp source itself must be injected at the workflow boundary rather
than hardcoded throughout promotion and audit code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


class _ResearchClock(Protocol):
    """Clock contract used by research orchestration and evidence writers."""

    def now(self, *, offset_seconds: int = 0) -> datetime:
        """Return a timezone-aware UTC timestamp."""


@dataclass(frozen=True, slots=True)
class DeterministicResearchClock:
    """Clock that returns a fixed start plus caller-provided offsets."""

    start: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None:
            raise ValueError("DeterministicResearchClock start must be timezone-aware")
        object.__setattr__(self, "start", self.start.astimezone(UTC))

    def now(self, *, offset_seconds: int = 0) -> datetime:
        return self.start + timedelta(seconds=offset_seconds)


class _SystemResearchClock:
    """Clock backed by the current UTC wall time."""

    def now(self, *, offset_seconds: int = 0) -> datetime:
        return datetime.now(UTC) + timedelta(seconds=offset_seconds)


ResearchClock = _ResearchClock


def system_research_clock() -> ResearchClock:
    """Return the default wall-clock research timestamp provider."""

    return _SystemResearchClock()


__all__ = ["DeterministicResearchClock", "ResearchClock", "system_research_clock"]
