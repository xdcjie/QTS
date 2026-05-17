"""Audit sink protocol and built-in sinks.

Auth decisions and other operationally-significant security events flow
through this layer. The sink is intentionally separate from
``RuntimeEventSink``: audit events have different retention,
different consumers, and survive runtime restarts.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from typing import IO, Protocol

from qts.observability.audit import AuditEvent


class AuditSink(Protocol):
    """Write one audit event."""

    def write(self, event: AuditEvent) -> None:
        """Write an audit event to the underlying destination."""
        ...


class InMemoryAuditSink:
    """In-process buffer used by tests."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def write(self, event: AuditEvent) -> None:
        """Append the event to the in-memory buffer."""
        self._events.append(event)

    def events(self) -> tuple[AuditEvent, ...]:
        """Return a snapshot of buffered events."""
        return tuple(self._events)

    def clear(self) -> None:
        """Reset the buffer."""
        self._events.clear()


class StderrJsonAuditSink:
    """Default sink — writes one JSON line per event to stderr."""

    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream = stream or sys.stderr

    def write(self, event: AuditEvent) -> None:
        """Write a single JSON line representing the event."""
        payload = asdict(event)
        payload["event_time"] = event.event_time.isoformat()
        self._stream.write(json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n")
        self._stream.flush()


def now() -> datetime:
    """Return an aware UTC timestamp for audit events."""
    return datetime.now(tz=UTC)


__all__ = ["AuditSink", "InMemoryAuditSink", "StderrJsonAuditSink", "now"]
