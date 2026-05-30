"""Assemble runtime session dependencies and build a real RuntimeSession.

This owns the paper-simulated dependency assembly that integration tests and the
paper runner previously wired by hand: it turns a strategy plus an instrument
registry into a fully-wired :class:`RuntimeSession` running the shared
strategy/risk/order/execution/account chain. It lives in the application layer
because it orchestrates adapters (execution, risk, registry) into runtime
dependencies; the runtime package itself stays free of adapter wiring. Live and
broker assembly stay with the broker startup path; this builder targets paper.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.core.ids import AccountId, InstrumentId
from qts.execution.adapters.simulated_execution_adapter import SimulatedExecutionAdapter
from qts.portfolio.account_snapshot import AccountSnapshot
from qts.registry.instrument_registry import InstrumentRegistry
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actors.account_actor import AccountActor
from qts.runtime.config import BacktestCostModel
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.session import RuntimeSession
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy


@dataclass(frozen=True, slots=True)
class RuntimeStartConfig:
    """Normalize the resolved inputs needed to build a paper runtime session.

    This is the configuration the session builder consumes. It is produced from
    a start-runtime command (and, via the promotion runtime config builder, from
    an approved promotion packet) and stays free of broker or strategy-class
    internals.
    """

    runtime_mode: RuntimeMode
    account_id: AccountId
    initial_cash: Mapping[str, Decimal]

    def __post_init__(self) -> None:
        """Normalize runtime mode and freeze the initial cash mapping."""
        object.__setattr__(self, "runtime_mode", RuntimeMode.from_value(self.runtime_mode))
        object.__setattr__(self, "initial_cash", dict(self.initial_cash))


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
    ) -> RuntimeSessionBuilder:
        """Assemble paper-simulated dependencies from a runtime start config."""
        if config.runtime_mode is not RuntimeMode.PAPER_SIMULATED:
            raise ValueError(
                "RuntimeSessionBuilder.from_runtime_config supports paper_simulated only; "
                f"got {config.runtime_mode.value}"
            )
        account_id = config.account_id
        dependencies = RuntimeSessionDependencies(
            strategy=strategy,
            risk_engine=RiskEngine([]),
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

    @property
    def dependencies(self) -> RuntimeSessionDependencies:
        """Return the assembled runtime session dependencies."""
        return self._dependencies

    def build(self) -> RuntimeSession:
        """Build the real runtime session from the assembled dependencies."""
        return RuntimeSession(self._dependencies)

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
