from __future__ import annotations

from qts.api.schemas.common import OperationalErrorSchema
from qts.api.services.command_idempotency import CommandIdempotencyStore


def test_operational_error_schema_hides_internal_details() -> None:
    schema = OperationalErrorSchema.from_exception(
        code="RUNTIME_PAUSED",
        message="runtime is paused",
        exc=RuntimeError("database password=secret"),
    )

    assert schema.code == "RUNTIME_PAUSED"
    assert schema.message == "runtime is paused"
    assert schema.detail is None


def test_command_idempotency_returns_first_result_for_duplicate_key() -> None:
    store = CommandIdempotencyStore()

    first = store.run("key-1", lambda: {"status": "paused"})
    second = store.run("key-1", lambda: {"status": "running"})

    assert first == {"status": "paused"}
    assert second == {"status": "paused"}


def test_command_idempotency_is_scoped_by_command_kind() -> None:
    store = CommandIdempotencyStore()

    runtime_result = store.run("key-1", lambda: {"status": "paused"}, scope="runtime")
    order_result = store.run("key-1", lambda: {"status": "cancelled"}, scope="cancel")

    assert runtime_result == {"status": "paused"}
    assert order_result == {"status": "cancelled"}


def test_runtime_command_result_schema_exposes_reason_code() -> None:
    from qts.api.schemas.operations import RuntimeCommandResultResponseSchema

    payload = RuntimeCommandResultResponseSchema(
        command_id="cmd-001",
        idempotency_key="key-1",
        status="rejected",
        evidence={},
        failure_reason="permission denied",
        reason_code="COMMAND_PERMISSION_DENIED",
    )

    assert payload.reason_code == "COMMAND_PERMISSION_DENIED"
