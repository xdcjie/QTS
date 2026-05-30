"""Historical futures chain metadata parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.core.ids import InstrumentId
from qts.data.sessions import RegularSessionWindow


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
    active_months: tuple[int, ...] = ()
    trading_hours: str = ""
    _contracts_by_symbol: dict[str, HistoricalContract] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Build the symbol-to-contract lookup index from the contract tuple."""
        contracts_by_symbol: dict[str, HistoricalContract] = {}
        for contract in self.contracts:
            contracts_by_symbol.setdefault(contract.symbol, contract)
        object.__setattr__(
            self,
            "_contracts_by_symbol",
            contracts_by_symbol,
        )

    def session_window(self) -> RegularSessionWindow | None:
        """Derive a recurring exchange-local session window from trading_hours.

        Parses the first segment of the ``trading_hours`` string
        (``YYYYMMDD:HHMM-YYYYMMDD:HHMM``, semicolon-separated days)
        and treats its open/close times as the recurring daily rule.
        Returns ``None`` when the chain has no ``trading_hours`` field.

        Holiday and early-close days are not represented here; the
        recurring window is enough to distinguish in-session from
        daily-break timestamps for overnight futures.
        """
        if not self.trading_hours.strip():
            return None
        first_segment = self.trading_hours.split(";")[0].strip()
        if "-" not in first_segment:
            raise ValueError(f"trading_hours segment missing '-' separator: {first_segment!r}")
        open_part, close_part = first_segment.split("-", 1)
        return RegularSessionWindow(
            exchange_timezone=self.timezone,
            open_time=self._parse_hhmm_suffix(open_part),
            close_time=self._parse_hhmm_suffix(close_part),
        )

    @staticmethod
    def _parse_hhmm_suffix(token: str) -> time:
        """Parse the ``HHMM`` portion of a ``YYYYMMDD:HHMM`` trading_hours token."""
        if ":" not in token:
            raise ValueError(f"trading_hours token missing ':' separator: {token!r}")
        suffix = token.split(":", 1)[1].strip()
        if len(suffix) != 4 or not suffix.isdigit():
            raise ValueError(f"trading_hours HHMM suffix must be 4 digits: {token!r}")
        return time(hour=int(suffix[:2]), minute=int(suffix[2:]))

    def contract_for_symbol(self, symbol: str) -> HistoricalContract:
        """Return the contract for the given local symbol, raising if unknown."""
        try:
            return self._contracts_by_symbol[symbol]
        except KeyError as exc:
            raise KeyError(f"unknown historical contract symbol: {symbol}") from exc

    def contract_for_symbol_and_expiry(
        self,
        symbol: str,
        expiry: datetime | date | str,
    ) -> HistoricalContract:
        """Return the contract matching the symbol and the given expiry date/datetime."""
        target = self._normalize_expiry_target(expiry)
        candidates = self.contracts_by_symbol(symbol)
        for candidate in candidates:
            if isinstance(target, date) and not isinstance(target, datetime):
                if candidate.expiry.date() == target:
                    return candidate
            elif candidate.expiry == target:
                return candidate
        raise KeyError(f"historical contract not found for {symbol} at {expiry!r}")

    def contracts_by_symbol(self, symbol: str) -> tuple[HistoricalContract, ...]:
        """Return all contracts with the provided local symbol."""
        return tuple(contract for contract in self.contracts if contract.symbol == symbol)

    def instrument_id_for_symbol_and_expiry(
        self,
        symbol: str,
        expiry: datetime | date | str,
    ) -> InstrumentId:
        """Return the InstrumentId for the contract matching the symbol and expiry."""
        _ = self.contract_for_symbol_and_expiry(symbol, expiry)
        return InstrumentId(f"FUTURE.{self.exchange}.{self.root}.{symbol}")

    def is_outright_symbol(self, symbol: str) -> bool:
        """Return True if the symbol is a known non-spread outright contract."""
        return "-" not in symbol and symbol in self._contracts_by_symbol

    def instrument_id_for_symbol(self, symbol: str) -> InstrumentId:
        """Return the InstrumentId for an outright contract symbol, raising otherwise."""
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
        raw_trading_hours = payload.get("trading_hours")
        trading_hours = str(raw_trading_hours) if isinstance(raw_trading_hours, str) else ""
        active_months = cls._parse_active_months(payload.get("active_months"))
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
            active_months=active_months,
            trading_hours=trading_hours,
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
        """Build a HistoricalContract from one raw chain-file contract entry."""
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
        """Return a required non-empty string field, raising if missing or blank."""
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        return value

    @staticmethod
    def _required_decimal(payload: dict[str, Any], field: str) -> Decimal:
        """Return a required positive Decimal field, raising if missing or non-positive."""
        if field not in payload:
            raise ValueError(f"{field} is required")
        value = Decimal(str(payload[field]))
        if value <= Decimal("0"):
            raise ValueError(f"{field} must be positive")
        return value

    @staticmethod
    def _parse_active_months(payload: object) -> tuple[int, ...]:
        """Parse optional active delivery months from chain metadata."""
        if payload is None:
            return ()
        if not isinstance(payload, list):
            raise ValueError("active_months must be a list")
        months = tuple(int(month) for month in payload)
        invalid = [month for month in months if month < 1 or month > 12]
        if invalid:
            raise ValueError("active_months entries must be in 1..12")
        return months

    @staticmethod
    def _normalize_expiry_target(expiry: datetime | date | str) -> datetime | date:
        """Normalize expiry to comparable datetime/date objects."""
        if isinstance(expiry, datetime):
            return expiry.astimezone(UTC) if expiry.tzinfo else expiry.replace(tzinfo=UTC)
        if isinstance(expiry, date):
            return expiry
        if isinstance(expiry, str):
            expiry_text = expiry.strip()
            if not expiry_text:
                raise ValueError("expiry must not be empty")
            try:
                return date.fromisoformat(expiry_text)
            except ValueError:
                value = datetime.fromisoformat(expiry_text)
                return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
        raise TypeError("expiry must be datetime, date, or ISO formatted string")

    @staticmethod
    def _exchange_code(market: str) -> str:
        """Return the exchange code, stripping any trailing ``_FUT`` suffix."""
        if market.endswith("_FUT"):
            return market.removesuffix("_FUT")
        return market


__all__ = ["HistoricalChain", "HistoricalContract"]
