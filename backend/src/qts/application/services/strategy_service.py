"""Strategy lifecycle application service."""

from __future__ import annotations

from qts.application.strategy_lifecycle import StrategyInstance, StrategyStatus
from qts.core.ids import StrategyId


class StrategyLifecycleService:
    """Start, stop, and inspect configured strategy instances."""

    def __init__(self, instances: tuple[StrategyInstance, ...] = ()) -> None:
        """Perform __init__."""
        self._instances = {instance.strategy_id: instance for instance in instances}
        self._status = {
            instance.strategy_id: StrategyStatus.STOPPED
            for instance in instances
            if instance.enabled
        }

    def add(self, instance: StrategyInstance) -> None:
        """Perform add."""
        if instance.strategy_id in self._instances:
            raise ValueError(f"strategy instance already exists: {instance.strategy_id}")
        self._instances[instance.strategy_id] = instance
        if instance.enabled:
            self._status[instance.strategy_id] = StrategyStatus.STOPPED

    def start(self, strategy_id: StrategyId) -> StrategyStatus:
        """Perform start."""
        self._require_enabled(strategy_id)
        self._status[strategy_id] = StrategyStatus.RUNNING
        return self._status[strategy_id]

    def stop(self, strategy_id: StrategyId) -> StrategyStatus:
        """Perform stop."""
        self._require_enabled(strategy_id)
        self._status[strategy_id] = StrategyStatus.STOPPED
        return self._status[strategy_id]

    def status(self, strategy_id: StrategyId) -> StrategyStatus:
        """Perform status."""
        self._require_enabled(strategy_id)
        return self._status[strategy_id]

    def list_instances(self) -> tuple[StrategyInstance, ...]:
        """Perform list_instances."""
        return tuple(self._instances.values())

    def _require_enabled(self, strategy_id: StrategyId) -> None:
        """Perform _require_enabled."""
        instance = self._instances[strategy_id]
        if not instance.enabled:
            raise ValueError(f"strategy instance is disabled: {strategy_id}")


__all__ = ["StrategyLifecycleService"]
