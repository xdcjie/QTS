"""Historical-specific symbol resolution adapters."""

from __future__ import annotations

from dataclasses import dataclass

from qts.core.ids import InstrumentId
from qts.data.historical.chains import HistoricalChain


@dataclass(frozen=True, slots=True)
class HistoricalFutureChainSymbolResolver:
    """Resolve historical futures outright symbols through chain metadata."""

    chain: HistoricalChain

    @property
    def root(self) -> str:
        """Perform root."""
        return self.chain.root

    def is_supported_symbol(self, symbol: str) -> bool:
        """Perform is_supported_symbol."""
        return self.chain.is_outright_symbol(symbol)

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId:
        """Perform instrument_id_for_symbol."""
        return self.chain.instrument_id_for_symbol(symbol)


__all__ = ["HistoricalFutureChainSymbolResolver"]
