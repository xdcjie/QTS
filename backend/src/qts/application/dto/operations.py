"""Operational application DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RuntimeStateDTO:
    """Stable runtime state response."""

    state: str


@dataclass(frozen=True, slots=True)
class RuntimeCommandResultDTO:
    """Stable runtime command result for API and CLI callers."""

    command_id: str
    idempotency_key: str
    status: str
    evidence: Mapping[str, object] = field(default_factory=dict)
    failure_reason: str | None = None
    reason_code: str | None = None

    def __post_init__(self) -> None:
        """Normalize evidence into an immutable DTO payload."""
        if not self.command_id.strip():
            raise ValueError("command_id must not be empty")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if not self.status.strip():
            raise ValueError("status must not be empty")
        object.__setattr__(self, "evidence", dict(self.evidence))


@dataclass(frozen=True, slots=True)
class KillSwitchCommandDTO:
    """Stable kill-switch activation request."""

    scope: str
    reason: str
    scope_id: str | None = None

    def __post_init__(self) -> None:
        """Validate that scope and reason are set and scope_id is present when scoped."""
        if not self.scope.strip():
            raise ValueError("scope must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        if self.scope != "global" and (self.scope_id is None or not self.scope_id.strip()):
            raise ValueError("scope_id is required for non-global scope")


@dataclass(frozen=True, slots=True)
class KillSwitchStateDTO:
    """Stable kill-switch state response."""

    scope: str
    active: bool
    reason: str
    scope_id: str | None = None


@dataclass(frozen=True, slots=True)
class OperatorStatusFieldDTO:
    """One timestamped operator dashboard field."""

    value: object
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate timestamp evidence for this operator status field."""
        if self.timestamp.tzinfo is None:
            raise ValueError("operator status field timestamp must be timezone-aware")
        object.__setattr__(self, "value", self._freeze_value(self.value))

    @classmethod
    def _freeze_value(cls, value: object) -> object:
        if isinstance(value, Mapping):
            return {str(key): cls._freeze_value(item) for key, item in value.items()}
        if isinstance(value, list | tuple):
            return tuple(cls._freeze_value(item) for item in value)
        return value


@dataclass(frozen=True, slots=True)
class OperatorAlertDTO:
    """Timestamped operator dashboard alert."""

    code: str
    severity: str
    message: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate alert evidence."""
        if not self.code.strip():
            raise ValueError("alert code must not be empty")
        if not self.severity.strip():
            raise ValueError("alert severity must not be empty")
        if not self.message.strip():
            raise ValueError("alert message must not be empty")
        if self.timestamp.tzinfo is None:
            raise ValueError("alert timestamp must be timezone-aware")


@dataclass(frozen=True, slots=True)
class OperatorDashboardStatusDTO:
    """Application-owned operator dashboard status DTO."""

    runtime_state: OperatorStatusFieldDTO
    runtime_mode: OperatorStatusFieldDTO
    order_permission_state: OperatorStatusFieldDTO
    broker_connection_state: OperatorStatusFieldDTO
    market_data_permission_state: OperatorStatusFieldDTO
    stale_subscriptions: OperatorStatusFieldDTO
    open_orders: OperatorStatusFieldDTO
    positions: OperatorStatusFieldDTO
    cash_snapshot: OperatorStatusFieldDTO
    kill_switch_state: OperatorStatusFieldDTO
    last_reconciliation_result: OperatorStatusFieldDTO
    unresolved_broker_callbacks: OperatorStatusFieldDTO
    event_sink: OperatorStatusFieldDTO
    latest_manifest: OperatorStatusFieldDTO
    alerts: tuple[OperatorAlertDTO, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Add required alerts for operator-visible problem states."""
        alerts = list(self.alerts)
        existing_codes = {alert.code for alert in alerts}
        for alert in self._required_alerts():
            if alert.code not in existing_codes:
                alerts.append(alert)
        object.__setattr__(self, "alerts", tuple(alerts))

    def _required_alerts(self) -> tuple[OperatorAlertDTO, ...]:
        alerts: list[OperatorAlertDTO] = []
        if self._has_items(self.stale_subscriptions.value):
            alerts.append(
                OperatorAlertDTO(
                    code="STALE_DATA",
                    severity="warning",
                    message="One or more market data subscriptions are stale.",
                    timestamp=self.stale_subscriptions.timestamp,
                )
            )
        if self._has_reconciliation_drift(self.last_reconciliation_result.value):
            alerts.append(
                OperatorAlertDTO(
                    code="RECONCILIATION_DRIFT",
                    severity="critical",
                    message="Last reconciliation reported drift.",
                    timestamp=self.last_reconciliation_result.timestamp,
                )
            )
        if self._has_items(self.unresolved_broker_callbacks.value):
            alerts.append(
                OperatorAlertDTO(
                    code="UNRESOLVED_BROKER_CALLBACKS",
                    severity="critical",
                    message="Broker callbacks remain unresolved.",
                    timestamp=self.unresolved_broker_callbacks.timestamp,
                )
            )
        return tuple(alerts)

    @staticmethod
    def _has_items(value: object) -> bool:
        return isinstance(value, tuple | list) and len(value) > 0

    @staticmethod
    def _has_reconciliation_drift(value: object) -> bool:
        if not isinstance(value, Mapping):
            return False
        status = value.get("status")
        drift_count = value.get("drift_count")
        return status in {"drift", "drift_detected"} or (
            isinstance(drift_count, int) and drift_count > 0
        )

    @property
    def fields(self) -> Mapping[str, OperatorStatusFieldDTO]:
        """Return dashboard fields keyed by response name."""
        return {
            "runtime_state": self.runtime_state,
            "runtime_mode": self.runtime_mode,
            "order_permission_state": self.order_permission_state,
            "broker_connection_state": self.broker_connection_state,
            "market_data_permission_state": self.market_data_permission_state,
            "stale_subscriptions": self.stale_subscriptions,
            "open_orders": self.open_orders,
            "positions": self.positions,
            "cash_snapshot": self.cash_snapshot,
            "kill_switch_state": self.kill_switch_state,
            "last_reconciliation_result": self.last_reconciliation_result,
            "unresolved_broker_callbacks": self.unresolved_broker_callbacks,
            "event_sink": self.event_sink,
            "latest_manifest": self.latest_manifest,
        }


__all__ = [
    "KillSwitchCommandDTO",
    "KillSwitchStateDTO",
    "OperatorAlertDTO",
    "OperatorDashboardStatusDTO",
    "OperatorStatusFieldDTO",
    "RuntimeCommandResultDTO",
    "RuntimeStateDTO",
]
