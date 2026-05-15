from __future__ import annotations

from datetime import UTC, datetime


def test_runtime_command_bus_returns_same_result_for_duplicate_command_key() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            completed_at=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence={"state": "paused"},
        )

    bus = RuntimeCommandBus(handler=handler)
    first = bus.submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="pause-key",
            operator_id="ops-a",
        )
    )
    second = bus.submit(
        RuntimeCommand(
            command_id="cmd-002",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="pause-key",
            operator_id="ops-a",
        )
    )

    assert second == first
    assert [command.command_id for command in calls] == ["cmd-001"]


def test_runtime_command_result_requires_failure_reason_for_rejected_command() -> None:
    import pytest
    from qts.runtime.commands import RuntimeCommandResult, RuntimeCommandResultStatus

    with pytest.raises(ValueError, match="failure_reason"):
        RuntimeCommandResult(
            command_id="cmd-001",
            idempotency_key="key-1",
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.REJECTED,
        )


def test_runtime_command_bus_scopes_idempotency_by_command_type() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            completed_at=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence={"command_type": command.command_type.value},
        )

    bus = RuntimeCommandBus(handler=handler)
    pause = bus.submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="shared-key",
            operator_id="ops-a",
        )
    )
    reconcile = bus.submit(
        RuntimeCommand(
            command_id="cmd-002",
            command_type=RuntimeCommandType.RECONCILE,
            idempotency_key="shared-key",
            operator_id="ops-a",
        )
    )

    assert pause.evidence["command_type"] == "pause"
    assert reconcile.evidence["command_type"] == "reconcile"
    assert [command.command_type for command in calls] == [
        RuntimeCommandType.PAUSE,
        RuntimeCommandType.RECONCILE,
    ]


def test_runtime_command_bus_scopes_idempotency_by_runtime_and_operator() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            completed_at=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence={"operator_id": command.operator_id},
        )

    bus = RuntimeCommandBus(handler=handler)
    first = bus.submit(
        RuntimeCommand(
            command_id="cmd-001",
            runtime_instance_id="runtime-a",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="shared-key",
            operator_id="ops-a",
        )
    )
    duplicate = bus.submit(
        RuntimeCommand(
            command_id="cmd-002",
            runtime_instance_id="runtime-a",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="shared-key",
            operator_id="ops-a",
        )
    )
    other_operator = bus.submit(
        RuntimeCommand(
            command_id="cmd-003",
            runtime_instance_id="runtime-a",
            command_type=RuntimeCommandType.PAUSE,
            idempotency_key="shared-key",
            operator_id="ops-b",
        )
    )

    assert duplicate == first
    assert other_operator.evidence["operator_id"] == "ops-b"
    assert [command.command_id for command in calls] == ["cmd-001", "cmd-003"]


def test_runtime_command_bus_rejects_unauthorized_kill_switch_deactivation() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        raise AssertionError("unauthorized command should not reach handler")

    result = RuntimeCommandBus(handler=handler).submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.DEACTIVATE_KILL_SWITCH,
            idempotency_key="kill-off",
            operator_id="ops-a",
            operator_role="trader",
            authorization_scope="runtime:read",
        )
    )

    assert result.result_status is RuntimeCommandResultStatus.REJECTED
    assert result.reason_code == "COMMAND_PERMISSION_DENIED"
    assert calls == []


def test_runtime_command_bus_rejects_live_enablement_without_dual_control() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        raise AssertionError("unapproved live enablement should not reach handler")

    result = RuntimeCommandBus(handler=handler).submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.EXIT_OBSERVATION,
            idempotency_key="enable-live",
            operator_id="ops-a",
            operator_role="safety_officer",
            authorization_scope="runtime:safety:write",
            approval_required=True,
            payload={"enable_live_orders": True},
        )
    )

    assert result.result_status is RuntimeCommandResultStatus.REJECTED
    assert result.reason_code == "DUAL_CONTROL_REQUIRED"


def test_runtime_command_bus_allows_approved_live_enablement() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    calls: list[RuntimeCommand] = []

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        calls.append(command)
        return RuntimeCommandResult(
            command_id=command.command_id,
            idempotency_key=command.idempotency_key,
            accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            completed_at=datetime(2026, 1, 2, 14, 30, 1, tzinfo=UTC),
            result_status=RuntimeCommandResultStatus.COMPLETED,
            evidence={"approved_by": command.approved_by},
        )

    result = RuntimeCommandBus(handler=handler).submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.EXIT_OBSERVATION,
            idempotency_key="enable-live",
            operator_id="ops-a",
            operator_role="safety_officer",
            authorization_scope="runtime:safety:write",
            approval_required=True,
            approved_by="ops-b",
            payload={"enable_live_orders": True},
        )
    )

    assert result.result_status is RuntimeCommandResultStatus.COMPLETED
    assert result.evidence["approved_by"] == "ops-b"
    assert [command.command_id for command in calls] == ["cmd-001"]


def test_runtime_command_bus_rejects_live_enablement_self_approval() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        raise AssertionError("self-approved live enablement should not reach handler")

    result = RuntimeCommandBus(handler=handler).submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.EXIT_OBSERVATION,
            idempotency_key="enable-live",
            operator_id="ops-a",
            operator_role="safety_officer",
            authorization_scope="runtime:safety:write",
            approved_by="ops-a",
            payload={"enable_live_orders": True},
        )
    )

    assert result.result_status is RuntimeCommandResultStatus.REJECTED
    assert result.reason_code == "DUAL_CONTROL_REQUIRED"


def test_runtime_command_audit_events_include_authorization_scope() -> None:
    from qts.runtime.commands import RuntimeCommand, RuntimeCommandType

    command = RuntimeCommand(
        command_id="cmd-001",
        runtime_instance_id="runtime-a",
        command_type=RuntimeCommandType.RECONCILE,
        idempotency_key="reconcile-key",
        operator_id="ops-a",
        operator_role="safety_officer",
        authorization_scope="runtime:safety:write",
        requested_at=datetime(2026, 1, 2, 14, 29, tzinfo=UTC),
        approved_by="ops-b",
    )

    event = command.accepted_event(accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC))

    assert event.payload["runtime_instance_id"] == "runtime-a"
    assert event.payload["operator_role"] == "safety_officer"
    assert event.payload["authorization_scope"] == "runtime:safety:write"
    assert event.payload["requested_at"] == "2026-01-02T14:29:00+00:00"
    assert event.payload["approved_by"] == "ops-b"


def test_runtime_command_control_types_emit_audit_events() -> None:
    from qts.runtime.commands import RuntimeCommand, RuntimeCommandType

    command_types = [
        RuntimeCommandType.PAUSE,
        RuntimeCommandType.RESUME,
        RuntimeCommandType.ACTIVATE_KILL_SWITCH,
        RuntimeCommandType.DEACTIVATE_KILL_SWITCH,
        RuntimeCommandType.RECONCILE,
        RuntimeCommandType.SNAPSHOT,
    ]

    for command_type in command_types:
        command = RuntimeCommand(
            command_id=f"cmd-{command_type.value}",
            command_type=command_type,
            idempotency_key=f"key-{command_type.value}",
            operator_id="ops-a",
            authorization_scope="runtime:safety:write",
        )

        event = command.accepted_event(accepted_at=datetime(2026, 1, 2, 14, 30, tzinfo=UTC))

        assert event.event_type == "command_accepted"
        assert event.payload["command_type"] == command_type.value
        assert event.payload["operator_id"] == "ops-a"
        assert event.payload["authorization_scope"] == "runtime:safety:write"


def test_runtime_command_bus_rejects_resume_after_reconnect_without_reconciliation() -> None:
    from qts.runtime.commands import (
        RuntimeCommand,
        RuntimeCommandBus,
        RuntimeCommandResult,
        RuntimeCommandResultStatus,
        RuntimeCommandType,
    )

    def handler(command: RuntimeCommand) -> RuntimeCommandResult:
        raise AssertionError("resume without reconnect reconciliation should not reach handler")

    result = RuntimeCommandBus(handler=handler).submit(
        RuntimeCommand(
            command_id="cmd-001",
            command_type=RuntimeCommandType.RESUME,
            idempotency_key="resume-key",
            operator_id="ops-a",
            payload={
                "reconnect_reconciliation_required": True,
                "reconciliation_passed": False,
            },
        )
    )

    assert result.result_status is RuntimeCommandResultStatus.REJECTED
    assert result.reason_code == "RECONNECT_RECONCILIATION_REQUIRED"
