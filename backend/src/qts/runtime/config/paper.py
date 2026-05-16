"""Paper runtime configuration contracts."""

from dataclasses import dataclass
from typing import ClassVar

from qts.runtime.config.models import BrokerRuntimeConfig
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class PaperSimulatedRuntimeConfig(BrokerRuntimeConfig):
    """Configuration for local simulated execution runtime mode."""

    _supported_modes: ClassVar[frozenset[RuntimeMode]] = frozenset({RuntimeMode.PAPER_SIMULATED})

    def __post_init__(self) -> None:
        mode = RuntimeMode.from_value(self.mode)
        if mode is not RuntimeMode.PAPER_SIMULATED:
            raise ValueError("PaperSimulatedRuntimeConfig mode must be paper_simulated")
        BrokerRuntimeConfig.__post_init__(self)


__all__ = [
    "PaperSimulatedRuntimeConfig",
]
