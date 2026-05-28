"""Broker symbol mapping kept at broker/data-source boundaries."""

from __future__ import annotations

from qts.core.ids import BrokerId, InstrumentId


class BrokerSymbolMapping:
    """Bidirectional mapping between internal IDs and one broker's symbols."""

    def __init__(self, broker_id: BrokerId) -> None:
        """Perform __init__."""
        self.broker_id = broker_id
        self._to_broker: dict[InstrumentId, str] = {}
        self._to_instrument: dict[str, InstrumentId] = {}

    def register(self, instrument_id: InstrumentId, broker_symbol: str) -> None:
        """Perform register."""
        symbol = self._normalize_broker_symbol(broker_symbol)
        existing = self._to_instrument.get(symbol)
        if existing is not None and existing != instrument_id:
            raise ValueError(f"broker symbol already mapped: {broker_symbol}")
        existing_symbol = self._to_broker.get(instrument_id)
        if existing_symbol is not None and existing_symbol != symbol:
            raise ValueError(f"instrument already mapped to broker symbol: {instrument_id}")
        self._to_broker[instrument_id] = symbol
        self._to_instrument[symbol] = instrument_id

    def to_broker_symbol(self, instrument_id: InstrumentId) -> str:
        """Perform to_broker_symbol."""
        try:
            return self._to_broker[instrument_id]
        except KeyError as exc:
            raise KeyError(f"missing broker symbol for instrument: {instrument_id}") from exc

    def to_instrument_id(self, broker_symbol: str) -> InstrumentId:
        """Perform to_instrument_id."""
        symbol = self._normalize_broker_symbol(broker_symbol)
        try:
            return self._to_instrument[symbol]
        except KeyError as exc:
            raise KeyError(
                f"missing instrument mapping for broker symbol: {broker_symbol}"
            ) from exc

    def is_supported_symbol(self, symbol: str) -> bool:
        """Perform is_supported_symbol."""
        return self._normalize_broker_symbol(symbol) in self._to_instrument

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId:
        """Perform instrument_id_for_symbol."""
        return self.to_instrument_id(symbol)

    @staticmethod
    def _normalize_broker_symbol(broker_symbol: str) -> str:
        """Perform _normalize_broker_symbol."""
        normalized = broker_symbol.strip()
        if not normalized:
            raise ValueError("broker_symbol must not be empty")
        return normalized


__all__ = ["BrokerSymbolMapping"]
