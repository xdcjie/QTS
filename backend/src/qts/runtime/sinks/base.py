"""Runtime event sink contracts.

RuntimeEventSink consumes normalized runtime events. Mode-specific sinks may
turn those events into artifacts, logs, metrics, or operational streams.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

from qts.core.ids import (
    AccountId,
    CausationId,
    CorrelationId,
    EventId,
    InstrumentId,
    RuntimeRunId,
    StrategyId,
)


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """A normalized event emitted by the shared runtime."""

    SCHEMA_VERSION: ClassVar[str] = "1"

    kind: str
    payload: dict[str, Any]
    event_id: EventId | None = None
    run_id: RuntimeRunId | None = None
    mode: str | None = None
    sequence_no: int | None = None
    ts_event: datetime | None = None
    ts_ingest: datetime | None = None
    account_id: AccountId | None = None
    strategy_id: StrategyId | None = None
    instrument_id: InstrumentId | None = None
    correlation_id: CorrelationId | None = None
    causation_id: CausationId | None = None
    execution_environment: str | None = None
    payload_schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Normalize timestamps and payload shape."""
        object.__setattr__(self, "payload", dict(self.payload))
        if self.sequence_no is not None and self.sequence_no <= 0:
            raise ValueError("sequence_no must be positive")
        if self.ts_ingest is None:
            object.__setattr__(self, "ts_ingest", datetime.now(UTC))

    def to_envelope(self, *, sequence_no: int | None = None) -> dict[str, Any]:
        """Serialize the runtime event envelope."""
        effective_sequence_no = self.sequence_no if self.sequence_no is not None else sequence_no
        return {
            "event_id": self._id_value(self.event_id),
            "run_id": self._id_value(self.run_id),
            "mode": self.mode,
            "sequence_no": effective_sequence_no,
            "ts_event": self.ts_event.isoformat() if self.ts_event is not None else None,
            "ts_ingest": self.ts_ingest.isoformat() if self.ts_ingest is not None else None,
            "account_id": self._id_value(self.account_id),
            "strategy_id": self._id_value(self.strategy_id),
            "instrument_id": self._id_value(self.instrument_id),
            "correlation_id": self._id_value(self.correlation_id),
            "causation_id": self._id_value(self.causation_id),
            "kind": self.kind,
            "execution_environment": self.execution_environment,
            "payload_schema_version": self.payload_schema_version,
            "payload": self.payload,
        }

    @staticmethod
    def _id_value(identifier: object) -> str | None:
        """Return the string value for typed IDs."""
        if identifier is None:
            return None
        return str(identifier)


class RuntimeEventSink:
    """Boundary for consuming normalized runtime events."""

    def write(self, event: RuntimeEvent) -> object:
        """Write one runtime event."""
        raise NotImplementedError


__all__ = ["RuntimeEvent", "RuntimeEventSink"]
