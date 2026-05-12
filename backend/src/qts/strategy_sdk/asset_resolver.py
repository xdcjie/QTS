"""Strategy symbol and contract resolution helpers."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable

from qts.core.ids import InstrumentId
from qts.domain.instruments import OptionRight
from qts.strategy_sdk.asset_ref import AssetRef


class SymbolResolver(Protocol):
    """Platform-provided symbol resolution boundary."""

    def resolve(self, user_symbol: str) -> InstrumentId: ...


class FutureContractResolver(Protocol):
    """Platform-provided future chain resolution boundary."""

    def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId: ...


@runtime_checkable
class ContinuousFutureResolver(Protocol):
    """Platform-provided continuous future reference boundary."""

    def continuous_instrument_id(self, root_symbol: str, *, offset: int = 0) -> InstrumentId: ...


class OptionContractRef(Protocol):
    """Read-only option contract reference returned by the platform."""

    @property
    def instrument_id(self) -> InstrumentId: ...


class OptionContractResolver(Protocol):
    """Platform-provided option chain resolution boundary."""

    def find(
        self,
        *,
        underlying: InstrumentId,
        expiry: date | None = None,
        strike: Decimal | None = None,
        right: OptionRight | None = None,
    ) -> Sequence[OptionContractRef]: ...


class StrategyAssetResolver:
    """Resolve user input symbols/roots/options into stable `AssetRef` objects."""

    def __init__(
        self,
        *,
        instrument_registry: SymbolResolver | None = None,
        future_chain_registry: FutureContractResolver | ContinuousFutureResolver | None = None,
        option_chain_registry: OptionContractResolver | None = None,
    ) -> None:
        self.instrument_registry = instrument_registry
        self.future_chain_registry = future_chain_registry
        self.option_chain_registry = option_chain_registry

    def resolve_symbol(self, user_symbol: str) -> AssetRef:
        """Perform resolve_symbol."""
        if self.instrument_registry is None:
            raise RuntimeError("instrument registry is not configured")
        instrument_id = self.instrument_registry.resolve(user_symbol)
        return AssetRef(instrument_id=instrument_id, symbol=user_symbol)

    def resolve_future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        """Perform resolve_future."""
        if self.future_chain_registry is None:
            raise RuntimeError("future chain registry is not configured")
        if contract != "front":
            raise ValueError("only front future contract selection is supported")
        if isinstance(self.future_chain_registry, ContinuousFutureResolver):
            instrument_id = self.future_chain_registry.continuous_instrument_id(
                root_symbol, offset=0
            )
        else:
            instrument_id = self.future_chain_registry.resolve_contract(root_symbol, offset=0)
        return AssetRef(
            instrument_id=instrument_id,
            symbol=root_symbol,
            metadata={"contract": contract},
        )

    def resolve_option(
        self,
        *,
        underlying: InstrumentId,
        expiry: date,
        strike: Decimal,
        right: OptionRight,
    ) -> AssetRef:
        """Perform resolve_option."""
        if self.option_chain_registry is None:
            raise RuntimeError("option chain registry is not configured")
        matches = self.option_chain_registry.find(
            underlying=underlying,
            expiry=expiry,
            strike=strike,
            right=right,
        )
        if not matches:
            raise KeyError("no option contract matched selection")
        option = matches[0]
        return AssetRef(instrument_id=option.instrument_id, symbol=str(option.instrument_id))


__all__ = [
    "ContinuousFutureResolver",
    "FutureContractResolver",
    "OptionContractRef",
    "OptionContractResolver",
    "SymbolResolver",
    "StrategyAssetResolver",
]
