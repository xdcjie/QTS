from __future__ import annotations

from datetime import UTC, datetime


def test_audit_event_represents_risk_rejection_and_order_transition() -> None:
    from qts.observability import AuditEvent

    risk = AuditEvent(
        event_type="risk.rejected",
        event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
        actor="RiskEngine",
        message="MAX_NOTIONAL_EXCEEDED",
        correlation_id="corr-001",
    )
    order = AuditEvent(
        event_type="order.transition",
        event_time=datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
        actor="OrderManagerActor",
        message="accepted -> filled",
        correlation_id="corr-001",
    )

    assert risk.correlation_id == order.correlation_id
