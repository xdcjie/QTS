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
    """Boundary for consuming normalized runtime events."""

    def write(self, event: RuntimeEvent) -> object:
        """Write one runtime event."""
        raise NotImplementedError


__all__ = ["RuntimeEvent", "RuntimeEventSink"]
