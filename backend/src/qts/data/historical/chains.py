"""Historical futures chain metadata parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import InstrumentId


@dataclass(frozen=True, slots=True)
class HistoricalContract:
    """One outright contract from a historical chain file."""

    symbol: str
    root: str
    exchange: str
    currency: str
    tick_size: Decimal
    multiplier: Decimal
    expiry: datetime
    first_notice_day: date
    trading_calendar: str


@dataclass(frozen=True, slots=True)
class HistoricalChain:
    """Parsed historical futures chain."""

    root: str
    exchange: str
    currency: str
    timezone: str
    tick_size: Decimal
    multiplier: Decimal
    trading_calendar: str
    contracts: tuple[HistoricalContract, ...]
    _contracts_by_symbol: dict[str, HistoricalContract] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        contracts_by_symbol: dict[str, HistoricalContract] = {}
        for contract in self.contracts:
            contracts_by_symbol.setdefault(contract.symbol, contract)
        object.__setattr__(
            self,
            "_contracts_by_symbol",
            contracts_by_symbol,
        )

    def contract_for_symbol(self, symbol: str) -> HistoricalContract:
        try:
            return self._contracts_by_symbol[symbol]
        except KeyError as exc:
            raise KeyError(f"unknown historical contract symbol: {symbol}") from exc

    def is_outright_symbol(self, symbol: str) -> bool:
        return "-" not in symbol and symbol in self._contracts_by_symbol

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId:
        if not self.is_outright_symbol(symbol):
            raise ValueError(f"{symbol} is not an outright {self.root} historical contract")
        return InstrumentId(f"FUTURE.{self.exchange}.{self.root}.{symbol}")

    @classmethod
    def load(cls, path: Path) -> HistoricalChain:
        """Load a historical futures chain JSON file into typed metadata."""

        payload = json.loads(path.read_text(encoding="utf-8"))
        root = cls._required_text(payload, "root")
        exchange = cls._exchange_code(cls._required_text(payload, "market"))
        currency = cls._required_text(payload, "currency")
        timezone = cls._required_text(payload, "timezone_id")
        tick_size = cls._required_decimal(payload, "tick_size")
        multiplier = cls._required_decimal(payload, "multiplier")
        trading_calendar = cls._required_text(payload, "trading_calendar")
        raw_contracts = payload.get("contracts")
        if not isinstance(raw_contracts, list):
            raise ValueError("contracts must be a list")

        contracts = tuple(
            cls._parse_contract(
                item,
                root=root,
                exchange=exchange,
                chain_currency=currency,
                chain_tick_size=tick_size,
                chain_multiplier=multiplier,
                chain_calendar=trading_calendar,
            )
            for item in raw_contracts
        )
        return cls(
            root=root,
            exchange=exchange,
            currency=currency,
            timezone=timezone,
            tick_size=tick_size,
            multiplier=multiplier,
            trading_calendar=trading_calendar,
            contracts=contracts,
        )

    @classmethod
    def _parse_contract(
        cls,
        payload: object,
        *,
        root: str,
        exchange: str,
        chain_currency: str,
        chain_tick_size: Decimal,
        chain_multiplier: Decimal,
        chain_calendar: str,
    ) -> HistoricalContract:
        if not isinstance(payload, dict):
            raise ValueError("contract entries must be objects")
        item: dict[str, Any] = payload
        symbol = cls._required_text(item, "local_symbol")
        expiry = datetime.fromisoformat(cls._required_text(item, "expiry")).astimezone(UTC)
        first_notice_day = date.fromisoformat(cls._required_text(item, "first_notice_day"))
        return HistoricalContract(
            symbol=symbol,
            root=root,
            exchange=exchange,
            currency=str(item.get("currency") or chain_currency),
            tick_size=chain_tick_size,
            multiplier=chain_multiplier,
            expiry=expiry,
            first_notice_day=first_notice_day,
            trading_calendar=str(item.get("trading_calendar") or chain_calendar),
        )

    @staticmethod
    def _required_text(payload: dict[str, Any], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        return value

    @staticmethod
    def _required_decimal(payload: dict[str, Any], field: str) -> Decimal:
        if field not in payload:
            raise ValueError(f"{field} is required")
        value = Decimal(str(payload[field]))
        if value <= Decimal("0"):
            raise ValueError(f"{field} must be positive")
        return value

    @staticmethod
    def _exchange_code(market: str) -> str:
        if market.endswith("_FUT"):
            return market.removesuffix("_FUT")
        return market


__all__ = ["HistoricalChain", "HistoricalContract"]
