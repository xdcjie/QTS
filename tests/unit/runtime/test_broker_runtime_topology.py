from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Any

import pytest
from qts.core.ids import (
    AccountId,
    BrokerId,
    CorrelationId,
    InstrumentId,
    OrderId,
    RuntimeRunId,
    StrategyId,
)
from qts.domain.orders import ExecutionReport, ExecutionReportStatus, OrderIntent
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actors.account_actor import AccountActor, AccountSnapshot
from qts.runtime.broker_runtime_topology import BrokerRuntimeTopologyResolver
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.topology import (
    AccountRuntimeSpec,
    BrokerRouteSpec,
    MarketDataRouteSpec,
    RuntimeTopology,
    StrategyRuntimeSpec,
)
from qts.strategy_sdk import PortfolioPosition, PortfolioView, Strategy


class _ExecutionAdapter:
    """Execution adapter stub that returns accepted/cancelled execution reports."""

    def __init__(self) -> None:
        self._counter = 0

    def execute_market_order(
        self,
        intent: OrderIntent,
        *,
        broker_order_id: str,
        market_price: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
        bar_time: object | None = None,
    ) -> ExecutionReport:
        """Return a synthetic accepted execution report."""
        _ = intent, account_id, strategy_id, client_order_id, correlation_id
        self._counter += 1
        return ExecutionReport(
            report_id=f"report-{self._counter}",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
            filled_quantity=Decimal("0"),
            fill_price=market_price,
            fill_id=None,
            commission=Decimal("0"),
            slippage=Decimal("0"),
        )

    def cancel_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Return a synthetic cancelled execution report."""
        _ = order_id, account_id, strategy_id, client_order_id, correlation_id
        self._counter += 1
        return ExecutionReport(
            report_id=f"report-{self._counter}",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.CANCELLED,
            filled_quantity=Decimal("0"),
            fill_id=None,
            commission=Decimal("0"),
            slippage=Decimal("0"),
        )

    def replace_order(
        self,
        order_id: OrderId,
        *,
        broker_order_id: str,
        new_quantity: Decimal,
        account_id: AccountId,
        strategy_id: StrategyId,
        client_order_id: str,
        correlation_id: CorrelationId,
    ) -> ExecutionReport:
        """Return a synthetic accepted replace execution report."""
        _ = order_id, new_quantity, account_id, strategy_id, client_order_id, correlation_id
        self._counter += 1
        return ExecutionReport(
            report_id=f"report-{self._counter}",
            broker_order_id=broker_order_id,
            status=ExecutionReportStatus.ACCEPTED,
            filled_quantity=Decimal("0"),
            fill_id=None,
            commission=Decimal("0"),
            slippage=Decimal("0"),
        )


class _Strategy(Strategy):
    pass


class _InstrumentContext:
    def order_instrument_for_intent(self, intent: Any, *, bar: object) -> InstrumentId:
        return InstrumentId(intent.asset.instrument_id.value)

    def market_price_for_intent(
        self,
        intent: object,
        *,
        instrument_id: InstrumentId,
        bar: object,
    ) -> Decimal:
        return Decimal("100")

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        return False

    def related_contracts_for(
        self, continuous_instrument_id: InstrumentId
    ) -> frozenset[InstrumentId]:
        return frozenset()


def _portfolio_view(
    snapshot: AccountSnapshot,
    *,
    latest_prices: Mapping[InstrumentId, Decimal],
) -> PortfolioView:
    return PortfolioView(
        cash=snapshot.cash["USD"],
        equity=snapshot.cash["USD"],
        positions={
            instrument_id: PortfolioPosition(
                quantity=position.quantity,
                market_value=position.quantity * latest_prices.get(instrument_id, Decimal("0")),
            )
            for instrument_id, position in snapshot.positions.items()
        },
    )


def _deps(
    strategy: Strategy,
    *,
    strategies: tuple[Strategy, ...] | None = None,
    runtime_topology: RuntimeTopology | None = None,
    account_id: AccountId | None = None,
    strategy_id: StrategyId | None = None,
    account_actors: dict[AccountId, AccountActor] | None = None,
    risk_engines: dict[AccountId, RiskEngine] | None = None,
) -> RuntimeSessionDependencies:
    return RuntimeSessionDependencies(
        strategy=None if strategies is not None else strategy,
        strategies=strategies,
        risk_engine=RiskEngine([]),
        instrument_context=_InstrumentContext(),
        execution_adapter=_ExecutionAdapter(),
        account_actor=AccountActor(
            initial_cash={"USD": Decimal("10000")},
            account_id=account_id,
        ),
        instrument_registry=None,
        future_roll_registry=None,
        portfolio_view=_portfolio_view,
        multiplier_for=lambda instrument_id: Decimal("1"),
        runtime_topology=runtime_topology,
        account_actors=account_actors,
        risk_engines=risk_engines,
        account_id=account_id,
        strategy_id=strategy_id,
    )


def _topology(
    *,
    mode: RuntimeMode,
    account_ids: tuple[AccountId, ...],
    strategy_specs: tuple[tuple[str, tuple[InstrumentId, ...]], ...],
) -> RuntimeTopology:
    return RuntimeTopology(
        run_id=RuntimeRunId("live-topology-builder"),
        mode=mode,
        accounts=tuple(
            AccountRuntimeSpec(
                account_id=account_id,
                initial_cash=Decimal("10000"),
            )
            for account_id in account_ids
        ),
        strategies=tuple(
            StrategyRuntimeSpec(
                strategy_id=StrategyId(strategy_id),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=account_id,
                subscriptions=subscription_ids,
            )
            for strategy_id, account_id, subscription_ids in (
                (
                    strategy_id,
                    account_ids[min(index, len(account_ids) - 1)],
                    subscriptions,
                )
                for index, (strategy_id, subscriptions) in enumerate(strategy_specs)
            )
        ),
        broker_routes=tuple(
            BrokerRouteSpec(
                broker_id=BrokerId("broker"),
                account_id=account_id,
                execution_adapter_type="ibkr",
                order_transport_type="ib_async",
                execution_environment=ExecutionEnvironment.SIMULATED,
            )
            for account_id in account_ids
        ),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )


def test_broker_runtime_topology_resolver_defaults_for_non_topology_execution() -> None:
    builder = BrokerRuntimeTopologyResolver(
        _deps(strategy=_Strategy(), account_id=AccountId("acct-default"))
    )
    resolved = builder.build()

    assert len(resolved.account_partitions) == 1
    assert resolved.resolved_account_id == AccountId("acct-default")
    assert resolved.resolved_strategy_id == StrategyId("strategy")
    assert resolved.strategy_bindings[0].strategy_id == StrategyId("strategy")


def test_runtime_topology_resolver_uses_account_scoped_risk_engines() -> None:
    account_a = AccountId("acct-a")
    account_b = AccountId("acct-b")
    risk_a = RiskEngine([])
    risk_b = RiskEngine([])
    topology = _topology(
        mode=RuntimeMode.PAPER_SIMULATED,
        account_ids=(account_a, account_b),
        strategy_specs=(
            ("strategy-a", (InstrumentId("EQUITY.US.NASDAQ.AAPL"),)),
            ("strategy-b", (InstrumentId("EQUITY.US.NASDAQ.MSFT"),)),
        ),
    )

    resolved = BrokerRuntimeTopologyResolver(
        _deps(
            strategy=_Strategy(),
            strategies=(_Strategy(), _Strategy()),
            runtime_topology=topology,
            account_actors={
                account_a: AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=account_a,
                ),
                account_b: AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=account_b,
                ),
            },
            risk_engines={account_a: risk_a, account_b: risk_b},
        )
    ).build()

    assert resolved.account_partitions[account_a].risk_engine is risk_a
    assert resolved.account_partitions[account_b].risk_engine is risk_b


def test_broker_runtime_topology_resolver_uses_topology_fallback_subscriptions() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-fallback"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-topo"),
            ),
        ),
        broker_routes=(
            BrokerRouteSpec(
                broker_id=BrokerId("broker"),
                account_id=AccountId("acct-topo"),
                execution_adapter_type="ibkr",
                order_transport_type="ib_async",
                execution_environment=ExecutionEnvironment.SIMULATED,
            ),
        ),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(
                    InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                    InstrumentId("EQUITY.US.NASDAQ.GOOG"),
                ),
            ),
        ),
    )

    builder = BrokerRuntimeTopologyResolver(_deps(strategy=_Strategy(), runtime_topology=topology))
    resolved = builder.build()

    assert resolved.strategy_bindings[0].subscriptions == (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.GOOG"),
    )


def test_broker_runtime_topology_resolver_builds_single_partition() -> None:
    topology = _topology(
        mode=RuntimeMode.PAPER_SIMULATED,
        account_ids=(AccountId("acct-topo"),),
        strategy_specs=(("strat-topo", ()),),
    )
    builder = BrokerRuntimeTopologyResolver(
        _deps(
            strategy=_Strategy(),
            runtime_topology=topology,
            account_id=AccountId("acct-topo"),
        )
    )
    resolved = builder.build()

    assert len(resolved.account_partitions) == 1
    assert AccountId("acct-topo") in resolved.account_partitions
    assert resolved.strategy_bindings[0].account_id == AccountId("acct-topo")


def test_broker_runtime_topology_resolver_builds_multi_account_partitions() -> None:
    account_a = AccountId("acct-a")
    account_b = AccountId("acct-b")
    account_actors = {
        account_a: AccountActor(
            initial_cash={"USD": Decimal("10000")},
            account_id=account_a,
        ),
        account_b: AccountActor(
            initial_cash={"USD": Decimal("10000")},
            account_id=account_b,
        ),
    }
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-multi"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-a"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-b"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=account_b,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    builder = BrokerRuntimeTopologyResolver(
        RuntimeSessionDependencies(
            strategies=(_Strategy(), _Strategy()),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_ExecutionAdapter(),
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
            account_actors=account_actors,
            instrument_registry=None,
        )
    )
    resolved = builder.build()

    assert resolved.account_partitions.keys() == {account_a, account_b}


def test_broker_runtime_topology_resolver_rejects_strategy_instance_count_mismatch() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-mismatch"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-topo"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(ValueError, match="strategy count does not match"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategies=(_Strategy(), _Strategy()),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                instrument_registry=None,
            )
        ).build()


def test_broker_runtime_topology_resolver_rejects_backtest_mode() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-backtest"),
        mode=RuntimeMode.BACKTEST,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-topo"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(ValueError, match="cannot run backtest topology"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategy=_Strategy(),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=AccountId("acct-topo"),
                ),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                account_id=AccountId("acct-topo"),
                mode=RuntimeMode.BACKTEST,
                instrument_registry=None,
            )
        ).build()


def test_broker_runtime_topology_resolver_rejects_multi_account_without_account_actors() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-multi-no-actors"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-a"),
                initial_cash=Decimal("10000"),
            ),
            AccountRuntimeSpec(
                account_id=AccountId("acct-b"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-a"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-a"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-b"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-b"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="multi-account runtime topology requires account_actors mapping",
    ):
        RuntimeSessionDependencies(
            strategies=(_Strategy(), _Strategy()),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_ExecutionAdapter(),
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
            instrument_registry=None,
        )


def test_broker_runtime_topology_resolver_rejects_topology_account_id_mismatch() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-account-mismatch"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-topo"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(ValueError, match="dependency account_id does not match topology account"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategy=_Strategy(),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=AccountId("acct-topo"),
                ),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                account_id=AccountId("acct-mismatch"),
                instrument_registry=None,
            )
        ).build()


def test_broker_runtime_topology_resolver_rejects_account_actor_id_mismatch() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-actor-mismatch"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-topo"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(ValueError, match="account actor account_id mismatch"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategy=_Strategy(),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=AccountId("acct-mismatch"),
                ),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                instrument_registry=None,
            )
        ).build()


def test_broker_runtime_topology_resolver_rejects_multi_account_actor_id_mismatch() -> None:
    account_a = AccountId("acct-a")
    account_b = AccountId("acct-b")
    account_actors = {
        account_a: AccountActor(
            initial_cash={"USD": Decimal("10000")},
            account_id=AccountId("acct-a-mismatch"),
        ),
        account_b: AccountActor(
            initial_cash={"USD": Decimal("10000")},
            account_id=account_b,
        ),
    }
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-multi-actor-mismatch"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(account_id=account_a, initial_cash=Decimal("10000")),
            AccountRuntimeSpec(account_id=account_b, initial_cash=Decimal("10000")),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-a"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=account_a,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-b"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=account_b,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(ValueError, match="account actor account_id mismatch"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategies=(_Strategy(), _Strategy()),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
                account_actors=account_actors,
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                instrument_registry=None,
            )
        ).build()


def test_broker_runtime_topology_resolver_rejects_empty_market_data_routes() -> None:
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-no-md-route"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-topo"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-topo"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=AccountId("acct-topo"),
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(),
    )

    with pytest.raises(ValueError, match="at least one market data route"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategy=_Strategy(),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=AccountId("acct-topo"),
                ),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                instrument_registry=None,
            )
        ).build()


def test_broker_route_missing_fails_fast() -> None:
    from qts.runtime.router import RouteNotFoundError

    account_id = AccountId("acct-missing-route")
    topology = RuntimeTopology(
        run_id=RuntimeRunId("live-topology-missing-broker-route"),
        mode=RuntimeMode.PAPER_BROKER,
        accounts=(
            AccountRuntimeSpec(
                account_id=account_id,
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-missing-route"),
                strategy_class="tests.unit.runtime.test_broker_runtime_topology._Strategy",
                account_id=account_id,
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
        broker_routes=(),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="streaming",
                source_type="streaming",
                provider="streaming",
                subscriptions=(InstrumentId("EQUITY.US.NASDAQ.AAPL"),),
            ),
        ),
    )

    with pytest.raises(RouteNotFoundError, match="no route for key"):
        BrokerRuntimeTopologyResolver(
            RuntimeSessionDependencies(
                strategy=_Strategy(),
                risk_engine=RiskEngine([]),
                instrument_context=_InstrumentContext(),
                execution_adapter=_ExecutionAdapter(),
                account_actor=AccountActor(
                    initial_cash={"USD": Decimal("10000")},
                    account_id=account_id,
                ),
                portfolio_view=_portfolio_view,
                multiplier_for=lambda instrument_id: Decimal("1"),
                runtime_topology=topology,
                mode=RuntimeMode.PAPER_BROKER,
                execution_environment=ExecutionEnvironment.BROKER,
                instrument_registry=None,
            )
        ).build()
