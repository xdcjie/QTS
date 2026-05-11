"""Shared futures contract roll selection and resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from qts.core.ids import InstrumentId


@dataclass(frozen=True, slots=True)
class FutureContractCandidate:
    """One concrete futures contract candidate at a decision timestamp."""

    root_symbol: str
    symbol: str
    instrument_id: InstrumentId
    as_of: datetime
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if self.volume < Decimal("0"):
            raise ValueError("volume must be non-negative")


class FutureContractSelector(Protocol):
    """Select one concrete future from same-root same-time candidates."""

    def select(
        self,
        candidates: tuple[FutureContractCandidate, ...],
    ) -> FutureContractCandidate: ...


class HighestVolumeFutureContractSelector:
    """Select the most liquid candidate for one root at one timestamp."""

    def select(
        self,
        candidates: tuple[FutureContractCandidate, ...],
    ) -> FutureContractCandidate:
        if not candidates:
            raise ValueError("candidates must not be empty")
        return max(
            candidates,
            key=lambda candidate: (
                candidate.volume,
                candidate.symbol,
                candidate.instrument_id.value,
            ),
        )


@dataclass(frozen=True, slots=True)
class FutureRollSelection:
    """Resolved concrete contract for a continuous future at one timestamp."""

    continuous_instrument_id: InstrumentId
    root_symbol: str
    as_of: datetime
    concrete_instrument_id: InstrumentId
    source_symbol: str
    prices_by_instrument: Mapping[InstrumentId, Decimal]

    def __post_init__(self) -> None:
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")
        if not self.source_symbol.strip():
            raise ValueError("source_symbol must not be empty")


class FutureRollRegistry:
    """Resolve continuous futures to concrete contracts over time."""

    def __init__(self) -> None:
        self._continuous_by_root: dict[str, InstrumentId] = {}
        self._root_by_continuous: dict[InstrumentId, str] = {}
        self._contracts_by_continuous: dict[InstrumentId, tuple[InstrumentId, ...]] = {}
        self._selections_by_continuous: dict[InstrumentId, list[FutureRollSelection]] = {}

    def register_root(
        self,
        *,
        root_symbol: str,
        exchange: str,
        contracts: tuple[InstrumentId, ...],
    ) -> InstrumentId:
        root = self._normalize_root(root_symbol)
        if not exchange.strip():
            raise ValueError("exchange must not be empty")
        unique_contracts = tuple(dict.fromkeys(contracts))
        if not unique_contracts:
            raise ValueError("contracts must not be empty")
        continuous_id = InstrumentId(f"CONTINUOUS_FUTURE.{exchange.strip().upper()}.{root}")
        self._continuous_by_root[root] = continuous_id
        self._root_by_continuous[continuous_id] = root
        self._contracts_by_continuous[continuous_id] = unique_contracts
        self._selections_by_continuous.setdefault(continuous_id, [])
        return continuous_id

    def continuous_instrument_id(self, root_symbol: str, *, offset: int = 0) -> InstrumentId:
        if offset != 0:
            raise ValueError("only front continuous futures are supported")
        root = self._normalize_root(root_symbol)
        try:
            return self._continuous_by_root[root]
        except KeyError as exc:
            raise KeyError(f"missing future roll root: {root_symbol}") from exc

    def record_selection(self, selection: FutureRollSelection) -> None:
        if selection.continuous_instrument_id not in self._root_by_continuous:
            raise KeyError(f"unknown continuous future: {selection.continuous_instrument_id}")
        selections = self._selections_by_continuous[selection.continuous_instrument_id]
        selections.append(selection)
        selections.sort(key=lambda item: item.as_of)

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        return instrument_id in self._root_by_continuous

    def resolve_contract(
        self,
        reference: str | InstrumentId,
        *,
        as_of: datetime,
        offset: int = 0,
    ) -> InstrumentId:
        if offset != 0:
            raise ValueError("only front continuous futures are supported")
        continuous_id = (
            reference
            if isinstance(reference, InstrumentId)
            else self.continuous_instrument_id(reference)
        )
        selection = self._selection_at(continuous_id, as_of=as_of)
        return selection.concrete_instrument_id

    def related_contracts(self, continuous_instrument_id: InstrumentId) -> tuple[InstrumentId, ...]:
        try:
            return self._contracts_by_continuous[continuous_instrument_id]
        except KeyError as exc:
            raise KeyError(f"unknown continuous future: {continuous_instrument_id}") from exc

    def execution_price(
        self,
        continuous_instrument_id: InstrumentId,
        concrete_instrument_id: InstrumentId,
        *,
        as_of: datetime,
    ) -> Decimal:
        selection = self._selection_at(continuous_instrument_id, as_of=as_of)
        try:
            return selection.prices_by_instrument[concrete_instrument_id]
        except KeyError as exc:
            raise KeyError(
                f"missing roll execution price for {concrete_instrument_id} at {as_of.isoformat()}"
            ) from exc

    def _selection_at(
        self,
        continuous_instrument_id: InstrumentId,
        *,
        as_of: datetime,
    ) -> FutureRollSelection:
        try:
            selections = self._selections_by_continuous[continuous_instrument_id]
        except KeyError as exc:
            raise KeyError(f"unknown continuous future: {continuous_instrument_id}") from exc
        available = [selection for selection in selections if selection.as_of <= as_of]
        if not available:
            raise KeyError(
                "missing future roll selection for "
                f"{continuous_instrument_id} at {as_of.isoformat()}"
            )
        return available[-1]

    @staticmethod
    def _normalize_root(root_symbol: str) -> str:
        normalized = root_symbol.strip().upper()
        if not normalized:
            raise ValueError("root_symbol must not be empty")
        return normalized


__all__ = [
    "FutureContractCandidate",
    "FutureContractSelector",
    "FutureRollRegistry",
    "FutureRollSelection",
    "HighestVolumeFutureContractSelector",
]
