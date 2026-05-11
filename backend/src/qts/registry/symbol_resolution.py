"""Source symbol resolution interfaces shared by data-source boundaries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from qts.core.ids import InstrumentId


class SourceSymbolResolver(Protocol):
    """Resolve external source symbols into internal instrument IDs."""

    def is_supported_symbol(self, symbol: str) -> bool: ...

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId: ...


@dataclass(frozen=True, slots=True)
class StaticSymbolResolver:
    """Resolve source symbols from an explicit symbol-to-instrument mapping."""

    instrument_ids: Mapping[str, InstrumentId]
    _normalized_instrument_ids: dict[str, InstrumentId] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.instrument_ids:
            raise ValueError("instrument_ids must not be empty")
        normalized_ids: dict[str, InstrumentId] = {}
        for symbol, instrument_id in self.instrument_ids.items():
            normalized = self._normalize_symbol(symbol)
            if normalized in normalized_ids:
                raise ValueError(f"duplicate source symbol after normalization: {symbol}")
            normalized_ids[normalized] = instrument_id
        object.__setattr__(self, "_normalized_instrument_ids", normalized_ids)

    def is_supported_symbol(self, symbol: str) -> bool:
        return self._normalize_symbol(symbol) in self._normalized_instrument_ids

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId:
        normalized = self._normalize_symbol(symbol)
        try:
            return self._normalized_instrument_ids[normalized]
        except KeyError as exc:
            raise ValueError(f"unsupported source symbol: {symbol}") from exc

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        return normalized


__all__ = ["SourceSymbolResolver", "StaticSymbolResolver"]
