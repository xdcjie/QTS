"""Strategy lifecycle models and registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum

from qts.core.ids import AccountId, StrategyId
from qts.strategy_sdk import Strategy


class StrategyStatus(StrEnum):
    """Configured strategy instance lifecycle status."""

    STOPPED = "stopped"
    RUNNING = "running"


@dataclass(frozen=True, slots=True)
class StrategyInstance:
    """Configured runtime instance of a Strategy class."""

    strategy_id: StrategyId
    class_path: str
    account_id: AccountId
    params: Mapping[str, str] = field(default_factory=dict)
    allocation: Decimal = Decimal("1")
    enabled: bool = True

    def __post_init__(self) -> None:
        """Validate the class path is non-empty and allocation is non-negative."""
        if not self.class_path.strip():
            raise ValueError("class_path must not be empty")
        if self.allocation < Decimal("0"):
            raise ValueError("allocation must be non-negative")


class StrategyRegistry:
    """Safe registry for explicitly approved strategy classes."""

    def __init__(self) -> None:
        """Initialize an empty registry of approved strategy classes."""
        self._classes: dict[str, type[Strategy]] = {}

    def register(self, class_path: str, strategy_cls: type[Strategy]) -> None:
        """Register a strategy class under its class path, rejecting duplicates."""
        if not class_path.strip():
            raise ValueError("class_path must not be empty")
        if class_path in self._classes:
            raise ValueError(f"strategy already registered: {class_path}")
        self._classes[class_path] = strategy_cls

    def resolve(self, class_path: str) -> type[Strategy]:
        """Return the registered strategy class for a class path."""
        try:
            return self._classes[class_path]
        except KeyError as exc:
            raise KeyError(f"strategy is not registered: {class_path}") from exc


__all__ = ["StrategyInstance", "StrategyRegistry", "StrategyStatus"]
