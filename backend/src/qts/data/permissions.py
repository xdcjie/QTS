"""Market-data permission state shared across streaming providers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MarketDataPermissionState(StrEnum):
    """Provider permission state visible to runtime and risk gates."""

    LIVE = "live"
    FROZEN = "frozen"
    DELAYED = "delayed"
    DELAYED_FROZEN = "delayed_frozen"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class MarketDataPermissionEvent:
    """Market-data permission state emitted by a data source."""

    source_id: str
    permission_state: MarketDataPermissionState
    provider_market_data_type: int
    request_id: int

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")


__all__ = ["MarketDataPermissionEvent", "MarketDataPermissionState"]
