"""Strategy control application service.

Backs the strategy API routes with the real strategy lifecycle owner
(:class:`StrategyLifecycleService`) instead of route literals. The service
exposes list/start/stop in terms of stable :class:`StrategyStatusDTO`
projections so the API layer never touches lifecycle internals.
"""

from __future__ import annotations

from qts.application.dto.control_plane import StrategyStatusDTO
from qts.application.services.strategy_service import StrategyLifecycleService
from qts.application.strategy_lifecycle import StrategyInstance
from qts.core.ids import StrategyId


class StrategyControlService:
    """Own list/start/stop control of configured strategies via the lifecycle owner."""

    def __init__(self, lifecycle: StrategyLifecycleService | None = None) -> None:
        """Create the service over a strategy lifecycle owner."""
        self._lifecycle = lifecycle or StrategyLifecycleService()

    @classmethod
    def with_configured_strategies(
        cls,
        instances: tuple[StrategyInstance, ...],
    ) -> StrategyControlService:
        """Create the service seeded with a configured strategy roster."""
        return cls(StrategyLifecycleService(instances))

    def add(self, instance: StrategyInstance) -> None:
        """Register a configured strategy instance with the lifecycle owner."""
        self._lifecycle.add(instance)

    def list_strategies(self) -> tuple[StrategyStatusDTO, ...]:
        """Return the status of every enabled configured strategy."""
        return tuple(
            StrategyStatusDTO(
                strategy_id=instance.strategy_id.value,
                status=self._lifecycle.status(instance.strategy_id).value,
            )
            for instance in self._lifecycle.list_instances()
            if instance.enabled
        )

    def start(self, strategy_id: str) -> StrategyStatusDTO:
        """Start a configured strategy and return its lifecycle status."""
        status = self._lifecycle.start(StrategyId(strategy_id))
        return StrategyStatusDTO(strategy_id=strategy_id, status=status.value)

    def stop(self, strategy_id: str) -> StrategyStatusDTO:
        """Stop a configured strategy and return its lifecycle status."""
        status = self._lifecycle.stop(StrategyId(strategy_id))
        return StrategyStatusDTO(strategy_id=strategy_id, status=status.value)


__all__ = ["StrategyControlService"]
