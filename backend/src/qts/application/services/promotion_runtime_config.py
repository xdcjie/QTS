"""Convert an approved promotion packet into a runtime start configuration.

:class:`PromotionPacketV2` is validation-only by design: it never constructs
runtime dependencies or starts paper/live behavior. This builder is the separate
owner that reads an *approved* packet's ``runtime`` mapping and produces a
:class:`StartRuntimeCommand` consumable by ``start_runtime``.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar, cast

from qts.application.commands.start_runtime import StartRuntimeCommand
from qts.core.hashing import stable_json_hash
from qts.research.promotion_packet import PromotionPacketV2
from qts.runtime.broker_startup import BrokerRuntimeStartupDecision
from qts.runtime.launch_plan import (
    RuntimeLaunchPlan,
    RuntimeLaunchPlanResolution,
    RuntimeLaunchPlanStore,
)
from qts.runtime.mode import RuntimeMode


class PromotionRuntimeConfigBuilder:
    """Build runtime start commands from approved promotion packets."""

    _PAPER_MODES: ClassVar[frozenset[str]] = frozenset(
        {RuntimeMode.PAPER_SIMULATED.value, RuntimeMode.PAPER_BROKER.value}
    )
    _LIVE_MODES: ClassVar[frozenset[str]] = frozenset(
        {RuntimeMode.LIVE_OBSERVATION.value, RuntimeMode.LIVE.value}
    )

    def __init__(self, *, launch_plan_dir: Path | None = None) -> None:
        self._launch_plan_dir = launch_plan_dir or Path("runs") / "promotion_launch_plans"
        self._launch_plan_store = RuntimeLaunchPlanStore(self._launch_plan_dir)

    def paper_start_command(
        self,
        packet: PromotionPacketV2,
        *,
        operator_id: str,
        idempotency_key: str,
        reason: str,
    ) -> StartRuntimeCommand:
        """Return a paper ``StartRuntimeCommand`` derived from the packet runtime."""
        if packet.target_mode not in self._PAPER_MODES:
            raise ValueError(f"promotion target_mode is not a paper mode: {packet.target_mode}")
        runtime = packet.runtime
        runtime_mode = self._runtime_mode(
            packet,
            runtime,
            allowed_modes=self._PAPER_MODES,
            mode_label="paper",
        )
        runtime_instance_id = self._runtime_instance_id(packet, runtime_mode=runtime_mode)
        launch_plan = self._materialize_launch_plan(
            packet,
            runtime_mode=runtime_mode,
            runtime_instance_id=runtime_instance_id,
        )
        return StartRuntimeCommand(
            runtime_mode=runtime_mode,
            runtime_instance_id=runtime_instance_id,
            config_ref=launch_plan.config_ref,
            launch_plan_hash=launch_plan.content_hash,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
            reason=reason,
        )

    def live_start_command(
        self,
        packet: PromotionPacketV2,
        *,
        operator_id: str,
        idempotency_key: str,
        reason: str,
        startup_decision: BrokerRuntimeStartupDecision,
    ) -> StartRuntimeCommand:
        """Return a live-capable ``StartRuntimeCommand`` derived from the packet runtime."""
        if packet.target_mode not in self._LIVE_MODES:
            raise ValueError(f"promotion target_mode is not a live mode: {packet.target_mode}")
        runtime = packet.runtime
        runtime_mode = self._runtime_mode(
            packet,
            runtime,
            allowed_modes=self._LIVE_MODES,
            mode_label="live",
        )
        if startup_decision.mode is not runtime_mode:
            raise ValueError("startup_decision mode must match promotion runtime_mode")
        runtime_instance_id = self._runtime_instance_id(packet, runtime_mode=runtime_mode)
        launch_plan = self._materialize_launch_plan(
            packet,
            runtime_mode=runtime_mode,
            runtime_instance_id=runtime_instance_id,
        )
        return StartRuntimeCommand(
            runtime_mode=runtime_mode,
            runtime_instance_id=runtime_instance_id,
            config_ref=launch_plan.config_ref,
            launch_plan_hash=launch_plan.content_hash,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
            reason=reason,
            startup_decision=startup_decision,
        )

    def _runtime_mode(
        self,
        packet: PromotionPacketV2,
        runtime: Mapping[str, object],
        *,
        allowed_modes: frozenset[str],
        mode_label: str,
    ) -> RuntimeMode:
        declared = runtime.get("runtime_mode", packet.target_mode)
        mode = RuntimeMode.from_value(cast(str, declared))
        if mode.value not in allowed_modes:
            raise ValueError(f"promotion runtime_mode is not a {mode_label} mode: {mode.value}")
        if mode.value != packet.target_mode:
            raise ValueError(
                "promotion runtime.runtime_mode must match target_mode: "
                f"{mode.value} != {packet.target_mode}"
            )
        return mode

    def _materialize_launch_plan(
        self,
        packet: PromotionPacketV2,
        *,
        runtime_mode: RuntimeMode,
        runtime_instance_id: str,
    ) -> RuntimeLaunchPlanResolution:
        """Write and return the immutable launch plan for a promotion packet."""
        target_module = packet.target_module.strip()
        if not target_module:
            raise ValueError("promotion target_module is required to build a runtime config")
        runtime_payload = dict(packet.runtime)
        runtime_payload["runtime_mode"] = runtime_mode.value
        runtime_payload["runtime_instance_id"] = runtime_instance_id
        plan = RuntimeLaunchPlan(
            promotion_candidate_id=packet.promotion_candidate_id,
            target_mode=runtime_mode.value,
            strategy_id=packet.strategy_id,
            source_module=packet.source_module,
            target_module=target_module,
            idea_id=packet.idea_id,
            evidence_bundle_id=packet.evidence_bundle_id,
            runtime=runtime_payload,
            operations=packet.operations,
            source_packet_hash=stable_json_hash(packet.to_payload()),
        )
        return self._launch_plan_store.write(plan)

    @staticmethod
    def _runtime_instance_id(
        packet: PromotionPacketV2,
        *,
        runtime_mode: RuntimeMode,
    ) -> str:
        """Return the runtime instance identity carried by the operator command."""

        configured = packet.runtime.get("runtime_instance_id")
        if isinstance(configured, str) and configured.strip():
            return configured.strip()
        return f"{packet.promotion_candidate_id}-{runtime_mode.value}"


__all__ = ["PromotionRuntimeConfigBuilder"]
