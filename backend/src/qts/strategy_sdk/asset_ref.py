"""User-safe asset references."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from qts.core.ids import InstrumentId


@dataclass(frozen=True, slots=True)
class AssetRef:
    """Lightweight strategy-facing reference to an internal instrument."""

    instrument_id: InstrumentId
    symbol: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def __hash__(self) -> int:
        """Perform __hash__."""
        return hash((self.instrument_id, self.symbol))


__all__ = ["AssetRef"]
