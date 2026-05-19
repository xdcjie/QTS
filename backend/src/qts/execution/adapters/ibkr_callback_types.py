"""Shared types and helpers for IBKR callback normalization components."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from qts.domain.orders import ExecutionReport, ExecutionReportStatus
from qts.execution.broker import normalize_broker_status


@dataclass(frozen=True, slots=True)
class IbkrExecutionReport:
    """IBKR execution report shape before normalization."""

    report_id: str
    broker_order_id: str
    status: ExecutionReportStatus
    filled_quantity: Decimal = Decimal("0")
    fill_price: Decimal | None = None
    fill_id: str | None = None
    commission: Decimal = Decimal("0")
    fill_time: datetime | None = None


@dataclass(frozen=True, slots=True)
class IbkrOrderCallbackEvent:
    """Audit event for normalized IBKR order callback handling."""

    kind: str
    report_id: str | None = None
    broker_order_id: str | None = None
    execution_id: str | None = None
    reason: str | None = None
    expected_account: str | None = None
    observed_account: str | None = None

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        for field_name, value in (
            ("report_id", self.report_id),
            ("broker_order_id", self.broker_order_id),
            ("execution_id", self.execution_id),
            ("reason", self.reason),
            ("expected_account", self.expected_account),
            ("observed_account", self.observed_account),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be empty when provided")


def mask_account_id(account_id: str) -> str:
    """Mask an account ID for audit logging."""
    if len(account_id) <= 4:
        return "*" * len(account_id)
    return f"{account_id[:2]}{'*' * max(len(account_id) - 4, 1)}{account_id[-2:]}"


def record_callback_event(
    events: list[IbkrOrderCallbackEvent],
    kind: str,
    *,
    report_id: str | None = None,
    broker_order_id: str | None = None,
    execution_id: str | None = None,
    reason: str | None = None,
    expected_account: str | None = None,
    observed_account: str | None = None,
) -> None:
    """Append an audit event to the shared callback events list."""
    events.append(
        IbkrOrderCallbackEvent(
            kind=kind,
            report_id=report_id,
            broker_order_id=broker_order_id,
            execution_id=execution_id,
            reason=reason,
            expected_account=expected_account,
            observed_account=observed_account,
        )
    )


def record_account_mismatch_event(
    events: list[IbkrOrderCallbackEvent],
    account_id: str,
    *,
    report_id: str | None,
    broker_order_id: str | None,
    observed_account: str,
    execution_id: str | None = None,
) -> None:
    """Append an account-mismatch quarantine audit event."""
    record_callback_event(
        events,
        "ibkr_account_callback_quarantined",
        report_id=report_id,
        broker_order_id=broker_order_id,
        execution_id=execution_id,
        reason="wrong_account",
        expected_account=mask_account_id(account_id),
        observed_account=mask_account_id(observed_account),
    )


def normalize_ibkr_execution_report(report: IbkrExecutionReport) -> ExecutionReport:
    """Normalize an IBKR execution report to the internal execution report."""
    return ExecutionReport(
        report_id=report.report_id,
        broker_order_id=report.broker_order_id,
        status=normalize_broker_status(report.status),
        filled_quantity=report.filled_quantity,
        fill_price=report.fill_price,
        fill_id=report.fill_id,
        commission=report.commission,
        fill_time=report.fill_time,
    )


__all__ = [
    "IbkrExecutionReport",
    "IbkrOrderCallbackEvent",
    "mask_account_id",
    "normalize_ibkr_execution_report",
    "record_account_mismatch_event",
    "record_callback_event",
]
