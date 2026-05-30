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
        """Validate the symbol and freeze the metadata into a read-only mapping."""
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def __hash__(self) -> int:
        """Return a hash derived from the instrument id and symbol."""
        return hash((self.instrument_id, self.symbol))


__all__ = ["AssetRef"]
