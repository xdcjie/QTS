"""Dependency bundle for paper/live runtime sessions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import tzinfo
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, RuntimeRunId, StrategyId
from qts.data.sources.streaming_market_data_source import StreamingMarketDataSource
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionAdapter
from qts.runtime.intent_processing import InstrumentExecutionContext
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.sinks.base import RuntimeEventSink
from qts.strategy_sdk import PortfolioView, Strategy

PortfolioViewBuilder = Callable[
    [AccountSnapshot],
    PortfolioView,
]


@dataclass(frozen=True, slots=True)
class LiveRuntimeDependencies:
    """Cohesive dependencies needed to run one paper/live runtime session."""

    strategy: Strategy
    risk_engine: RiskEngine
    instrument_context: InstrumentExecutionContext
    execution_adapter: ExecutionAdapter
    account_actor: AccountActor
    portfolio_view: Callable[..., PortfolioView]
    multiplier_for: Callable[[InstrumentId], Decimal]
    run_id: RuntimeRunId = field(default_factory=lambda: RuntimeRunId("local-live-run"))
    mode: RuntimeMode = RuntimeMode.PAPER_SIMULATED
    execution_environment: ExecutionEnvironment = ExecutionEnvironment.SIMULATED
    account_id: AccountId | None = None
    strategy_id: StrategyId | None = None
    market_data_source: StreamingMarketDataSource | None = None
    sink: RuntimeEventSink | None = None
    instrument_registry: InstrumentRegistry | None = None
    future_roll_registry: FutureRollRegistry | None = None
    contract_multipliers: dict[InstrumentId, Decimal] | None = None
    target_timeframe: str | None = None
    exchange_timezone_by_instrument: dict[InstrumentId, str | tzinfo] | None = None
    warmup_bars: int = 0
    order_submission_enabled: bool = True
    order_id_prefix: str = "live"

    def __post_init__(self) -> None:
        """Validate runtime construction invariants."""
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars must be non-negative")
        if not self.order_id_prefix.strip():
            raise ValueError("order_id_prefix must not be empty")

    @property
    def multipliers(self) -> dict[InstrumentId, Decimal]:
        """Return configured contract multipliers."""
        return dict(self.contract_multipliers or {})

    @property
    def exchange_timezones(self) -> dict[InstrumentId, str | tzinfo]:
        """Return exchange timezones used by market-data aggregation."""
        return dict(self.exchange_timezone_by_instrument or {})


__all__ = ["LiveRuntimeDependencies"]
