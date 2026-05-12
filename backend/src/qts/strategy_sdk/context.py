"""User-facing StrategyContext."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.instruments import OptionRight
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.asset_resolver import (
    ContinuousFutureResolver,
    FutureContractResolver,
    OptionContractRef,
    OptionContractResolver,
    StrategyAssetResolver,
    SymbolResolver,
)
from qts.strategy_sdk.data_view import DataView
from qts.strategy_sdk.factors import FactorFactory
from qts.strategy_sdk.indicators import IndicatorFactory
from qts.strategy_sdk.portfolio_view import PortfolioView
from qts.strategy_sdk.subscription_registry import DataSubscription, StrategySubscriptionRegistry
from qts.strategy_sdk.target import TargetIntent, TargetIntentType
from qts.strategy_sdk.target_emitter import TargetIntentEmitter


@dataclass(slots=True)
class StrategyContext:
    """User-facing strategy context."""

    instrument_registry: SymbolResolver | None = None
    future_chain_registry: FutureContractResolver | ContinuousFutureResolver | None = None
    option_chain_registry: OptionContractResolver | None = None
    data: DataView | None = None
    portfolio: PortfolioView | None = None
    indicator: IndicatorFactory = field(default_factory=IndicatorFactory)
    factor: FactorFactory = field(default_factory=FactorFactory)
    _asset_resolver: StrategyAssetResolver = field(init=False)
    _intent_emitter: TargetIntentEmitter = field(default_factory=TargetIntentEmitter, init=False)
    _subscription_registry: StrategySubscriptionRegistry = field(
        default_factory=StrategySubscriptionRegistry, init=False
    )

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        self._asset_resolver = StrategyAssetResolver(
            instrument_registry=self.instrument_registry,
            future_chain_registry=self.future_chain_registry,
            option_chain_registry=self.option_chain_registry,
        )

    @property
    def intents(self) -> tuple[TargetIntent, ...]:
        """Perform intents."""
        return self._intent_emitter.intents

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        """Perform subscriptions."""
        return self._subscription_registry.subscriptions

    def symbol(self, user_symbol: str) -> AssetRef:
        """Perform symbol."""
        return self._asset_resolver.resolve_symbol(user_symbol)

    def future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        """Perform future."""
        return self._asset_resolver.resolve_future(root_symbol, contract=contract)

    def option(
        self,
        *,
        underlying: InstrumentId,
        expiry: date,
        strike: Decimal,
        right: OptionRight,
    ) -> AssetRef:
        """Perform option."""
        return self._asset_resolver.resolve_option(
            underlying=underlying,
            expiry=expiry,
            strike=strike,
            right=right,
        )

    def target_percent(self, asset: AssetRef, weight: Decimal) -> TargetIntent:
        """Perform target_percent."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.PERCENT, value=weight)
        )

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> TargetIntent:
        """Perform target_quantity."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.QUANTITY, value=quantity)
        )

    def target_value(self, asset: AssetRef, value: Decimal) -> TargetIntent:
        """Perform target_value."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.VALUE, value=value)
        )

    def close(self, asset: AssetRef) -> TargetIntent:
        """Perform close."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.CLOSE, value=None)
        )

    def rebalance(self, weights: dict[AssetRef, Decimal]) -> tuple[TargetIntent, ...]:
        """Perform rebalance."""
        return tuple(self.target_percent(asset, weight) for asset, weight in weights.items())

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> DataSubscription:
        """Perform subscribe."""
        subscription = DataSubscription(asset=asset, timeframe=timeframe, warmup=warmup)
        return self._subscription_registry.subscribe(subscription)


__all__ = [
    "DataSubscription",
    "ContinuousFutureResolver",
    "FutureContractResolver",
    "OptionContractRef",
    "OptionContractResolver",
    "StrategyAssetResolver",
    "SymbolResolver",
    "StrategyContext",
]
