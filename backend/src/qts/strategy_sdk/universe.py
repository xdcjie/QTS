"""Strategy-facing universe selection contracts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, TypeAlias

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk.asset_ref import AssetRef

UniverseMember: TypeAlias = AssetRef | InstrumentId


class UniverseSelector(Protocol):
    """Strategy-owned selector that returns internal-instrument universe intent."""

    def select_universe(self) -> Iterable[UniverseMember]:
        """Return the next selected universe members."""


@dataclass(frozen=True, slots=True)
class FundamentalUniverseRow:
    """Fundamental snapshot used by strategy-owned universe selectors."""

    instrument_id: InstrumentId
    market_cap: Decimal = Decimal("0")
    dollar_volume: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        """Validate fundamental selector metrics."""
        if self.market_cap < Decimal("0"):
            raise ValueError("market_cap must be non-negative")
        if self.dollar_volume < Decimal("0"):
            raise ValueError("dollar_volume must be non-negative")


@dataclass(frozen=True, slots=True)
class FundamentalTopNSelector:
    """Select top-N instruments by a configured fundamental metric."""

    rows: tuple[FundamentalUniverseRow, ...]
    top_n: int
    metric: str = "market_cap"

    def __post_init__(self) -> None:
        """Validate selector configuration."""
        if self.top_n <= 0:
            raise ValueError("top_n must be positive")
        if self.metric not in {"market_cap", "dollar_volume"}:
            raise ValueError("unsupported fundamental universe metric")
        object.__setattr__(self, "rows", tuple(self.rows))

    def select_universe(self) -> Iterable[UniverseMember]:
        """Return the top-N instrument IDs by metric descending."""
        ordered = sorted(
            self.rows,
            key=lambda row: (-self._metric_value(row), row.instrument_id.value),
        )
        return tuple(row.instrument_id for row in ordered[: self.top_n])

    def _metric_value(self, row: FundamentalUniverseRow) -> Decimal:
        return row.market_cap if self.metric == "market_cap" else row.dollar_volume


@dataclass(frozen=True, slots=True)
class TopNVolumeSelector:
    """Select top-N instruments by total volume in a completed bar window."""

    bars: tuple[Bar, ...]
    top_n: int

    def __post_init__(self) -> None:
        """Validate volume selector configuration."""
        if self.top_n <= 0:
            raise ValueError("top_n must be positive")
        object.__setattr__(self, "bars", tuple(self.bars))

    def select_universe(self) -> Iterable[UniverseMember]:
        """Return top-N instrument IDs by aggregate volume descending."""
        volume_by_instrument: dict[InstrumentId, Decimal] = {}
        for bar in self.bars:
            if not bar.is_complete:
                continue
            volume_by_instrument[bar.instrument_id] = (
                volume_by_instrument.get(bar.instrument_id, Decimal("0")) + bar.volume
            )
        ordered = sorted(
            volume_by_instrument.items(),
            key=lambda item: (-item[1], item[0].value),
        )
        return tuple(instrument_id for instrument_id, _volume in ordered[: self.top_n])


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


__all__ = [
    "FundamentalTopNSelector",
    "FundamentalUniverseRow",
    "TopNVolumeSelector",
    "Universe",
    "UniverseMember",
    "UniverseSelector",
]
