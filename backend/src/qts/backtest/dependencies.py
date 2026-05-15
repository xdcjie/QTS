"""Dependency value objects for backtest orchestration."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import tzinfo
from decimal import Decimal
from typing import TYPE_CHECKING

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.risk.rules.max_notional import MaxNotionalRule

if TYPE_CHECKING:
    from qts.reporting.backtest import EquityCurvePoint
    from qts.runtime.actors.execution_actor import ExecutionAdapter
    from qts.runtime.intent_processing import ProcessedIntent
    from qts.strategy_sdk import PortfolioView

ProcessIntentHandler = Callable[..., "ProcessedIntent"]
PortfolioViewBuilder = Callable[..., "PortfolioView"]
EquityPointBuilder = Callable[..., "EquityCurvePoint"]
RollingPriceUpdater = Callable[..., None]
MarketDataProvenanceProvider = Callable[[Bar], Mapping[str, object]]


def empty_market_data_provenance(_: Bar) -> Mapping[str, object]:
    """Return no replay provenance when a caller has none configured."""
    return {}


@dataclass(frozen=True, slots=True)
class BacktestEngineDependencies:
    """Runtime dependencies for constructing and running ``BacktestEngine``."""

    risk_engine: RiskEngine
    instrument_registry: InstrumentRegistry | None = None
    future_roll_registry: FutureRollRegistry | None = None
    contract_multipliers: Mapping[InstrumentId, Decimal] = field(default_factory=dict)
    exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] = field(
        default_factory=dict
    )
    execution_adapter: ExecutionAdapter | None = None

    @classmethod
    def with_defaults(
        cls,
        *,
        initial_cash: Decimal,
        risk_engine: RiskEngine | None = None,
        instrument_registry: InstrumentRegistry | None = None,
        future_roll_registry: FutureRollRegistry | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] | None = None,
        execution_adapter: ExecutionAdapter | None = None,
    ) -> BacktestEngineDependencies:
        """Build runtime dependencies with stable defaults."""
        resolved_risk_engine = (
            risk_engine
            if risk_engine is not None
            else RiskEngine([MaxNotionalRule(max_notional=initial_cash * Decimal("100"))])
        )
        return cls(
            risk_engine=resolved_risk_engine,
            instrument_registry=instrument_registry,
            future_roll_registry=future_roll_registry,
            contract_multipliers=dict(contract_multipliers or {}),
            exchange_timezone_by_instrument=dict(exchange_timezone_by_instrument or {}),
            execution_adapter=execution_adapter,
        )


@dataclass(frozen=True, slots=True)
class BacktestActorLoopConfig:
    """Execution-loop runtime configuration."""

    initial_cash: Decimal
    target_timeframe: str | None = None
    warmup_bars: int = 0

    def __post_init__(self) -> None:
        """Normalize and validate loop runtime settings."""
        object.__setattr__(self, "initial_cash", Decimal(str(self.initial_cash)))
        if self.initial_cash < Decimal("0"):
            raise ValueError("initial_cash must be non-negative")
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars must be non-negative")


@dataclass(frozen=True, slots=True)
class BacktestActorLoopDependencies:
    """Runtime collaborators and policy objects used by ``BacktestActorLoop``."""

    instrument_registry: InstrumentRegistry
    process_intent: ProcessIntentHandler
    portfolio_view: PortfolioViewBuilder
    equity_point: EquityPointBuilder
    update_rolling_prices: RollingPriceUpdater
    market_data_provenance_for: MarketDataProvenanceProvider = empty_market_data_provenance
    contract_multipliers: Mapping[InstrumentId, Decimal] = field(default_factory=dict)
    exchange_timezone_by_instrument: Mapping[InstrumentId, str | tzinfo] = field(
        default_factory=dict
    )
    future_roll_registry: FutureRollRegistry | None = None
    execution_adapter: ExecutionAdapter | None = None


__all__ = [
    "BacktestActorLoopConfig",
    "BacktestActorLoopDependencies",
    "BacktestEngineDependencies",
]
