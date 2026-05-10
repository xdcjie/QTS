"""User-facing StrategyContext."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Protocol

from qts.core.ids import InstrumentId
from qts.domain.instruments import OptionRight
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.data_view import DataView
from qts.strategy_sdk.factors import FactorFactory
from qts.strategy_sdk.indicators import IndicatorFactory
from qts.strategy_sdk.portfolio_view import PortfolioView
from qts.strategy_sdk.target import TargetIntent, TargetIntentType


class SymbolResolver(Protocol):
    """Platform-provided symbol resolution boundary."""

    def resolve(self, user_symbol: str) -> InstrumentId: ...


class FutureContractResolver(Protocol):
    """Platform-provided future chain resolution boundary."""

    def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId: ...


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


@dataclass(slots=True)
class DataSubscription:
    """Strategy-declared market data requirement."""

    asset: AssetRef
    timeframe: str
    warmup: int

    def __post_init__(self) -> None:
        if not self.timeframe.strip():
            raise ValueError("timeframe must not be empty")
        if self.warmup <= 0:
            raise ValueError("warmup must be positive")


@dataclass(slots=True)
class StrategyContext:
    """User-facing strategy context."""

    instrument_registry: SymbolResolver | None = None
    future_chain_registry: FutureContractResolver | None = None
    option_chain_registry: OptionContractResolver | None = None
    data: DataView | None = None
    portfolio: PortfolioView | None = None
    indicator: IndicatorFactory = field(default_factory=IndicatorFactory)
    factor: FactorFactory = field(default_factory=FactorFactory)
    _intents: list[TargetIntent] = field(default_factory=list, init=False)
    _subscriptions: list[DataSubscription] = field(default_factory=list, init=False)

    @property
    def intents(self) -> tuple[TargetIntent, ...]:
        return tuple(self._intents)

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        return tuple(self._subscriptions)

    def symbol(self, user_symbol: str) -> AssetRef:
        if self.instrument_registry is None:
            raise RuntimeError("instrument registry is not configured")
        instrument_id = self.instrument_registry.resolve(user_symbol)
        return AssetRef(instrument_id=instrument_id, symbol=user_symbol)

    def future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        if self.future_chain_registry is None:
            raise RuntimeError("future chain registry is not configured")
        if contract != "front":
            raise ValueError("only front future contract selection is supported")
        instrument_id = self.future_chain_registry.resolve_contract(root_symbol, offset=0)
        return AssetRef(
            instrument_id=instrument_id,
            symbol=root_symbol,
            metadata={"contract": contract},
        )

    def option(
        self,
        *,
        underlying: InstrumentId,
        expiry: date,
        strike: Decimal,
        right: OptionRight,
    ) -> AssetRef:
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

    def target_percent(self, asset: AssetRef, weight: Decimal) -> TargetIntent:
        return self._emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.PERCENT, value=weight)
        )

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> TargetIntent:
        return self._emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.QUANTITY, value=quantity)
        )

    def target_value(self, asset: AssetRef, value: Decimal) -> TargetIntent:
        return self._emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.VALUE, value=value)
        )

    def close(self, asset: AssetRef) -> TargetIntent:
        return self._emit(TargetIntent(asset=asset, intent_type=TargetIntentType.CLOSE, value=None))

    def rebalance(self, weights: dict[AssetRef, Decimal]) -> tuple[TargetIntent, ...]:
        return tuple(self.target_percent(asset, weight) for asset, weight in weights.items())

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> DataSubscription:
        subscription = DataSubscription(asset=asset, timeframe=timeframe, warmup=warmup)
        self._subscriptions.append(subscription)
        return subscription

    def _emit(self, intent: TargetIntent) -> TargetIntent:
        self._intents.append(intent)
        return intent


__all__ = [
    "DataSubscription",
    "FutureContractResolver",
    "OptionContractRef",
    "OptionContractResolver",
    "StrategyContext",
    "SymbolResolver",
]
