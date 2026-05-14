"""Paper runtime configuration contracts."""

from dataclasses import dataclass

from qts.runtime.config.models import LiveRuntimeConfig
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class PaperRuntimeConfig(LiveRuntimeConfig):
    """Configuration for paper broker or paper simulated runtime modes."""

    def __post_init__(self) -> None:
        super().__post_init__()
        mode = RuntimeMode.from_value(self.mode)
        if mode not in {RuntimeMode.PAPER_BROKER, RuntimeMode.PAPER_SIMULATED}:
            raise ValueError("PaperRuntimeConfig mode must be paper_broker or paper_simulated")


__all__ = ["PaperRuntimeConfig"]
