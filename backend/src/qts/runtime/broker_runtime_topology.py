"""Runtime topology resolution for paper/live sessions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, StrategyId
from qts.risk.risk_engine import RiskEngine
from qts.runtime.actor_ref import ActorRef
from qts.runtime.actors.account_actor import AccountActor, GetAccountSnapshot
from qts.runtime.actors.execution_actor import ExecutionActor
from qts.runtime.actors.order_manager_actor import OrderManagerActor
from qts.runtime.dependencies import RuntimeSessionDependencies
from qts.runtime.mailbox import Mailbox
from qts.runtime.mode import ExecutionEnvironment, RuntimeMode
from qts.runtime.router import RouteNotFoundError
from qts.runtime.signal_policy import SignalAggregationPolicy
from qts.runtime.state_recovery import SnapshotStore
from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline
from qts.runtime.topology import BrokerRouteSpec, RuntimeTopology
from qts.strategy_sdk import Strategy


@dataclass(frozen=True, slots=True)
class StrategyRuntimeBinding:
    """Runtime-local strategy instance with its bound execution pipeline."""

    strategy_id: StrategyId
    account_id: AccountId | None
    strategy: Strategy
    subscriptions: tuple[InstrumentId, ...]
    enabled: bool
    signal_aggregation_policy: SignalAggregationPolicy
    signal_priority: int
    signal_weight: Decimal
    conflict_group: str
    pipeline: StrategyExecutionPipeline


@dataclass(frozen=True, slots=True)
class AccountRuntimePartition:
    """Per-account actor partition for isolated runtime execution state."""

    account_id: AccountId | None
    risk_engine: RiskEngine
    broker_route: BrokerRouteSpec | None
    snapshot_store: SnapshotStore | None
    account_actor: AccountActor
    account_ref: ActorRef
    order_manager_actor: OrderManagerActor
    order_manager_ref: ActorRef
    execution_ref: ActorRef


@dataclass(frozen=True, slots=True)
class ResolvedRuntimeTopology:
    """Topology-dependent objects resolved for one runtime session."""

    strategy_bindings: tuple[StrategyRuntimeBinding, ...]
    strategy_subscriptions: tuple[InstrumentId, ...]
    account_partitions: dict[AccountId | None, AccountRuntimePartition]
    resolved_account_id: AccountId | None
    resolved_strategy_id: StrategyId | None


class BrokerRuntimeTopologyResolver:
    """Build strategy bindings and per-account partitions from a runtime topology."""

    def __init__(self, dependencies: RuntimeSessionDependencies) -> None:
        self._dependencies = dependencies
        self._topology = dependencies.runtime_topology
        self._resolved_account_id = dependencies.account_id
        self._resolved_strategy_id = dependencies.strategy_id

    def build(self) -> ResolvedRuntimeTopology:
        """Return strategy bindings and partitions ready for session execution."""
        if self._topology is None:
            strategy_bindings = self._build_default_strategy_bindings()
            strategy_subscriptions: tuple[InstrumentId, ...] = ()
            account_partitions = self._build_default_account_partitions()
        else:
            topology = self._topology
            self._apply_topology(topology)
            strategy_bindings = self._build_topology_strategy_bindings(topology)
            strategy_subscriptions = tuple(
                item for binding in strategy_bindings for item in binding.subscriptions
            )
            strategy_subscriptions = tuple(dict.fromkeys(strategy_subscriptions))
            account_partitions = self._build_topology_account_partitions(
                topology,
                strategy_bindings,
            )

        return ResolvedRuntimeTopology(
            strategy_bindings=strategy_bindings,
            strategy_subscriptions=strategy_subscriptions,
            account_partitions=account_partitions,
            resolved_account_id=self._resolved_account_id,
            resolved_strategy_id=self._resolved_strategy_id,
        )

    def _build_default_strategy_bindings(self) -> tuple[StrategyRuntimeBinding, ...]:
        """Build one binding for non-topology execution mode."""
        if self._dependencies.strategy is None:
            raise ValueError("default mode requires a concrete strategy")
        if self._resolved_strategy_id is None:
            self._resolved_strategy_id = StrategyId("strategy")
        if self._resolved_account_id is None:
            account_ref = ActorRef(
                actor=self._dependencies.account_actor,
                mailbox=Mailbox(),
            )
            self._resolved_account_id = account_ref.ask(GetAccountSnapshot()).account_id
        if self._resolved_account_id is None:
            raise ValueError("account_id is required for runtime execution")

        pipeline = self._make_strategy_pipeline(
            self._dependencies.strategy,
            strategy_id=self._resolved_strategy_id,
        )
        return (
            StrategyRuntimeBinding(
                strategy_id=self._resolved_strategy_id,
                account_id=self._resolved_account_id,
                strategy=self._dependencies.strategy,
                subscriptions=(),
                enabled=True,
                signal_aggregation_policy=SignalAggregationPolicy.SUM_TARGETS,
                signal_priority=0,
                signal_weight=Decimal("1"),
                conflict_group="default",
                pipeline=pipeline,
            ),
        )

    def _build_default_account_partitions(self) -> dict[AccountId | None, AccountRuntimePartition]:
        """Build a single partition for non-topology execution mode."""
        if self._resolved_account_id is None:
            account_ref = ActorRef(
                actor=self._dependencies.account_actor,
                mailbox=Mailbox(),
            )
            account_id = account_ref.ask(GetAccountSnapshot()).account_id
        else:
            account_id = self._resolved_account_id
        if account_id is None:
            raise ValueError("account_id is required for runtime execution")
        default_partitions: dict[AccountId | None, AccountRuntimePartition] = {
            account_id: self._build_account_partition(
                account_id,
                self._dependencies.account_actor,
                broker_route=None,
            )
        }
        return default_partitions

    def _build_topology_strategy_bindings(
        self, topology: RuntimeTopology
    ) -> tuple[StrategyRuntimeBinding, ...]:
        """Build runtime bindings from topology specs and injected strategies."""
        strategy_instances = self._dependencies.strategies
        if strategy_instances is None:
            if self._dependencies.strategy is None:
                raise ValueError("runtime topology requires one injected strategy instance")
            strategy_instances = (self._dependencies.strategy,)
            if len(topology.strategies) != 1:
                raise ValueError(
                    "runtime topology strategy count does not match injected strategies"
                )
        elif len(strategy_instances) != len(topology.strategies):
            raise ValueError("runtime topology strategy count does not match injected strategies")

        default_subscriptions = tuple(
            item for route in topology.market_data_routes for item in route.subscriptions
        )
        default_subscriptions = tuple(dict.fromkeys(default_subscriptions))

        bindings: list[StrategyRuntimeBinding] = []
        for index, strategy_spec in enumerate(topology.strategies):
            strategy = strategy_instances[index]
            subscriptions = tuple(strategy_spec.subscriptions)
            if not subscriptions:
                subscriptions = default_subscriptions
            if not subscriptions:
                raise ValueError("topology strategy requires at least one subscribed instrument")

            pipeline = self._make_strategy_pipeline(
                strategy,
                strategy_id=strategy_spec.strategy_id,
                signal_aggregation_policy=strategy_spec.signal_aggregation_policy,
                signal_priority=strategy_spec.signal_priority,
                signal_weight=strategy_spec.signal_weight,
                conflict_group=strategy_spec.conflict_group,
            )
            bindings.append(
                StrategyRuntimeBinding(
                    strategy_id=strategy_spec.strategy_id,
                    account_id=strategy_spec.account_id,
                    strategy=strategy,
                    subscriptions=tuple(dict.fromkeys(subscriptions)),
                    enabled=strategy_spec.enabled,
                    signal_aggregation_policy=SignalAggregationPolicy(
                        strategy_spec.signal_aggregation_policy
                    ),
                    signal_priority=strategy_spec.signal_priority,
                    signal_weight=strategy_spec.signal_weight,
                    conflict_group=strategy_spec.conflict_group,
                    pipeline=pipeline,
                )
            )

        if self._resolved_strategy_id is None and len(topology.strategies) == 1:
            self._resolved_strategy_id = topology.strategies[0].strategy_id
        return tuple(bindings)

    def _build_topology_account_partitions(
        self,
        topology: RuntimeTopology,
        bindings: tuple[StrategyRuntimeBinding, ...],
    ) -> dict[AccountId | None, AccountRuntimePartition]:
        """Build one partition per account required by topology-bound strategies."""
        needed_account_ids: list[AccountId] = []
        for binding in bindings:
            if binding.account_id is None:
                raise ValueError("strategy account_id is required for topology execution")
            if binding.account_id not in needed_account_ids:
                needed_account_ids.append(binding.account_id)
        if not needed_account_ids:
            raise ValueError("runtime topology must bind at least one account")

        if len(topology.accounts) == 1 and self._dependencies.account_actors is None:
            if len(needed_account_ids) != 1:
                raise ValueError("runtime topology strategies must reference one account")
            account_id = needed_account_ids[0]
            topology_account_actor = self._dependencies.account_actor
            self._validate_account_actor_matches(account_id, topology_account_actor)
            single_partition: dict[AccountId | None, AccountRuntimePartition] = {
                account_id: self._build_account_partition(
                    account_id,
                    topology_account_actor,
                    broker_route=self._broker_route_for(topology, account_id),
                )
            }
            return single_partition

        account_actors = self._dependencies.account_actors
        if account_actors is None:
            account_actors = {}
        partitions: dict[AccountId | None, AccountRuntimePartition] = {}
        for account_id in needed_account_ids:
            actor: AccountActor | None = account_actors.get(account_id)
            if actor is None:
                raise ValueError(f"missing account actor for topology account: {account_id.value}")
            self._validate_account_actor_matches(account_id, actor)
            partitions[account_id] = self._build_account_partition(
                account_id,
                actor,
                broker_route=self._broker_route_for(topology, account_id),
            )
        return partitions

    def _build_account_partition(
        self,
        account_id: AccountId | None,
        account_actor: AccountActor,
        *,
        broker_route: BrokerRouteSpec | None,
    ) -> AccountRuntimePartition:
        """Build one partition owning account/order/execution state."""
        execution_mailbox = Mailbox()
        order_manager_mailbox = Mailbox()
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        order_manager_actor = OrderManagerActor(
            execution_ref=ActorRef(mailbox=execution_mailbox),
            account_ref=account_ref,
            multiplier_by_instrument=self._dependencies.multipliers,
            account_id=account_id,
        )
        order_manager_ref = ActorRef(
            actor=order_manager_actor,
            mailbox=order_manager_mailbox,
        )
        execution_ref = ActorRef(
            actor=ExecutionActor(
                order_manager_ref=order_manager_ref,
                execution_adapter=self._dependencies.execution_adapter,
                live_capital_decision=self._dependencies.live_capital_decision,
            ),
            mailbox=execution_mailbox,
        )
        return AccountRuntimePartition(
            account_id=account_id,
            risk_engine=self._risk_engine_for(account_id),
            broker_route=broker_route,
            snapshot_store=self._snapshot_store_for(account_id),
            account_actor=account_actor,
            account_ref=account_ref,
            order_manager_actor=order_manager_actor,
            order_manager_ref=order_manager_ref,
            execution_ref=execution_ref,
        )

    def _risk_engine_for(self, account_id: AccountId | None) -> RiskEngine:
        if account_id is not None and self._dependencies.risk_engines is not None:
            return self._dependencies.risk_engines.get(account_id, self._dependencies.risk_engine)
        return self._dependencies.risk_engine

    def _snapshot_store_for(self, account_id: AccountId | None) -> SnapshotStore | None:
        if account_id is not None and self._dependencies.snapshot_stores is not None:
            return self._dependencies.snapshot_stores.get(
                account_id,
                self._dependencies.snapshot_store,
            )
        return self._dependencies.snapshot_store

    def _broker_route_for(
        self,
        topology: RuntimeTopology,
        account_id: AccountId,
    ) -> BrokerRouteSpec | None:
        routes = [route for route in topology.broker_routes if route.account_id == account_id]
        if len(routes) > 1:
            raise ValueError(f"multiple broker routes for account: {account_id.value}")
        if not routes:
            if self._dependencies.execution_environment is ExecutionEnvironment.BROKER:
                raise RouteNotFoundError(f"no route for key: {account_id.value}")
            return None
        return routes[0]

    def _validate_account_actor_matches(
        self,
        account_id: AccountId,
        account_actor: AccountActor,
    ) -> None:
        account_ref = ActorRef(actor=account_actor, mailbox=Mailbox())
        actor_account_id = account_ref.ask(GetAccountSnapshot()).account_id
        if actor_account_id is not None and actor_account_id != account_id:
            raise ValueError(
                f"account actor account_id mismatch: expected {account_id}, got {actor_account_id}"
            )

    def _apply_topology(self, topology: RuntimeTopology) -> None:
        """Validate topology for live runtime session execution."""
        if topology.mode is not self._dependencies.mode:
            raise ValueError("topology mode does not match dependency mode")
        if topology.mode is RuntimeMode.BACKTEST:
            raise ValueError("live runtime session cannot run backtest topology")
        if not topology.accounts:
            raise ValueError("live runtime topology must define at least one account")
        if not topology.market_data_routes:
            raise ValueError("live runtime topology must define at least one market data route")

        if len(topology.accounts) == 1:
            account = topology.accounts[0]
            if self._resolved_account_id is None:
                self._resolved_account_id = account.account_id
            elif self._resolved_account_id != account.account_id:
                raise ValueError("dependency account_id does not match topology account")
            if self._resolved_strategy_id is not None and len(topology.strategies) > 1:
                raise ValueError("cannot set dependency strategy_id for multi-strategy topology")
        elif self._resolved_account_id is not None:
            account_ids = {item.account_id for item in topology.accounts}
            if self._resolved_account_id not in account_ids:
                raise ValueError("dependency account_id does not match topology accounts")

    def _make_strategy_pipeline(
        self,
        strategy: Strategy,
        *,
        strategy_id: StrategyId,
        signal_aggregation_policy: str = "sum_targets",
        signal_priority: int = 0,
        signal_weight: Decimal = Decimal("1"),
        conflict_group: str = "default",
    ) -> StrategyExecutionPipeline:
        """Build a strategy pipeline for one strategy instance."""
        return StrategyExecutionPipeline(
            strategy=strategy,
            strategy_id=strategy_id,
            instrument_registry=self._dependencies.instrument_registry,
            future_chain_registry=self._dependencies.future_roll_registry,
            portfolio_view=self._dependencies.portfolio_view,
            prune_history=True,
            signal_aggregation_policy=signal_aggregation_policy,
            signal_priority=signal_priority,
            signal_weight=signal_weight,
            conflict_group=conflict_group,
        )


__all__ = [
    "AccountRuntimePartition",
    "BrokerRuntimeTopologyResolver",
    "ResolvedRuntimeTopology",
    "StrategyRuntimeBinding",
]
