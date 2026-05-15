"""Construct a local paper runtime from configuration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PaperRuntimeConfig:
    """Local simulated paper runtime configuration."""

    account_id: str
    initial_cash: Decimal
    data_source: str
    simulated_broker: bool = True

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.account_id.strip():
            raise ValueError("account_id must not be empty")
        if self.initial_cash <= Decimal("0"):
            raise ValueError("initial_cash must be positive")
        if not self.data_source.strip():
            raise ValueError("data_source must not be empty")


@dataclass(frozen=True, slots=True)
class PaperRuntime:
    """Constructed paper runtime descriptor."""

    config: PaperRuntimeConfig
    status: str = "constructed"


def start_paper(config: PaperRuntimeConfig) -> PaperRuntime:
    """Construct the local simulated paper runtime boundary."""

    return PaperRuntime(config=config)


__all__ = ["PaperRuntime", "PaperRuntimeConfig", "start_paper"]
