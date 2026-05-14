"""Operational error taxonomy for runtime events, logs, and API payloads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class OperationalErrorCode(StrEnum):
    """Standard reason codes for runtime incidents."""

    MARKET_DATA_PERMISSION_ERROR = "MARKET_DATA_PERMISSION_ERROR"
    MARKET_DATA_STALE = "MARKET_DATA_STALE"
    BROKER_DISCONNECTED = "BROKER_DISCONNECTED"
    ORDER_REJECTED_BY_RISK = "ORDER_REJECTED_BY_RISK"
    ORDER_REJECTED_BY_BROKER = "ORDER_REJECTED_BY_BROKER"
    EXECUTION_REPORT_UNRESOLVED = "EXECUTION_REPORT_UNRESOLVED"
    RECONCILIATION_DRIFT = "RECONCILIATION_DRIFT"
    EVENT_STORE_WRITE_FAILED = "EVENT_STORE_WRITE_FAILED"


@dataclass(frozen=True, slots=True)
class RuntimeErrorReason:
    """Structured runtime error reason suitable for event payloads."""

    code: OperationalErrorCode
    message: str
    detail: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message must not be empty")

    def to_payload(self) -> dict[str, object]:
        """Return a normalized payload with the standard reason code."""
        return {
            "reason_code": self.code.value,
            "message": self.message,
            "detail": dict(self.detail),
        }


__all__ = ["OperationalErrorCode", "RuntimeErrorReason"]
