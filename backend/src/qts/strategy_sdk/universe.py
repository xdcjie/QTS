"""Strategy-facing universe selection contracts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from qts.core.ids import InstrumentId
from qts.strategy_sdk.asset_ref import AssetRef

UniverseMember: TypeAlias = AssetRef | InstrumentId


class UniverseSelector(Protocol):
    """Strategy-owned selector that returns internal-instrument universe intent."""

    def select_universe(self) -> Iterable[UniverseMember]:
        """Return the next selected universe members."""


@dataclass(frozen=True, slots=True)
class Universe:
    """Duplicate-free universe expressed only as internal instrument IDs."""

    instrument_ids: tuple[InstrumentId, ...]

    def __post_init__(self) -> None:
        """Normalize direct construction into deterministic internal IDs."""
        object.__setattr__(self, "instrument_ids", _dedupe_sorted(self.instrument_ids))

    @classmethod
    def empty(cls) -> Universe:
        """Return an empty universe for context initialization."""
        return cls(())

    @classmethod
    def from_members(cls, members: Iterable[UniverseMember]) -> Universe:
        """Create a universe from strategy-facing asset refs or internal IDs."""
        instrument_ids = _instrument_ids(members)
        if not instrument_ids:
            raise ValueError("universe must contain at least one instrument")
        return cls(instrument_ids)

    def set(self, members: Iterable[UniverseMember]) -> Universe:
        """Replace this universe with the given members."""
        return Universe.from_members(members)

    def add(self, members: Iterable[UniverseMember]) -> Universe:
        """Return a universe containing existing and additional members."""
        return Universe((*self.instrument_ids, *_instrument_ids(members)))

    def remove(self, members: Iterable[UniverseMember]) -> Universe:
        """Return a universe without the given members."""
        remove_ids = set(_instrument_ids(members))
        return Universe(tuple(item for item in self.instrument_ids if item not in remove_ids))


def _instrument_ids(members: Iterable[UniverseMember]) -> tuple[InstrumentId, ...]:
    return tuple(
        member.instrument_id if isinstance(member, AssetRef) else member for member in members
    )


def _dedupe_sorted(instrument_ids: Iterable[InstrumentId]) -> tuple[InstrumentId, ...]:
    return tuple(sorted(set(instrument_ids), key=lambda item: item.value))


__all__ = ["Universe", "UniverseMember", "UniverseSelector"]
