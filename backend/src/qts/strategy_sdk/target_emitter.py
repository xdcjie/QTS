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

    def drain(self) -> tuple[TargetIntent, ...]:
        """Return the emitted target intents and clear the buffer.

        Long-running live sessions must not retain emissions indefinitely; callers
        drain per event instead of slicing an ever-growing buffer.
        """
        drained = tuple(self._intents)
        self._intents.clear()
        return drained


__all__ = ["TargetIntentEmitter"]
