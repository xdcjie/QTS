from __future__ import annotations


def test_runtime_error_reason_payload_uses_standard_reason_code() -> None:
    from qts.observability.errors import OperationalErrorCode, RuntimeErrorReason

    reason = RuntimeErrorReason(
        code=OperationalErrorCode.ORDER_REJECTED_BY_BROKER,
        message="Broker rejected order",
        detail={"broker_order_id": "broker-1"},
    )

    assert reason.to_payload() == {
        "reason_code": "ORDER_REJECTED_BY_BROKER",
        "message": "Broker rejected order",
        "detail": {"broker_order_id": "broker-1"},
    }


def test_error_taxonomy_includes_core_runtime_incident_codes() -> None:
    from qts.observability.errors import OperationalErrorCode

    assert {code.value for code in OperationalErrorCode} >= {
        "MARKET_DATA_PERMISSION_ERROR",
        "MARKET_DATA_SUBSCRIPTION_FAILED",
        "MARKET_DATA_STALE",
        "BROKER_DISCONNECTED",
        "ORDER_REJECTED_BY_RISK",
        "ORDER_REJECTED_BY_BROKER",
        "EXECUTION_REPORT_UNRESOLVED",
        "RECONCILIATION_DRIFT",
        "EVENT_SEQUENCE_GAP",
        "EVENT_SEQUENCE_DUPLICATE",
        "RECOVERY_OBSERVATION_REQUIRED",
        "RECOVERY_RECONCILIATION_REQUIRED",
        "EVENT_STORE_WRITE_FAILED",
    }
