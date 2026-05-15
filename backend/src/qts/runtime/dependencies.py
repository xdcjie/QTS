"""Dependency bundle for broker-capable runtime sessions."""

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
from qts.runtime.live import BrokerRuntimeStartupDecision
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.sinks.base import RuntimeEventSink
from qts.runtime.state_recovery import SnapshotStore
from qts.runtime.topology import RuntimeTopology
from qts.strategy_sdk import PortfolioView, Strategy

PortfolioViewBuilder = Callable[
    [AccountSnapshot],
    PortfolioView,
]


@dataclass(frozen=True, slots=True)
class RuntimeSessionDependencies:
    """Cohesive dependencies needed to run one broker-capable runtime session."""

    risk_engine: RiskEngine
    instrument_context: InstrumentExecutionContext
    execution_adapter: ExecutionAdapter
    account_actor: AccountActor
    portfolio_view: Callable[..., PortfolioView]
    multiplier_for: Callable[[InstrumentId], Decimal]
    risk_engines: dict[AccountId, RiskEngine] | None = None
    strategy: Strategy | None = None
    strategies: tuple[Strategy, ...] | None = None
    run_id: RuntimeRunId = field(default_factory=lambda: RuntimeRunId("local-live-run"))
    mode: RuntimeMode = RuntimeMode.PAPER_SIMULATED
    execution_environment: ExecutionEnvironment = ExecutionEnvironment.SIMULATED
    account_id: AccountId | None = None
    strategy_id: StrategyId | None = None
    market_data_source: StreamingMarketDataSource | None = None
    sink: RuntimeEventSink | None = None
    snapshot_store: SnapshotStore | None = None
    snapshot_stores: dict[AccountId, SnapshotStore] | None = None
    runtime_topology: RuntimeTopology | None = None
    account_actors: dict[AccountId, AccountActor] | None = None
    instrument_registry: InstrumentRegistry | None = None
    future_roll_registry: FutureRollRegistry | None = None
    contract_multipliers: dict[InstrumentId, Decimal] | None = None
    target_timeframe: str | None = None
    exchange_timezone_by_instrument: dict[InstrumentId, str | tzinfo] | None = None
    warmup_bars: int = 0
    order_submission_enabled: bool = True
    startup_decision: BrokerRuntimeStartupDecision | None = None
    order_id_prefix: str = "live"

    def __post_init__(self) -> None:
        """Validate runtime construction invariants."""
        if self.strategies is not None:
            if self.strategy is not None:
                raise ValueError("provide either strategy or strategies, not both")
            if len(self.strategies) == 0:
                raise ValueError("strategies must not be empty when provided")
            if self.runtime_topology is None:
                raise ValueError("runtime topology is required when strategies are provided")
        if self.strategy is None and (self.strategies is None or len(self.strategies) == 0):
            raise ValueError("strategy or strategies is required")
        if self.warmup_bars < 0:
            raise ValueError("warmup_bars must be non-negative")
        if (
            self.runtime_topology is not None
            and len(self.runtime_topology.accounts) > 1
            and self.account_actors is None
        ):
            raise ValueError("multi-account runtime topology requires account_actors mapping")
        if self.runtime_topology is not None and self.account_actors is not None:
            missing_accounts = [
                str(account.account_id)
                for account in self.runtime_topology.accounts
                if account.account_id not in self.account_actors
            ]
            if missing_accounts:
                raise ValueError(
                    "account_actors missing for topology accounts: "
                    + ", ".join(sorted(missing_accounts))
                )
        if not self.order_id_prefix.strip():
            raise ValueError("order_id_prefix must not be empty")
        if self.startup_decision is not None and self.startup_decision.mode is not self.mode:
            raise ValueError("startup decision mode must match runtime mode")

    @property
    def multipliers(self) -> dict[InstrumentId, Decimal]:
        """Return configured contract multipliers."""
        return dict(self.contract_multipliers or {})

    @property
    def exchange_timezones(self) -> dict[InstrumentId, str | tzinfo]:
        """Return exchange timezones used by market-data aggregation."""
        return dict(self.exchange_timezone_by_instrument or {})


LiveRuntimeDependencies = RuntimeSessionDependencies


__all__ = [
    "LiveRuntimeDependencies",
    "RuntimeSessionDependencies",
]
