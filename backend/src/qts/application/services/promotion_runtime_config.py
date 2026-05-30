"""Convert an approved promotion packet into a runtime start configuration.

:class:`PromotionPacketV2` is validation-only by design: it never constructs
runtime configuration or starts paper/live behavior. This builder is the
separate owner that reads an *approved* packet's ``runtime`` mapping and
produces a :class:`StartRuntimeCommand` consumable by ``start_runtime``.

The builder enforces that only the paper modes
(``paper_simulated`` / ``paper_broker``) are converted here; live promotion
requires the additional operator/risk gates that live outside the paper path.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, cast

from qts.application.commands.start_runtime import StartRuntimeCommand
from qts.research.promotion_packet import PromotionPacketV2
from qts.runtime.mode import RuntimeMode


class PromotionRuntimeConfigBuilder:
    """Build a paper runtime start command from an approved promotion packet."""

    _PAPER_MODES: ClassVar[frozenset[str]] = frozenset(
        {RuntimeMode.PAPER_SIMULATED.value, RuntimeMode.PAPER_BROKER.value}
    )

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
        runtime_mode = self._runtime_mode(packet, runtime)
        config_ref = self._config_ref(packet)
        return StartRuntimeCommand(
            runtime_mode=runtime_mode,
            config_ref=config_ref,
            operator_id=operator_id,
            idempotency_key=idempotency_key,
            reason=reason,
        )

    def _runtime_mode(
        self,
        packet: PromotionPacketV2,
        runtime: Mapping[str, object],
    ) -> RuntimeMode:
        declared = runtime.get("runtime_mode", packet.target_mode)
        mode = RuntimeMode.from_value(cast(str, declared))
        if mode.value not in self._PAPER_MODES:
            raise ValueError(f"promotion runtime_mode is not a paper mode: {mode.value}")
        if mode.value != packet.target_mode:
            raise ValueError(
                "promotion runtime.runtime_mode must match target_mode: "
                f"{mode.value} != {packet.target_mode}"
            )
        return mode

    @staticmethod
    def _config_ref(packet: PromotionPacketV2) -> str:
        """Derive a stable config reference from the promoted target module."""
        target_module = packet.target_module.strip()
        if not target_module:
            raise ValueError("promotion target_module is required to build a runtime config")
        return f"promotion://{packet.promotion_candidate_id}/{target_module}"


__all__ = ["PromotionRuntimeConfigBuilder"]
