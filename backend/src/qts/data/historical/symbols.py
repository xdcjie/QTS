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
        """Return the futures root symbol of the backing chain."""
        return self.chain.root

    def is_supported_symbol(self, symbol: str) -> bool:
        """Return True if the symbol is an outright contract in the chain."""
        return self.chain.is_outright_symbol(symbol)

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId:
        """Return the InstrumentId for an outright symbol via the chain metadata."""
        return self.chain.instrument_id_for_symbol(symbol)


__all__ = ["HistoricalFutureChainSymbolResolver"]
