"""User-facing StrategyContext."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.instruments import OptionRight
from qts.portfolio.holdings import Holding
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
from qts.strategy_sdk.portfolio_construction import PortfolioConstructionModel
from qts.strategy_sdk.portfolio_view import PortfolioView
from qts.strategy_sdk.signals import Signal
from qts.strategy_sdk.subscription_registry import DataSubscription, StrategySubscriptionRegistry
from qts.strategy_sdk.target import OrderSpec, TargetIntent, TargetIntentType
from qts.strategy_sdk.target_emitter import TargetIntentEmitter
from qts.strategy_sdk.universe import Universe, UniverseMember, UniverseSelector


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
    _signals: list[Signal] = field(default_factory=list, init=False)

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
    def signals(self) -> tuple[Signal, ...]:
        """Return pending signals waiting for portfolio construction."""
        return tuple(self._signals)

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

    def target_percent(
        self,
        asset: AssetRef,
        weight: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a portfolio-weight target for an asset."""
        return self._intent_emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.PERCENT,
                value=weight,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def target_quantity(
        self,
        asset: AssetRef,
        quantity: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a quantity target for an asset."""
        return self._intent_emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.QUANTITY,
                value=quantity,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def target_value(
        self,
        asset: AssetRef,
        value: Decimal,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a notional value target for an asset."""
        return self._intent_emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.VALUE,
                value=value,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def close(
        self,
        asset: AssetRef,
        *,
        spec: OrderSpec | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> TargetIntent:
        """Emit a target that closes an asset position."""
        return self._intent_emitter.emit(
            TargetIntent(
                asset=asset,
                intent_type=TargetIntentType.CLOSE,
                value=None,
                order_spec=spec or OrderSpec(),
                metadata=metadata or {},
            )
        )

    def emit_signal(self, signal: Signal) -> Signal:
        """Record a forecast signal for later portfolio construction."""
        self._signals.append(signal)
        return signal

    def construct_targets(
        self,
        model: PortfolioConstructionModel,
    ) -> tuple[TargetIntent, ...]:
        """Construct and emit target intents from pending signals."""
        pending = tuple(self._signals)
        targets = model.construct(pending)
        for target in targets:
            self._intent_emitter.emit(target)
        self._signals.clear()
        return targets

    def holding(self, asset: AssetRef) -> Holding | None:
        """Return the current holding for an asset."""
        if self.portfolio is None:
            return None
        return self.portfolio.holding(asset)

    def unrealized_pnl(self, asset: AssetRef) -> Decimal:
        """Return current unrealized PnL if a portfolio mark is available."""
        if self.portfolio is None:
            return Decimal("0")
        return self.portfolio.unrealized_pnl(asset)

    def realized_pnl(self, asset: AssetRef) -> Decimal:
        """Return cumulative realized PnL for an asset."""
        if self.portfolio is None:
            return Decimal("0")
        return self.portfolio.realized_pnl(asset)

    def avg_cost(self, asset: AssetRef) -> Decimal | None:
        """Return average cost for an asset."""
        if self.portfolio is None:
            return None
        return self.portfolio.avg_cost(asset)

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

    def set_universe_from_selector(self, selector: UniverseSelector) -> Universe:
        """Replace the strategy-declared universe from a selector result."""
        return self.set_universe(selector.select_universe())

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
    "Signal",
]
