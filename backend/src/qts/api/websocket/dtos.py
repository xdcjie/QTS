"""Public WebSocket event DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class StreamEventType(StrEnum):
    """Public WebSocket event types emitted by runtime operations."""

    RUNTIME_STATE_CHANGED = "runtime_state_changed"
    COMMAND_ACCEPTED = "command_accepted"
    COMMAND_COMPLETED = "command_completed"
    RISK_EVENT = "risk_event"
    ORDER_EVENT = "order_event"
    ACCOUNT_EVENT = "account_event"
    RECONCILIATION_EVENT = "reconciliation_event"
    MARKET_DATA_STATUS_EVENT = "market_data_status_event"


@dataclass(frozen=True, slots=True)
class StreamEventDTO:
    """Public stream event DTO."""

    event_type: str
    event_time: datetime
    payload: dict[str, str]
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")


__all__ = ["StreamEventDTO", "StreamEventType"]
