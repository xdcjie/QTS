"""Strategy lifecycle application service."""

from __future__ import annotations

from qts.application.strategy_lifecycle import StrategyInstance, StrategyStatus
from qts.core.ids import StrategyId


class StrategyLifecycleService:
    """Start, stop, and inspect configured strategy instances."""

    def __init__(self, instances: tuple[StrategyInstance, ...] = ()) -> None:
        """Index the given instances and mark enabled ones as STOPPED."""
        self._instances = {instance.strategy_id: instance for instance in instances}
        self._status = {
            instance.strategy_id: StrategyStatus.STOPPED
            for instance in instances
            if instance.enabled
        }

    def add(self, instance: StrategyInstance) -> None:
        """Register a new strategy instance, rejecting duplicate ids."""
        if instance.strategy_id in self._instances:
            raise ValueError(f"strategy instance already exists: {instance.strategy_id}")
        self._instances[instance.strategy_id] = instance
        if instance.enabled:
            self._status[instance.strategy_id] = StrategyStatus.STOPPED

    def start(self, strategy_id: StrategyId) -> StrategyStatus:
        """Mark an enabled strategy as RUNNING and return its new status."""
        self._require_enabled(strategy_id)
        self._status[strategy_id] = StrategyStatus.RUNNING
        return self._status[strategy_id]

    def stop(self, strategy_id: StrategyId) -> StrategyStatus:
        """Mark an enabled strategy as STOPPED and return its new status."""
        self._require_enabled(strategy_id)
        self._status[strategy_id] = StrategyStatus.STOPPED
        return self._status[strategy_id]

    def status(self, strategy_id: StrategyId) -> StrategyStatus:
        """Return the current status of an enabled strategy."""
        self._require_enabled(strategy_id)
        return self._status[strategy_id]

    def list_instances(self) -> tuple[StrategyInstance, ...]:
        """Return all registered strategy instances."""
        return tuple(self._instances.values())

    def _require_enabled(self, strategy_id: StrategyId) -> None:
        """Raise if the strategy is unknown or disabled."""
        instance = self._instances[strategy_id]
        if not instance.enabled:
            raise ValueError(f"strategy instance is disabled: {strategy_id}")


__all__ = ["StrategyLifecycleService"]
