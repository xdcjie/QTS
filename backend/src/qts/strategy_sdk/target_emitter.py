"""Target intent emission helpers for strategy context."""

from __future__ import annotations

from qts.strategy_sdk.target import TargetIntent


class TargetIntentEmitter:
    """Collect and emit `TargetIntent` values for one strategy context."""

    def __init__(self) -> None:
        """Initialize an empty list of emitted target intents."""
        self._intents: list[TargetIntent] = []

    @property
    def intents(self) -> tuple[TargetIntent, ...]:
        """Return the emitted target intents as an immutable tuple."""
        return tuple(self._intents)

    def emit(self, intent: TargetIntent) -> TargetIntent:
        """Record a target intent and return it."""
        self._intents.append(intent)
        return intent


__all__ = ["TargetIntentEmitter"]
