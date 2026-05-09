"""In-memory instrument registry."""

from __future__ import annotations

from qts.core.ids import InstrumentId
from qts.domain.instruments import ContractSpec, Instrument


class InstrumentRegistry:
    """Resolve user-facing symbols to internal instruments."""

    def __init__(self) -> None:
        self._symbols: dict[str, InstrumentId] = {}
        self._instruments: dict[InstrumentId, Instrument] = {}

    def register(self, user_symbol: str, instrument: Instrument) -> None:
        symbol = _normalize_symbol(user_symbol)
        self._symbols[symbol] = instrument.instrument_id
        self._instruments[instrument.instrument_id] = instrument

    def resolve(self, user_symbol: str) -> InstrumentId:
        symbol = _normalize_symbol(user_symbol)
        try:
            return self._symbols[symbol]
        except KeyError as exc:
            raise KeyError(f"unknown instrument symbol: {user_symbol}") from exc

    def get_instrument(self, instrument_id: InstrumentId) -> Instrument:
        try:
            return self._instruments[instrument_id]
        except KeyError as exc:
            raise KeyError(f"unknown instrument id: {instrument_id}") from exc

    def get_contract_spec(self, instrument_id: InstrumentId) -> ContractSpec:
        return self.get_instrument(instrument_id).contract_spec


def _normalize_symbol(user_symbol: str) -> str:
    normalized = user_symbol.strip().upper()
    if not normalized:
        raise ValueError("user_symbol must not be empty")
    return normalized


__all__ = ["InstrumentRegistry"]
