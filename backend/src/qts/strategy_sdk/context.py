"""User-facing StrategyContext."""

from __future__ import annotations

from collections.abc import Iterable
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
from qts.strategy_sdk.universe import Universe, UniverseMember


@dataclass(slots=True)
class StrategyContext:
    """User-facing strategy facade for data, assets, targets, and subscriptions."""

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
    _universe: Universe = field(default_factory=Universe.empty, init=False)

    def __post_init__(self) -> None:
        """Initialize internal SDK collaborators."""
        self._asset_resolver = StrategyAssetResolver(
            instrument_registry=self.instrument_registry,
            future_chain_registry=self.future_chain_registry,
            option_chain_registry=self.option_chain_registry,
        )

    @property
    def intents(self) -> tuple[TargetIntent, ...]:
        """Return target intents emitted by the strategy."""
        return self._intent_emitter.intents

    @property
    def subscriptions(self) -> tuple[DataSubscription, ...]:
        """Return market data subscriptions requested by the strategy."""
        return self._subscription_registry.subscriptions

    @property
    def universe(self) -> Universe:
        """Return the current strategy-declared universe."""
        return self._universe

    def symbol(self, user_symbol: str) -> AssetRef:
        """Resolve a user-facing symbol such as ``AAPL``."""
        return self._asset_resolver.resolve_symbol(user_symbol)

    def future(self, root_symbol: str, *, contract: str = "front") -> AssetRef:
        """Resolve a futures root to a selectable contract reference."""
        return self._asset_resolver.resolve_future(root_symbol, contract=contract)

    def option(
        self,
        *,
        underlying: str | AssetRef | InstrumentId,
        expiry: date,
        strike: Decimal,
        right: OptionRight,
    ) -> AssetRef:
        """Resolve an option by underlying symbol/ref and contract attributes."""
        return self._asset_resolver.resolve_option(
            underlying=underlying,
            expiry=expiry,
            strike=strike,
            right=right,
        )

    def target_percent(self, asset: AssetRef, weight: Decimal) -> TargetIntent:
        """Emit a portfolio-weight target for an asset."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.PERCENT, value=weight)
        )

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> TargetIntent:
        """Emit a quantity target for an asset."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.QUANTITY, value=quantity)
        )

    def target_value(self, asset: AssetRef, value: Decimal) -> TargetIntent:
        """Emit a notional value target for an asset."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.VALUE, value=value)
        )

    def close(self, asset: AssetRef) -> TargetIntent:
        """Emit a target that closes an asset position."""
        return self._intent_emitter.emit(
            TargetIntent(asset=asset, intent_type=TargetIntentType.CLOSE, value=None)
        )

    def rebalance(self, weights: dict[AssetRef, Decimal]) -> tuple[TargetIntent, ...]:
        """Emit one percent target per asset in ``weights``."""
        return tuple(self.target_percent(asset, weight) for asset, weight in weights.items())

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> DataSubscription:
        """Subscribe to bars for an asset and timeframe."""
        subscription = DataSubscription(asset=asset, timeframe=timeframe, warmup=warmup)
        return self._subscription_registry.subscribe(subscription)

    def set_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Replace the strategy-declared universe."""
        self._universe = Universe.from_members(members)
        return self._universe

    def add_to_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Add members to the strategy-declared universe."""
        self._universe = self._universe.add(members)
        return self._universe

    def remove_from_universe(self, members: Iterable[UniverseMember]) -> Universe:
        """Remove members from the strategy-declared universe."""
        self._universe = self._universe.remove(members)
        return self._universe


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
