"""Target intent emission helpers for strategy context."""

from __future__ import annotations

from qts.strategy_sdk.target import TargetIntent


class TargetIntentEmitter:
    """Collect and emit `TargetIntent` values for one strategy context."""

    def __init__(self) -> None:
        """Perform __init__."""
        self._intents: list[TargetIntent] = []

    @property
    def intents(self) -> tuple[TargetIntent, ...]:
        """Perform intents."""
        return tuple(self._intents)

    def emit(self, intent: TargetIntent) -> TargetIntent:
        """Perform emit."""
        self._intents.append(intent)
        return intent


__all__ = ["TargetIntentEmitter"]
