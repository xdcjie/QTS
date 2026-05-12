"""Audit event model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Operational or trading audit event."""

    event_type: str
    event_time: datetime
    actor: str
    message: str
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")
        if not self.actor.strip():
            raise ValueError("actor must not be empty")
        if not self.message.strip():
            raise ValueError("message must not be empty")


__all__ = ["AuditEvent"]
