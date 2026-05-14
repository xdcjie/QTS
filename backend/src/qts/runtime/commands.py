"""Runtime command model for API and CLI control surfaces."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from qts.core.time import require_aware_datetime


class RuntimeCommandType(StrEnum):
    """Operator command types accepted by runtime control boundaries."""

    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    ACTIVATE_KILL_SWITCH = "activate_kill_switch"
    DEACTIVATE_KILL_SWITCH = "deactivate_kill_switch"
    RECONCILE = "reconcile"
    SNAPSHOT = "snapshot"
    ENTER_OBSERVATION = "enter_observation"
    EXIT_OBSERVATION = "exit_observation"


class RuntimeCommandResultStatus(StrEnum):
    """Execution status for a runtime command result."""

    ACCEPTED = "accepted"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class RuntimeCommandStreamEvent:
    """Runtime command event suitable for API/CLI stream adapters."""

    event_type: str
    event_time: datetime
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise ValueError("event_type must not be empty")
        require_aware_datetime(self.event_time, name="event_time")
        object.__setattr__(self, "payload", dict(self.payload))


@dataclass(frozen=True, slots=True)
class RuntimeCommand:
    """Auditable command envelope issued by API or CLI callers."""

    command_id: str
    command_type: RuntimeCommandType
    idempotency_key: str
    operator_id: str
    reason: str | None = None
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate command identity and operator evidence."""
        self._require_text(self.command_id, "command_id")
        self._require_text(self.idempotency_key, "idempotency_key")
        self._require_text(self.operator_id, "operator_id")
        object.__setattr__(self, "payload", dict(self.payload))
        if self.reason is not None:
            self._require_text(self.reason, "reason")

    def accepted_event(self, *, accepted_at: datetime) -> RuntimeCommandStreamEvent:
        """Return a stream event proving this command was accepted."""

        require_aware_datetime(accepted_at, name="accepted_at")
        return RuntimeCommandStreamEvent(
            event_type="command_accepted",
            event_time=accepted_at,
            payload={
                "command_id": self.command_id,
                "idempotency_key": self.idempotency_key,
                "command_type": self.command_type.value,
                "operator_id": self.operator_id,
                **dict(self.payload),
            },
        )

    @staticmethod
    def _require_text(value: str, name: str) -> None:
        if not value.strip():
            raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class RuntimeCommandResult:
    """Stable command result with audit evidence and failure reason."""

    command_id: str
    idempotency_key: str
    accepted_at: datetime
    result_status: RuntimeCommandResultStatus
    completed_at: datetime | None = None
    evidence: Mapping[str, object] = field(default_factory=dict)
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        """Validate command result evidence."""
        RuntimeCommand._require_text(self.command_id, "command_id")
        RuntimeCommand._require_text(self.idempotency_key, "idempotency_key")
        require_aware_datetime(self.accepted_at, name="accepted_at")
        if self.completed_at is not None:
            require_aware_datetime(self.completed_at, name="completed_at")
        object.__setattr__(self, "evidence", dict(self.evidence))
        if self.result_status is RuntimeCommandResultStatus.REJECTED:
            if self.failure_reason is None or not self.failure_reason.strip():
                raise ValueError("failure_reason is required for rejected commands")
        elif self.failure_reason is not None and not self.failure_reason.strip():
            raise ValueError("failure_reason must not be empty when provided")

    def completed_event(self, command: RuntimeCommand) -> RuntimeCommandStreamEvent:
        """Return a stream event proving this command reached a terminal result."""

        if command.command_id != self.command_id:
            raise ValueError("command_id mismatch between command and result")
        event_time = self.completed_at or self.accepted_at
        payload = {
            "command_id": self.command_id,
            "idempotency_key": self.idempotency_key,
            "command_type": command.command_type.value,
            "result_status": self.result_status.value,
            **dict(self.evidence),
        }
        if self.failure_reason is not None:
            payload["failure_reason"] = self.failure_reason
        return RuntimeCommandStreamEvent(
            event_type="command_completed",
            event_time=event_time,
            payload=payload,
        )


class RuntimeCommandBus:
    """Route runtime commands through a handler with idempotent results."""

    def __init__(self, *, handler: Callable[[RuntimeCommand], RuntimeCommandResult]) -> None:
        """Perform __init__."""
        self._handler = handler
        self._results: dict[tuple[RuntimeCommandType, str], RuntimeCommandResult] = {}

    def submit(self, command: RuntimeCommand) -> RuntimeCommandResult:
        """Submit a command once per idempotency key."""
        result_key = (command.command_type, command.idempotency_key)
        if result_key in self._results:
            return self._results[result_key]
        result = self._handler(command)
        self._results[result_key] = result
        return result


__all__ = [
    "RuntimeCommand",
    "RuntimeCommandBus",
    "RuntimeCommandResult",
    "RuntimeCommandResultStatus",
    "RuntimeCommandStreamEvent",
    "RuntimeCommandType",
]
