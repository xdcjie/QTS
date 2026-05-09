from __future__ import annotations

from datetime import UTC, datetime


def test_structured_log_preserves_trace_fields_and_redacts_secrets() -> None:
    from qts.core.ids import AccountId, CorrelationId, EventId, OrderId
    from qts.domain.events import EventMetadata
    from qts.observability.logging import build_log_record

    record = build_log_record(
        level="info",
        message="order submitted",
        metadata=EventMetadata(
            event_id=EventId("evt-001"),
            event_type="order.submitted",
            event_time=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            account_id=AccountId("acct-001"),
            order_id=OrderId("ord-001"),
            correlation_id=CorrelationId("corr-001"),
        ),
        fields={
            "broker_order_id": "ibkr-001",
            "password": "do-not-log",
            "api_token": "do-not-log",
        },
    )

    assert record["level"] == "info"
    assert record["message"] == "order submitted"
    assert record["event_id"] == "evt-001"
    assert record["correlation_id"] == "corr-001"
    assert record["account_id"] == "acct-001"
    assert record["order_id"] == "ord-001"
    assert record["broker_order_id"] == "ibkr-001"
    assert record["password"] == "[REDACTED]"
    assert record["api_token"] == "[REDACTED]"
