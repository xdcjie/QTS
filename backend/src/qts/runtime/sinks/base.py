"""Runtime event sink contracts.

RuntimeEventSink consumes normalized runtime events. Mode-specific sinks may
turn those events into artifacts, logs, metrics, or operational streams.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
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
from qts.reporting.base import PLATFORM_BASELINE_VERSION
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class RuntimeEvent:
    """A normalized event emitted by the shared runtime."""

    SCHEMA_VERSION: ClassVar[str] = "1"

    kind: str
    payload: dict[str, Any]
    event_id: EventId | None = None
    parent_event_id: EventId | None = None
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
        if self._requires_correlation_id() and self.correlation_id is None:
            raise ValueError("correlation_id is required for order, risk, and fill events")
        if self._requires_client_order_id():
            client_order_id = self.payload.get("client_order_id")
            if not isinstance(client_order_id, str) or not client_order_id.strip():
                raise ValueError("client_order_id is required for order and fill events")
        if self._requires_causation_id() and self.causation_id is None:
            raise ValueError("causation_id is required for fill events")
        if self.sequence_no is not None and self.sequence_no <= 0:
            raise ValueError("sequence_no must be positive")
        if self.ts_ingest is None:
            object.__setattr__(self, "ts_ingest", datetime.now(UTC))
        if self.ts_event is None:
            object.__setattr__(self, "ts_event", self.ts_ingest)

    def to_envelope(self, *, sequence_no: int | None = None) -> dict[str, Any]:
        """Serialize the runtime event envelope."""
        effective_sequence_no = self.sequence_no if self.sequence_no is not None else sequence_no
        return {
            "event_id": self._id_value(self.event_id),
            "parent_event_id": self._id_value(self.parent_event_id),
            "run_id": self._id_value(self.run_id),
            "mode": self.mode,
            "runtime_mode": self.mode,
            "platform_baseline_version": PLATFORM_BASELINE_VERSION,
            "sequence_no": effective_sequence_no,
            "ts_event": self.ts_event.isoformat() if self.ts_event is not None else None,
            "ts_ingest": self.ts_ingest.isoformat() if self.ts_ingest is not None else None,
            "account_id": self._id_value(self.account_id),
            "strategy_id": self._id_value(self.strategy_id),
            "instrument_id": self._id_value(self.instrument_id),
            "correlation_id": self._id_value(self.correlation_id),
            "causation_id": self._id_value(self.causation_id),
            "kind": self.kind,
            "event_type": self.kind,
            "execution_environment": self.execution_environment,
            "payload_schema_version": self.payload_schema_version,
            "payload": self.payload,
        }

    def _requires_correlation_id(self) -> bool:
        normalized = self.kind.lower()
        trace_prefixes = (
            "runtime.order",
            "order.",
            "order_",
            "runtime.risk",
            "risk.",
            "risk_",
            "runtime.fill",
            "fill.",
            "fill_",
            "runtime.broker_report",
            "broker_report",
            "runtime.broker_rejected",
            "broker_rejected",
        )
        return any(normalized.startswith(prefix) for prefix in trace_prefixes)

    def _requires_client_order_id(self) -> bool:
        normalized = self.kind.lower()
        trace_prefixes = (
            "runtime.order",
            "order.",
            "order_",
            "runtime.broker_report",
            "broker_report",
            "runtime.fill",
            "fill.",
            "fill_",
        )
        return any(normalized.startswith(prefix) for prefix in trace_prefixes)

    def _requires_causation_id(self) -> bool:
        normalized = self.kind.lower()
        return normalized.startswith(("runtime.fill", "fill.", "fill_"))

    @staticmethod
    def require_canonical_envelope(row: dict[str, Any]) -> None:
        """Require identity, mode, and sequence fields before persistence."""
        required_fields = (
            "run_id",
            "runtime_mode",
            "sequence_no",
            "event_id",
            "payload_schema_version",
            "platform_baseline_version",
        )
        for field_name in required_fields:
            value = row.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ValueError(f"{field_name} is required for runtime event envelope")

    @staticmethod
    def _id_value(identifier: object) -> str | None:
        """Return the string value for typed IDs."""
        if identifier is None:
            return None
        return str(identifier)


@dataclass(frozen=True, slots=True)
class RuntimeEventWriteResult:
    """Metadata produced when a runtime event is appended."""

    sequence_no: int
    event_hash: str


@dataclass(frozen=True, slots=True)
class RuntimeEventContext:
    """Run-scoped defaults applied to every emitted runtime event."""

    run_id: RuntimeRunId
    mode: RuntimeMode | str
    execution_environment: object | None = None
    account_id: AccountId | None = None
    strategy_id: StrategyId | None = None

    def __post_init__(self) -> None:
        """Normalize enum-backed runtime context fields."""
        mode = RuntimeMode.from_value(self.mode)
        object.__setattr__(self, "mode", mode.value)
        if self.execution_environment is not None:
            execution_environment = self._normalize_label(self.execution_environment)
            if not execution_environment:
                raise ValueError("execution_environment must not be empty")
            object.__setattr__(self, "execution_environment", execution_environment)

    def apply(self, event: RuntimeEvent, *, sequence_no: int) -> RuntimeEvent:
        """Return an event with run context and a monotonic sequence number."""
        if sequence_no <= 0:
            raise ValueError("sequence_no must be positive")
        mode = str(self.mode)
        execution_environment = (
            None if self.execution_environment is None else str(self.execution_environment)
        )
        self._reject_conflicting("run_id", event.run_id, self.run_id)
        self._reject_conflicting("mode", event.mode, mode)
        self._reject_conflicting(
            "execution_environment",
            event.execution_environment,
            execution_environment,
        )
        self._reject_conflicting("account_id", event.account_id, self.account_id)
        self._reject_conflicting("strategy_id", event.strategy_id, self.strategy_id)
        if event.sequence_no is not None and event.sequence_no != sequence_no:
            raise ValueError("event sequence_no does not match sink sequence")
        return replace(
            event,
            event_id=event.event_id or EventId(f"{self.run_id.value}-{sequence_no:012d}"),
            run_id=event.run_id or self.run_id,
            mode=event.mode or mode,
            sequence_no=sequence_no,
            account_id=event.account_id or self.account_id,
            strategy_id=event.strategy_id or self.strategy_id,
            execution_environment=event.execution_environment or execution_environment,
        )

    @staticmethod
    def _reject_conflicting(field_name: str, event_value: object, context_value: object) -> None:
        if event_value is None or context_value is None:
            return
        if str(event_value) != str(context_value):
            raise ValueError(f"event {field_name} conflicts with runtime context")

    @staticmethod
    def _normalize_label(value: object) -> str:
        raw_value = value.value if isinstance(value, Enum) else value
        normalized = str(raw_value).strip().lower().replace("-", "_")
        if not normalized:
            raise ValueError("runtime context labels must not be empty")
        return normalized


class RuntimeEventSink:
    """Boundary for consuming normalized runtime events."""

    def write(self, event: RuntimeEvent) -> object:
        """Write one runtime event."""
        raise NotImplementedError


__all__ = [
    "RuntimeEvent",
    "RuntimeEventContext",
    "RuntimeEventSink",
    "RuntimeEventWriteResult",
]
