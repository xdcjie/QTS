"""Paper runtime configuration contracts."""

from dataclasses import dataclass

from qts.runtime.config.models import LiveRuntimeConfig
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class PaperBrokerRuntimeConfig(LiveRuntimeConfig):
    """Configuration for paper-account broker runtime mode."""

    def __post_init__(self) -> None:
        LiveRuntimeConfig.__post_init__(self)
        mode = RuntimeMode.from_value(self.mode)
        if mode is not RuntimeMode.PAPER_BROKER:
            raise ValueError("PaperBrokerRuntimeConfig mode must be paper_broker")


@dataclass(frozen=True, slots=True)
class PaperSimulatedRuntimeConfig(LiveRuntimeConfig):
    """Configuration for local simulated execution runtime mode."""

    def __post_init__(self) -> None:
        LiveRuntimeConfig.__post_init__(self)
        mode = RuntimeMode.from_value(self.mode)
        if mode is not RuntimeMode.PAPER_SIMULATED:
            raise ValueError("PaperSimulatedRuntimeConfig mode must be paper_simulated")


__all__ = [
    "PaperBrokerRuntimeConfig",
    "PaperSimulatedRuntimeConfig",
]
