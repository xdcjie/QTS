"""In-memory instrument registry."""

from __future__ import annotations

from collections.abc import Iterator

from qts.core.ids import InstrumentId
from qts.domain.instruments import ContractSpec, Instrument


class InstrumentRegistry:
    """Resolve user-facing symbols to internal instruments."""

    def __init__(self) -> None:
        """Initialize empty symbol and instrument lookup maps."""
        self._symbols: dict[str, InstrumentId] = {}
        self._instruments: dict[InstrumentId, Instrument] = {}

    def register(self, user_symbol: str, instrument: Instrument) -> None:
        """Register an instrument under a normalized user-facing symbol."""
        symbol = self._normalize_symbol(user_symbol)
        self._symbols[symbol] = instrument.instrument_id
        self._instruments[instrument.instrument_id] = instrument

    def resolve(self, user_symbol: str) -> InstrumentId:
        """Resolve a user-facing symbol to its internal instrument id."""
        symbol = self._normalize_symbol(user_symbol)
        try:
            return self._symbols[symbol]
        except KeyError as exc:
            raise KeyError(f"unknown instrument symbol: {user_symbol}") from exc

    def get_instrument(self, instrument_id: InstrumentId) -> Instrument:
        """Return the registered instrument for the given id."""
        try:
            return self._instruments[instrument_id]
        except KeyError as exc:
            raise KeyError(f"unknown instrument id: {instrument_id}") from exc

    def get_contract_spec(self, instrument_id: InstrumentId) -> ContractSpec:
        """Return the contract spec for the given instrument id."""
        return self.get_instrument(instrument_id).contract_spec

    def contract_specs(self) -> Iterator[ContractSpec]:
        """Yield the contract spec of every registered instrument."""
        for instrument in self._instruments.values():
            yield instrument.contract_spec

    @staticmethod
    def _normalize_symbol(user_symbol: str) -> str:
        """Return the symbol uppercased and stripped, rejecting empty values."""
        normalized = user_symbol.strip().upper()
        if not normalized:
            raise ValueError("user_symbol must not be empty")
        return normalized


__all__ = ["InstrumentRegistry"]
