"""Runtime event sink contracts.

RuntimeEventSink consumes normalized runtime events. Mode-specific sinks may
turn those events into artifacts, logs, metrics, or operational streams.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """A normalized event emitted by the shared runtime."""

    kind: str
    payload: dict[str, Any]


class RuntimeEventSink:
    """Boundary placeholder for consuming normalized runtime events."""


__all__ = ["RuntimeEvent", "RuntimeEventSink"]
