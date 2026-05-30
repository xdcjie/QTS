"""Option chain registry."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.instruments import AssetClass, Instrument, OptionRight, OptionSpec


class OptionChainRegistry:
    """Lookup option instruments by underlying and simple filters."""

    def __init__(self) -> None:
        """Initialize an empty option chain keyed by underlying instrument."""
        self._chains: dict[InstrumentId, list[Instrument]] = {}

    def register(self, option: Instrument) -> None:
        """Add an option instrument to its underlying's chain."""
        if option.asset_class is not AssetClass.OPTION or not isinstance(
            option.derivative, OptionSpec
        ):
            raise ValueError("option chain can only register option instruments")
        self._chains.setdefault(option.derivative.underlying, []).append(option)

    def options_for(self, underlying: InstrumentId) -> list[Instrument]:
        """Return all registered options for an underlying instrument."""
        try:
            return list(self._chains[underlying])
        except KeyError as exc:
            raise KeyError(f"missing option chain: {underlying}") from exc

    def find(
        self,
        *,
        underlying: InstrumentId,
        expiry: date | None = None,
        strike: Decimal | None = None,
        right: OptionRight | None = None,
    ) -> list[Instrument]:
        """Return options for an underlying filtered by expiry, strike, and right."""
        matches = self.options_for(underlying)
        if expiry is not None:
            matches = [
                option
                for option in matches
                if isinstance(option.derivative, OptionSpec) and option.derivative.expiry == expiry
            ]
        if strike is not None:
            matches = [
                option
                for option in matches
                if isinstance(option.derivative, OptionSpec) and option.derivative.strike == strike
            ]
        if right is not None:
            matches = [
                option
                for option in matches
                if isinstance(option.derivative, OptionSpec) and option.derivative.right is right
            ]
        return matches


__all__ = ["OptionChainRegistry"]
