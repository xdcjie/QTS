"""Public WebSocket event DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class StreamEventDTO:
    event_type: str
    event_time: datetime
    payload: dict[str, str]
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")


__all__ = ["StreamEventDTO"]
