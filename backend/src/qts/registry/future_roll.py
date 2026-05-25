"""Shared futures contract roll selection and resolution."""

from __future__ import annotations

from bisect import bisect_right
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import date, datetime
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
    session_date: date | None = None

    def __post_init__(self) -> None:
        if not self.root_symbol.strip():
            raise ValueError("root_symbol must not be empty")
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if self.volume < Decimal("0"):
            raise ValueError("volume must be non-negative")


@dataclass(frozen=True, slots=True)
class FutureContractRollSpec:
    """Contract metadata required to build a scheduled futures roll."""

    symbol: str
    instrument_id: InstrumentId
    first_notice_day: date
    expiry: datetime

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")


class FutureContractSelector(Protocol):
    """Select one concrete future from same-root same-time candidates."""

    def select(
        self,
        candidates: tuple[FutureContractCandidate, ...],
    ) -> FutureContractCandidate:
        """Select a concrete future contract."""
        ...


class HighestVolumeFutureContractSelector:
    """Select the most liquid candidate for one root at one timestamp."""

    def select(
        self,
        candidates: tuple[FutureContractCandidate, ...],
    ) -> FutureContractCandidate:
        """Perform select."""
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


class FirstNoticeDateFutureContractSelector:
    """Roll to the next active contract before first notice day."""

    def __init__(
        self,
        *,
        contracts: tuple[FutureContractRollSpec, ...],
        session_offset: Callable[[date, int], date],
        active_months: tuple[int, ...] = (),
        roll_sessions_before_first_notice: int = 3,
    ) -> None:
        if roll_sessions_before_first_notice <= 0:
            raise ValueError("roll_sessions_before_first_notice must be positive")
        active_month_set = frozenset(active_months)
        filtered_contracts = tuple(
            sorted(
                (
                    contract
                    for contract in contracts
                    if not active_month_set or contract.expiry.month in active_month_set
                ),
                key=lambda contract: (contract.expiry, contract.symbol),
            )
        )
        if not filtered_contracts:
            raise ValueError("at least one roll contract is required")
        self._contracts = filtered_contracts
        self._session_offset = session_offset
        self._roll_sessions_before_first_notice = roll_sessions_before_first_notice
        self._roll_sessions: dict[tuple[InstrumentId, datetime], date] = {}

    def select(
        self,
        candidates: tuple[FutureContractCandidate, ...],
    ) -> FutureContractCandidate:
        """Select the scheduled active contract for the candidates' exchange session."""
        if not candidates:
            raise ValueError("candidates must not be empty")
        session_dates = {candidate.session_date for candidate in candidates}
        if len(session_dates) != 1 or None in session_dates:
            raise ValueError("first-notice roll selection requires one exchange session date")
        session_date = next(iter(session_dates))
        if session_date is None:
            raise ValueError("first-notice roll selection requires an exchange session date")
        target = self._contract_for_session(session_date)
        candidates_by_instrument = {candidate.instrument_id: candidate for candidate in candidates}
        try:
            return candidates_by_instrument[target.instrument_id]
        except KeyError as exc:
            raise LookupError(
                f"scheduled contract {target.instrument_id} is unavailable "
                f"for session {session_date.isoformat()}"
            ) from exc

    def _contract_for_session(self, session_date: date) -> FutureContractRollSpec:
        for contract in self._contracts:
            if session_date < self._roll_session_for(contract):
                return contract
        return self._contracts[-1]

    def _roll_session_for(self, contract: FutureContractRollSpec) -> date:
        key = (contract.instrument_id, contract.expiry)
        roll_session = self._roll_sessions.get(key)
        if roll_session is None:
            roll_session = self._session_offset(
                contract.first_notice_day,
                -self._roll_sessions_before_first_notice,
            )
            self._roll_sessions[key] = roll_session
        return roll_session


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

    def __init__(self, *, retain_history: bool = True) -> None:
        self._retain_history = retain_history
        self._continuous_by_root: dict[str, InstrumentId] = {}
        self._root_by_continuous: dict[InstrumentId, str] = {}
        self._contracts_by_continuous: dict[InstrumentId, tuple[InstrumentId, ...]] = {}
        self._selections_by_continuous: dict[InstrumentId, list[FutureRollSelection]] = {}
        self._selection_times_by_continuous: dict[InstrumentId, list[datetime]] = {}
        self._latest_prices_by_continuous: dict[InstrumentId, dict[InstrumentId, Decimal]] = {}

    def register_root(
        self,
        *,
        root_symbol: str,
        exchange: str,
        contracts: tuple[InstrumentId, ...],
    ) -> InstrumentId:
        """Perform register_root."""
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
        self._selection_times_by_continuous.setdefault(continuous_id, [])
        self._latest_prices_by_continuous.setdefault(continuous_id, {})
        return continuous_id

    def continuous_instrument_id(self, root_symbol: str, *, offset: int = 0) -> InstrumentId:
        """Perform continuous_instrument_id."""
        if offset != 0:
            raise ValueError("only front continuous futures are supported")
        root = self._normalize_root(root_symbol)
        try:
            return self._continuous_by_root[root]
        except KeyError as exc:
            raise KeyError(f"missing future roll root: {root_symbol}") from exc

    def record_selection(self, selection: FutureRollSelection) -> None:
        """Perform record_selection."""
        if selection.continuous_instrument_id not in self._root_by_continuous:
            raise KeyError(f"unknown continuous future: {selection.continuous_instrument_id}")
        selections = self._selections_by_continuous[selection.continuous_instrument_id]
        selection_times = self._selection_times_by_continuous[selection.continuous_instrument_id]
        if selection_times and selection.as_of < selection_times[-1]:
            raise ValueError("future roll selections must be recorded in chronological order")
        latest_prices = self._latest_prices_by_continuous[selection.continuous_instrument_id]
        latest_prices.update(selection.prices_by_instrument)
        selection = replace(selection, prices_by_instrument=dict(latest_prices))
        if not self._retain_history:
            selections[:] = [selection]
            selection_times[:] = [selection.as_of]
            return
        selections.append(selection)
        selection_times.append(selection.as_of)

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        """Perform is_continuous."""
        return instrument_id in self._root_by_continuous

    def resolve_contract(
        self,
        reference: str | InstrumentId,
        *,
        as_of: datetime,
        offset: int = 0,
    ) -> InstrumentId:
        """Perform resolve_contract."""
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
        """Perform related_contracts."""
        try:
            return self._contracts_by_continuous[continuous_instrument_id]
        except KeyError as exc:
            raise KeyError(f"unknown continuous future: {continuous_instrument_id}") from exc

    def selection_history(
        self,
        continuous_instrument_id: InstrumentId | str | None = None,
    ) -> tuple[FutureRollSelection, ...]:
        """Return recorded roll selections for replay cache materialization."""

        if continuous_instrument_id is None:
            return tuple(
                selection
                for selections in self._selections_by_continuous.values()
                for selection in selections
            )
        continuous_id = (
            continuous_instrument_id
            if isinstance(continuous_instrument_id, InstrumentId)
            else self.continuous_instrument_id(continuous_instrument_id)
        )
        try:
            return tuple(self._selections_by_continuous[continuous_id])
        except KeyError as exc:
            raise KeyError(f"unknown continuous future: {continuous_id}") from exc

    def execution_price(
        self,
        continuous_instrument_id: InstrumentId,
        concrete_instrument_id: InstrumentId,
        *,
        as_of: datetime,
    ) -> Decimal:
        """Perform execution_price."""
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
            selection_times = self._selection_times_by_continuous[continuous_instrument_id]
        except KeyError as exc:
            raise KeyError(f"unknown continuous future: {continuous_instrument_id}") from exc
        index = bisect_right(selection_times, as_of) - 1
        if index < 0:
            raise KeyError(
                "missing future roll selection for "
                f"{continuous_instrument_id} at {as_of.isoformat()}"
            )
        return selections[index]

    @staticmethod
    def _normalize_root(root_symbol: str) -> str:
        normalized = root_symbol.strip().upper()
        if not normalized:
            raise ValueError("root_symbol must not be empty")
        return normalized


__all__ = [
    "FirstNoticeDateFutureContractSelector",
    "FutureContractCandidate",
    "FutureContractRollSpec",
    "FutureContractSelector",
    "FutureRollRegistry",
    "FutureRollSelection",
    "HighestVolumeFutureContractSelector",
]
