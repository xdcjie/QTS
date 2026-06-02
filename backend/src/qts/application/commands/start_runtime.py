"""Application command boundary for starting runtime modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qts.runtime.broker_startup import BrokerRuntimeStartupDecision
from qts.runtime.mode import RuntimeMode

if TYPE_CHECKING:
    from qts.application.services.runtime_session_builder import RuntimeSessionBuilder
    from qts.runtime.control_plane import RuntimeSessionRegistry
    from qts.runtime.launch_plan import RuntimeLaunchPlan, RuntimeLaunchPlanStore
    from qts.runtime.session import RuntimeSession


@dataclass(frozen=True, slots=True)
class StartRuntimeCommand:
    """Auditable request to start a runtime from a named configuration."""

    runtime_mode: RuntimeMode | str
    runtime_instance_id: str
    config_ref: str
    launch_plan_hash: str
    operator_id: str
    idempotency_key: str
    reason: str
    startup_decision: BrokerRuntimeStartupDecision | None = None

    def __post_init__(self) -> None:
        mode = RuntimeMode.from_value(self.runtime_mode)
        object.__setattr__(self, "runtime_mode", mode)
        self._require_text(self.runtime_instance_id, "runtime_instance_id")
        self._require_text(self.config_ref, "config_ref")
        self._require_text(self.launch_plan_hash, "launch_plan_hash")
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
    runtime_instance_id: str
    config_ref: str
    launch_plan_hash: str
    operator_id: str
    idempotency_key: str
    status: str
    order_submission_enabled: bool
    live_order_submission_enabled: bool
    reason: str
    evidence: Mapping[str, object] = field(default_factory=dict)
    session: RuntimeSession | None = None

    def __post_init__(self) -> None:
        StartRuntimeCommand._require_text(self.runtime_instance_id, "runtime_instance_id")
        StartRuntimeCommand._require_text(self.launch_plan_hash, "launch_plan_hash")
        object.__setattr__(self, "evidence", dict(self.evidence))
        if self.status == "started" and self.session is None:
            raise ValueError("started requires a RuntimeSession")


def start_runtime(
    command: StartRuntimeCommand,
    *,
    session_builder: RuntimeSessionBuilder | None = None,
    session_registry: RuntimeSessionRegistry | None = None,
    launch_plan_store: RuntimeLaunchPlanStore | None = None,
) -> RuntimeStartResult:
    """Start a runtime only when a real session can be built and started."""

    runtime_mode = RuntimeMode.from_value(command.runtime_mode)
    order_submission_enabled = _order_submission_enabled(command)
    live_order_submission_enabled = _live_order_submission_enabled(command)
    plan_evidence = _verify_launch_plan(command, launch_plan_store=launch_plan_store)
    if plan_evidence["verified"] is not True:
        return RuntimeStartResult(
            runtime_mode=runtime_mode,
            runtime_instance_id=command.runtime_instance_id,
            config_ref=command.config_ref,
            launch_plan_hash=command.launch_plan_hash,
            operator_id=command.operator_id,
            idempotency_key=command.idempotency_key,
            status="rejected",
            order_submission_enabled=False,
            live_order_submission_enabled=False,
            reason=command.reason,
            evidence={
                **_base_evidence(command, runtime_mode=runtime_mode),
                **plan_evidence,
                "session_constructed": False,
            },
        )
    if session_builder is None:
        return RuntimeStartResult(
            runtime_mode=runtime_mode,
            runtime_instance_id=command.runtime_instance_id,
            config_ref=command.config_ref,
            launch_plan_hash=command.launch_plan_hash,
            operator_id=command.operator_id,
            idempotency_key=command.idempotency_key,
            status="rejected",
            order_submission_enabled=False,
            live_order_submission_enabled=False,
            reason=command.reason,
            evidence={
                **_base_evidence(command, runtime_mode=runtime_mode),
                **plan_evidence,
                "session_constructed": False,
                "construction_reason": "session builder not supplied",
                "reason_code": "RUNTIME_SESSION_BUILDER_REQUIRED",
            },
        )
    if session_registry is None:
        return RuntimeStartResult(
            runtime_mode=runtime_mode,
            runtime_instance_id=command.runtime_instance_id,
            config_ref=command.config_ref,
            launch_plan_hash=command.launch_plan_hash,
            operator_id=command.operator_id,
            idempotency_key=command.idempotency_key,
            status="rejected",
            order_submission_enabled=False,
            live_order_submission_enabled=False,
            reason=command.reason,
            evidence={
                **_base_evidence(command, runtime_mode=runtime_mode),
                **plan_evidence,
                "session_constructed": False,
                "construction_reason": "session registry not supplied",
                "reason_code": "RUNTIME_SESSION_REGISTRY_REQUIRED",
            },
        )
    from qts.runtime.control_plane import RuntimeSessionKey

    session_key = RuntimeSessionKey(runtime_instance_id=command.runtime_instance_id)
    if session_registry.resolve(session_key) is not None:
        return RuntimeStartResult(
            runtime_mode=runtime_mode,
            runtime_instance_id=command.runtime_instance_id,
            config_ref=command.config_ref,
            launch_plan_hash=command.launch_plan_hash,
            operator_id=command.operator_id,
            idempotency_key=command.idempotency_key,
            status="rejected",
            order_submission_enabled=False,
            live_order_submission_enabled=False,
            reason=command.reason,
            evidence={
                **_base_evidence(command, runtime_mode=runtime_mode),
                **plan_evidence,
                "session_constructed": False,
                "session_registered": False,
                "session_already_bound": True,
                "construction_reason": "runtime session already bound",
                "reason_code": "RUNTIME_SESSION_ALREADY_BOUND",
            },
        )
    _validate_session_builder(
        command,
        session_builder=session_builder,
        order_submission_enabled=order_submission_enabled,
    )
    session = session_builder.build()
    session.start()
    session_registry.register(session_key, session)
    session_registered = session_registry.resolve(session_key) is session
    construction_reason = "runtime session constructed and started"
    return RuntimeStartResult(
        runtime_mode=runtime_mode,
        runtime_instance_id=command.runtime_instance_id,
        config_ref=command.config_ref,
        launch_plan_hash=command.launch_plan_hash,
        operator_id=command.operator_id,
        idempotency_key=command.idempotency_key,
        status="started",
        order_submission_enabled=order_submission_enabled,
        live_order_submission_enabled=live_order_submission_enabled,
        reason=command.reason,
        evidence={
            **_base_evidence(command, runtime_mode=runtime_mode),
            **plan_evidence,
            "session_constructed": session is not None,
            "session_registered": session_registered,
            "construction_reason": construction_reason,
        },
        session=session,
    )


def _base_evidence(
    command: StartRuntimeCommand,
    *,
    runtime_mode: RuntimeMode,
) -> dict[str, object]:
    return {
        "runtime_mode": runtime_mode.value,
        "runtime_instance_id": command.runtime_instance_id,
        "config_ref": command.config_ref,
        "launch_plan_hash": command.launch_plan_hash,
        "operator_id": command.operator_id,
        "idempotency_key": command.idempotency_key,
        "reason": command.reason,
        "startup_gate_checked": command.startup_decision is not None,
    }


def _verify_launch_plan(
    command: StartRuntimeCommand,
    *,
    launch_plan_store: RuntimeLaunchPlanStore | None,
) -> dict[str, object]:
    if launch_plan_store is None:
        return {
            "launch_plan_verified": False,
            "verified": False,
            "reason_code": "RUNTIME_LAUNCH_PLAN_STORE_REQUIRED",
            "construction_reason": "launch plan store not supplied",
        }
    try:
        resolution = launch_plan_store.resolve(
            command.config_ref,
            expected_hash=command.launch_plan_hash,
        )
    except (FileNotFoundError, ValueError) as exc:
        return {
            "launch_plan_verified": False,
            "verified": False,
            "reason_code": "RUNTIME_LAUNCH_PLAN_INVALID",
            "construction_reason": str(exc),
        }
    mismatch = _launch_plan_command_mismatch(command, resolution.plan)
    if mismatch is not None:
        return {
            "launch_plan_verified": False,
            "verified": False,
            "reason_code": "RUNTIME_LAUNCH_PLAN_COMMAND_MISMATCH",
            "construction_reason": mismatch,
        }
    return {
        "launch_plan_verified": True,
        "verified": True,
        "launch_plan_path": str(resolution.path),
        "promotion_candidate_id": resolution.plan.promotion_candidate_id,
        "evidence_bundle_id": resolution.plan.evidence_bundle_id,
    }


def _launch_plan_command_mismatch(
    command: StartRuntimeCommand,
    plan: RuntimeLaunchPlan,
) -> str | None:
    command_mode = RuntimeMode.from_value(command.runtime_mode)
    try:
        plan_target_mode = RuntimeMode.from_value(plan.target_mode)
    except ValueError as exc:
        return str(exc)
    if plan_target_mode is not command_mode:
        return (
            "launch plan target_mode must match command runtime_mode: "
            f"{plan_target_mode.value} != {command_mode.value}"
        )

    runtime_mode = plan.runtime.get("runtime_mode")
    if not isinstance(runtime_mode, str) or not runtime_mode.strip():
        return "launch plan runtime.runtime_mode is required"
    try:
        plan_runtime_mode = RuntimeMode.from_value(runtime_mode)
    except ValueError as exc:
        return str(exc)
    if plan_runtime_mode is not command_mode:
        return (
            "launch plan runtime.runtime_mode must match command runtime_mode: "
            f"{plan_runtime_mode.value} != {command_mode.value}"
        )

    runtime_instance_id = plan.runtime.get("runtime_instance_id")
    if not isinstance(runtime_instance_id, str) or not runtime_instance_id.strip():
        return "launch plan runtime.runtime_instance_id is required"
    if runtime_instance_id.strip() != command.runtime_instance_id:
        return (
            "launch plan runtime.runtime_instance_id must match command runtime_instance_id: "
            f"{runtime_instance_id.strip()} != {command.runtime_instance_id}"
        )
    return None


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
