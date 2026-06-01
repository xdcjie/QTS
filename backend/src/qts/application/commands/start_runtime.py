"""Application command boundary for starting runtime modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qts.runtime.broker_startup import BrokerRuntimeStartupDecision
from qts.runtime.mode import RuntimeMode

if TYPE_CHECKING:
    from qts.application.services.runtime_session_builder import RuntimeSessionBuilder
    from qts.runtime.session import RuntimeSession


@dataclass(frozen=True, slots=True)
class StartRuntimeCommand:
    """Auditable request to start a runtime from a named configuration."""

    runtime_mode: RuntimeMode | str
    config_ref: str
    operator_id: str
    idempotency_key: str
    reason: str
    startup_decision: BrokerRuntimeStartupDecision | None = None

    def __post_init__(self) -> None:
        mode = RuntimeMode.from_value(self.runtime_mode)
        object.__setattr__(self, "runtime_mode", mode)
        self._require_text(self.config_ref, "config_ref")
        self._require_text(self.operator_id, "operator_id")
        self._require_text(self.idempotency_key, "idempotency_key")
        self._require_text(self.reason, "reason")
        if self.startup_decision is not None and self.startup_decision.mode is not mode:
            raise ValueError("startup_decision mode must match runtime_mode")

    @staticmethod
    def _require_text(value: str, name: str) -> None:
        if not value.strip():
            raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class RuntimeStartResult:
    """Result of a start-runtime command.

    ``status`` is ``started`` only when a real :class:`RuntimeSession` was built
    and started. Sessionless production requests are rejected rather than
    reported as a soft start.
    """

    runtime_mode: RuntimeMode
    config_ref: str
    operator_id: str
    idempotency_key: str
    status: str
    order_submission_enabled: bool
    live_order_submission_enabled: bool
    reason: str
    evidence: Mapping[str, object] = field(default_factory=dict)
    session: RuntimeSession | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", dict(self.evidence))
        if self.status == "started" and self.session is None:
            raise ValueError("started requires a RuntimeSession")


def start_runtime(
    command: StartRuntimeCommand,
    *,
    session_builder: RuntimeSessionBuilder | None = None,
) -> RuntimeStartResult:
    """Start a runtime only when a real session can be built and started."""

    runtime_mode = RuntimeMode.from_value(command.runtime_mode)
    order_submission_enabled = _order_submission_enabled(command)
    live_order_submission_enabled = _live_order_submission_enabled(command)
    if session_builder is None:
        return RuntimeStartResult(
            runtime_mode=runtime_mode,
            config_ref=command.config_ref,
            operator_id=command.operator_id,
            idempotency_key=command.idempotency_key,
            status="rejected",
            order_submission_enabled=False,
            live_order_submission_enabled=False,
            reason=command.reason,
            evidence={
                "runtime_mode": runtime_mode.value,
                "config_ref": command.config_ref,
                "operator_id": command.operator_id,
                "idempotency_key": command.idempotency_key,
                "reason": command.reason,
                "startup_gate_checked": command.startup_decision is not None,
                "session_constructed": False,
                "construction_reason": "session builder not supplied",
                "reason_code": "RUNTIME_SESSION_BUILDER_REQUIRED",
            },
        )
    _validate_session_builder(
        command,
        session_builder=session_builder,
        order_submission_enabled=order_submission_enabled,
    )
    session = session_builder.build()
    session.start()
    construction_reason = "runtime session constructed and started"
    return RuntimeStartResult(
        runtime_mode=runtime_mode,
        config_ref=command.config_ref,
        operator_id=command.operator_id,
        idempotency_key=command.idempotency_key,
        status="started",
        order_submission_enabled=order_submission_enabled,
        live_order_submission_enabled=live_order_submission_enabled,
        reason=command.reason,
        evidence={
            "runtime_mode": runtime_mode.value,
            "config_ref": command.config_ref,
            "operator_id": command.operator_id,
            "idempotency_key": command.idempotency_key,
            "reason": command.reason,
            "startup_gate_checked": command.startup_decision is not None,
            "session_constructed": session is not None,
            "construction_reason": construction_reason,
        },
        session=session,
    )


def _order_submission_enabled(command: StartRuntimeCommand) -> bool:
    mode = command.runtime_mode
    if mode in {RuntimeMode.BACKTEST, RuntimeMode.PAPER_BROKER, RuntimeMode.PAPER_SIMULATED}:
        return True
    if mode is RuntimeMode.LIVE_OBSERVATION:
        return False
    if mode is RuntimeMode.LIVE:
        return (
            command.startup_decision is not None
            and command.startup_decision.order_permission.allows_order_submission
        )
    return False


def _validate_session_builder(
    command: StartRuntimeCommand,
    *,
    session_builder: RuntimeSessionBuilder,
    order_submission_enabled: bool,
) -> None:
    dependencies = session_builder.dependencies
    if dependencies.mode is not command.runtime_mode:
        raise ValueError("session builder mode must match command runtime_mode")
    if dependencies.startup_decision != command.startup_decision:
        raise ValueError("session builder startup_decision must match command startup_decision")
    if dependencies.order_submission_enabled != order_submission_enabled:
        raise ValueError("session builder order_submission_enabled must match command order gate")


def _live_order_submission_enabled(command: StartRuntimeCommand) -> bool:
    if command.runtime_mode is not RuntimeMode.LIVE:
        return False
    return (
        command.startup_decision is not None
        and command.startup_decision.real_order_submission_enabled
    )


__all__ = ["RuntimeStartResult", "StartRuntimeCommand", "start_runtime"]
