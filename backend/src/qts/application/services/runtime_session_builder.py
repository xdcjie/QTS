"""Assemble runtime session dependencies and build a real RuntimeSession.

This owns the application-layer dependency assembly for paper-simulated and
broker-capable paper/live runtimes: it turns resolved start inputs, strategy
code, instrument metadata, and boundary adapters into a fully-wired
:class:`RuntimeSession` running the shared strategy/risk/order/execution/account
chain. The runtime package stays free of adapter construction and config
parsing; real broker transports are injected at this boundary.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.core.ids import AccountId, InstrumentId
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.execution.execution_adapter import ExecutionAdapter
from qts.portfolio.account_snapshot import AccountSnapshot
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.broker_startup import BrokerRuntimeStartupDecision
from qts.runtime.config import BacktestCostModel
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.live_capital import LiveCapitalOrderDecision
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.session import RuntimeSession
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy


@dataclass(frozen=True, slots=True)
class RuntimeStartConfig:
    """Normalize the resolved inputs needed to build a runtime session.

    This is the configuration the session builder consumes. It is produced from
    a start-runtime command (and, via the promotion runtime config builder, from
    an approved promotion packet) and stays free of broker or strategy-class
    internals.
    """

    runtime_mode: RuntimeMode | str
    account_id: AccountId
    initial_cash: Mapping[str, Decimal]
    startup_decision: BrokerRuntimeStartupDecision | None = None
    live_capital_decision: LiveCapitalOrderDecision | None = None

    def __post_init__(self) -> None:
        """Normalize runtime mode and freeze the initial cash mapping."""
        runtime_mode = RuntimeMode.from_value(self.runtime_mode)
        object.__setattr__(self, "runtime_mode", runtime_mode)
        object.__setattr__(self, "initial_cash", dict(self.initial_cash))
        if self.startup_decision is not None and self.startup_decision.mode is not runtime_mode:
            raise ValueError("startup_decision mode must match runtime_mode")
        if self.live_capital_decision is not None and runtime_mode is not RuntimeMode.LIVE:
            raise ValueError("live_capital_decision is only valid for live runtime")


class RuntimeSessionBuilder:
    """Assemble runtime session dependencies and build a real RuntimeSession."""

    def __init__(self, dependencies: RuntimeSessionDependencies) -> None:
        """Create a builder around fully-assembled session dependencies."""
        self._dependencies = dependencies

    @classmethod
    def from_runtime_config(
        cls,
        config: RuntimeStartConfig,
        *,
        strategy: Strategy,
        instrument_registry: InstrumentRegistry,
        execution_adapter: ExecutionAdapter | None = None,
    ) -> RuntimeSessionBuilder:
        """Assemble runtime dependencies from a resolved start config."""
        account_id = config.account_id
        runtime_mode = RuntimeMode.from_value(config.runtime_mode)
        if runtime_mode is not RuntimeMode.PAPER_SIMULATED:
            return cls._from_broker_runtime_config(
                config,
                strategy=strategy,
                instrument_registry=instrument_registry,
                execution_adapter=execution_adapter,
            )
        dependencies = RuntimeSessionDependencies(
            strategy=strategy,
            # Order-submitting paper runtimes must enforce the same mandatory risk
            # floor as backtest, never an empty (all-orders-approved) engine. Using
            # the shared baseline keeps the paper risk gate identical to the one the
            # promotion-feeding backtest cleared.
            risk_engine=RiskEngine.with_baseline_floor(
                sum(config.initial_cash.values(), Decimal("0"))
            ),
            instrument_context=BacktestInstrumentContext(instrument_registry=instrument_registry),
            execution_adapter=SimulatedExecutionAdapter(cost_model=BacktestCostModel()),
            account_actor=AccountActor(
                initial_cash=dict(config.initial_cash),
                account_id=account_id,
            ),
            instrument_registry=instrument_registry,
            portfolio_view=cls._paper_portfolio_view,
            multiplier_for=cls._multiplier_for(instrument_registry),
            account_id=account_id,
            mode=RuntimeMode.PAPER_SIMULATED,
            execution_environment=ExecutionEnvironment.SIMULATED,
        )
        return cls(dependencies)

    @classmethod
    def _from_broker_runtime_config(
        cls,
        config: RuntimeStartConfig,
        *,
        strategy: Strategy,
        instrument_registry: InstrumentRegistry,
        execution_adapter: ExecutionAdapter | None,
    ) -> RuntimeSessionBuilder:
        """Assemble broker-capable paper/live dependencies from boundary adapters."""
        runtime_mode = RuntimeMode.from_value(config.runtime_mode)
        if config.startup_decision is None:
            raise ValueError(f"{runtime_mode.value} runtime requires startup_decision")
        if execution_adapter is None:
            raise ValueError(f"{runtime_mode.value} runtime requires execution_adapter")
        if (
            runtime_mode is RuntimeMode.LIVE
            and config.startup_decision.real_order_submission_enabled
            and config.live_capital_decision is None
        ):
            raise ValueError("live runtime requires live_capital_decision")
        account_id = config.account_id
        initial_equity = sum(config.initial_cash.values(), Decimal("0"))
        dependencies = RuntimeSessionDependencies(
            strategy=strategy,
            risk_engine=RiskEngine.with_baseline_floor(initial_equity),
            instrument_context=BacktestInstrumentContext(instrument_registry=instrument_registry),
            execution_adapter=execution_adapter,
            account_actor=AccountActor(
                initial_cash=dict(config.initial_cash),
                account_id=account_id,
            ),
            instrument_registry=instrument_registry,
            portfolio_view=cls._paper_portfolio_view,
            multiplier_for=cls._multiplier_for(instrument_registry),
            account_id=account_id,
            mode=runtime_mode,
            execution_environment=ExecutionEnvironment.from_value(None, mode=runtime_mode),
            order_submission_enabled=cls._order_submission_enabled(config),
            startup_decision=config.startup_decision,
            live_capital_decision=config.live_capital_decision,
            order_id_prefix=cls._order_id_prefix(runtime_mode),
        )
        return cls(dependencies)

    @property
    def dependencies(self) -> RuntimeSessionDependencies:
        """Return the assembled runtime session dependencies."""
        return self._dependencies

    def build(self) -> RuntimeSession:
        """Build the real runtime session from the assembled dependencies."""
        return RuntimeSession(self._dependencies)

    @staticmethod
    def _order_submission_enabled(config: RuntimeStartConfig) -> bool:
        mode = RuntimeMode.from_value(config.runtime_mode)
        if mode is RuntimeMode.PAPER_BROKER:
            return config.startup_decision is not None and (
                config.startup_decision.order_permission.allows_order_submission
            )
        if mode is RuntimeMode.LIVE_OBSERVATION:
            return False
        if mode is RuntimeMode.LIVE:
            return config.startup_decision is not None and (
                config.startup_decision.order_permission.allows_order_submission
            )
        return True

    @staticmethod
    def _order_id_prefix(mode: RuntimeMode) -> str:
        if mode is RuntimeMode.PAPER_BROKER:
            return "paper"
        return "live"

    @staticmethod
    def _multiplier_for(
        instrument_registry: InstrumentRegistry,
    ) -> Callable[[InstrumentId], Decimal]:
        def multiplier_for(instrument_id: InstrumentId) -> Decimal:
            return instrument_registry.get_contract_spec(instrument_id).multiplier

        return multiplier_for

    @staticmethod
    def _paper_portfolio_view(
        snapshot: AccountSnapshot,
        *,
        latest_prices: Mapping[InstrumentId, Decimal],
    ) -> PortfolioView:
        positions = {
            instrument_id: PortfolioPosition(
                quantity=position.quantity,
                market_value=position.quantity * latest_prices.get(instrument_id, Decimal("0")),
            )
            for instrument_id, position in snapshot.positions.items()
        }
        cash = snapshot.cash.get("USD", Decimal("0"))
        equity = cash + sum(
            (position.market_value for position in positions.values()),
            Decimal("0"),
        )
        return PortfolioView(cash=cash, equity=equity, positions=positions)


__all__ = ["RuntimeSessionBuilder", "RuntimeStartConfig"]
