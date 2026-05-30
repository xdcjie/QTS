"""Auditable runtime topology for strategy, account, broker, and data routes."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.core.ids import AccountId, BrokerId, InstrumentId, RuntimeRunId, StrategyId
from qts.runtime.config import BacktestRuntimeConfig, BrokerRuntimeConfig
from qts.runtime.mode import AccountEnvironment, ExecutionEnvironment, RuntimeMode


@dataclass(frozen=True, slots=True)
class StrategyRuntimeSpec:
    """One configured strategy instance in a runtime topology."""

    strategy_id: StrategyId
    strategy_class: str
    account_id: AccountId
    subscriptions: tuple[InstrumentId, ...] = ()
    capital_allocation: Decimal = Decimal("1")
    risk_profile_id: str = "default"
    signal_aggregation_policy: str = "sum_targets"
    enabled: bool = True
    signal_priority: int = 0
    signal_weight: Decimal = Decimal("1")
    conflict_group: str = "default"

    def __post_init__(self) -> None:
        """Validate and normalize strategy topology fields."""
        if not self.strategy_class.strip():
            raise ValueError("strategy_class must not be empty")
        if self.capital_allocation < Decimal("0"):
            raise ValueError("capital_allocation must be non-negative")
        if self.signal_weight < Decimal("0"):
            raise ValueError("signal_weight must be non-negative")
        object.__setattr__(self, "subscriptions", tuple(self.subscriptions))

    def to_payload(self) -> dict[str, Any]:
        """Serialize this strategy spec for manifests and hashing."""
        return {
            "strategy_id": self.strategy_id.value,
            "strategy_class": self.strategy_class,
            "account_id": self.account_id.value,
            "subscriptions": sorted(item.value for item in self.subscriptions),
            "capital_allocation": str(self.capital_allocation),
            "risk_profile_id": self.risk_profile_id,
            "signal_aggregation_policy": self.signal_aggregation_policy,
            "enabled": self.enabled,
            "signal_priority": self.signal_priority,
            "signal_weight": str(self.signal_weight),
            "conflict_group": self.conflict_group,
        }


@dataclass(frozen=True, slots=True)
class AccountRuntimeSpec:
    """One runtime account partition."""

    account_id: AccountId
    broker_id: BrokerId | None = None
    base_currency: str = "USD"
    risk_config: str = "default"
    initial_cash: Decimal = Decimal("0")
    live_account_mapping: str | None = None
    broker_account_code: str | None = None
    account_environment: AccountEnvironment = AccountEnvironment.SIMULATED

    def __post_init__(self) -> None:
        """Validate and normalize account topology fields."""
        if not self.base_currency.strip():
            raise ValueError("base_currency must not be empty")
        if self.initial_cash < Decimal("0"):
            raise ValueError("initial_cash must be non-negative")

    def to_payload(self) -> dict[str, Any]:
        """Serialize this account spec for manifests and hashing."""
        return {
            "account_id": self.account_id.value,
            "broker_id": None if self.broker_id is None else self.broker_id.value,
            "base_currency": self.base_currency,
            "risk_config": self.risk_config,
            "initial_cash": str(self.initial_cash),
            "live_account_mapping": self.live_account_mapping,
            "broker_account_code": self.broker_account_code,
            "account_environment": self.account_environment.value,
        }


@dataclass(frozen=True, slots=True)
class BrokerRouteSpec:
    """Execution route from an account partition to a broker boundary."""

    broker_id: BrokerId
    account_id: AccountId
    execution_adapter_type: str
    order_transport_type: str
    execution_environment: ExecutionEnvironment
    broker_capabilities: tuple[str, ...] = ()
    idempotency_store_ref: str | None = None

    def __post_init__(self) -> None:
        """Validate broker route labels."""
        if not self.execution_adapter_type.strip():
            raise ValueError("execution_adapter_type must not be empty")
        if not self.order_transport_type.strip():
            raise ValueError("order_transport_type must not be empty")
        object.__setattr__(self, "broker_capabilities", tuple(self.broker_capabilities))

    def to_payload(self) -> dict[str, Any]:
        """Serialize this broker route for manifests and hashing."""
        return {
            "broker_id": self.broker_id.value,
            "account_id": self.account_id.value,
            "execution_adapter_type": self.execution_adapter_type,
            "order_transport_type": self.order_transport_type,
            "execution_environment": self.execution_environment.value,
            "broker_capabilities": sorted(self.broker_capabilities),
            "idempotency_store_ref": self.idempotency_store_ref,
        }


@dataclass(frozen=True, slots=True)
class MarketDataRouteSpec:
    """Market-data route available to strategies in a runtime topology."""

    source_id: str
    source_type: str
    provider: str
    subscriptions: tuple[InstrumentId, ...] = ()
    permission_policy: str = "default"
    stale_data_policy: str = "default"

    def __post_init__(self) -> None:
        """Validate market-data route labels."""
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.source_type.strip():
            raise ValueError("source_type must not be empty")
        if not self.provider.strip():
            raise ValueError("provider must not be empty")
        object.__setattr__(self, "subscriptions", tuple(self.subscriptions))

    def to_payload(self) -> dict[str, Any]:
        """Serialize this market-data route for manifests and hashing."""
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "provider": self.provider,
            "subscriptions": sorted(item.value for item in self.subscriptions),
            "permission_policy": self.permission_policy,
            "stale_data_policy": self.stale_data_policy,
        }


@dataclass(frozen=True, slots=True)
class RuntimeTopology:
    """Auditable topology for one runtime session."""

    run_id: RuntimeRunId
    mode: RuntimeMode
    accounts: tuple[AccountRuntimeSpec, ...]
    strategies: tuple[StrategyRuntimeSpec, ...]
    broker_routes: tuple[BrokerRouteSpec, ...]
    market_data_routes: tuple[MarketDataRouteSpec, ...]

    def __post_init__(self) -> None:
        """Normalize and validate topology references."""
        object.__setattr__(self, "mode", RuntimeMode.from_value(self.mode))
        object.__setattr__(self, "accounts", tuple(self.accounts))
        object.__setattr__(self, "strategies", tuple(self.strategies))
        object.__setattr__(self, "broker_routes", tuple(self.broker_routes))
        object.__setattr__(self, "market_data_routes", tuple(self.market_data_routes))
        self._validate_unique_strategy_ids()
        self._validate_strategy_accounts()
        self._validate_broker_routes()

    @property
    def topology_hash(self) -> str:
        """Return a stable hash for this topology."""
        return stable_json_hash(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        """Serialize this topology without derived manifest fields."""
        return {
            "run_id": self.run_id.value,
            "mode": self.mode.value,
            "accounts": [item.to_payload() for item in self.accounts],
            "strategies": [item.to_payload() for item in self.strategies],
            "broker_routes": [item.to_payload() for item in self.broker_routes],
            "market_data_routes": [item.to_payload() for item in self.market_data_routes],
        }

    def to_manifest_payload(self) -> dict[str, Any]:
        """Serialize this topology with manifest metadata."""
        payload = self.to_payload()
        payload["account_count"] = len(self.accounts)
        payload["strategy_count"] = len(self.strategies)
        payload["broker_route_count"] = len(self.broker_routes)
        payload["market_data_route_count"] = len(self.market_data_routes)
        payload["account_partition_topology"] = self._account_partition_topology()
        payload["topology_hash"] = self.topology_hash
        return payload

    def _account_partition_topology(self) -> list[dict[str, Any]]:
        """Return manifest evidence for account-scoped runtime partitions."""
        partitions: list[dict[str, Any]] = []
        for account in self.accounts:
            strategy_ids = sorted(
                strategy.strategy_id.value
                for strategy in self.strategies
                if strategy.account_id == account.account_id
            )
            broker_route_count = sum(
                1 for route in self.broker_routes if route.account_id == account.account_id
            )
            partitions.append(
                {
                    "account_id": account.account_id.value,
                    "broker_route_count": broker_route_count,
                    "strategy_ids": strategy_ids,
                }
            )
        return partitions

    def _validate_unique_strategy_ids(self) -> None:
        strategy_ids = [item.strategy_id for item in self.strategies]
        if len(set(strategy_ids)) != len(strategy_ids):
            raise ValueError("duplicate strategy_id in runtime topology")

    def _validate_strategy_accounts(self) -> None:
        account_ids = {item.account_id for item in self.accounts}
        for strategy in self.strategies:
            if strategy.account_id not in account_ids:
                raise ValueError(f"strategy references missing account: {strategy.account_id}")

    def _validate_broker_routes(self) -> None:
        routes = {(route.account_id, route.broker_id) for route in self.broker_routes}
        for account in self.accounts:
            if account.broker_id is None:
                continue
            if (account.account_id, account.broker_id) not in routes:
                raise ValueError(f"missing broker route for account: {account.account_id}")


@dataclass(frozen=True, slots=True)
class RuntimeTopologyManifest:
    """Auditable manifest wrapper for a runtime topology."""

    payload: dict[str, Any]

    @classmethod
    def from_topology(cls, topology: RuntimeTopology) -> RuntimeTopologyManifest:
        """Create a manifest payload from one validated topology."""

        return cls(payload=topology.to_manifest_payload())

    @property
    def topology_hash(self) -> str:
        """Return the topology hash referenced by reports."""

        return str(self.payload["topology_hash"])


class RuntimeTopologyBuilder:
    """Build validated runtime topologies from runtime configs and route specs."""

    @staticmethod
    def _short_name(value: str) -> str:
        return value.rsplit(":", 1)[-1].rsplit(".", 1)[-1]

    @classmethod
    def from_backtest_config(
        cls,
        config: BacktestRuntimeConfig,
        run_id: RuntimeRunId,
        *,
        account_id: str = "acct-backtest",
    ) -> RuntimeTopology:
        """Build a backtest topology from one normalized backtest config."""
        strategy_class = config.strategy_class
        strategy_id = StrategyId(cls._short_name(strategy_class))
        strategy_allocation = Decimal("1")
        strategy_enabled = True
        account_id_value = account_id
        if config.strategy is not None:
            strategy_class = config.strategy.class_path
            strategy_id = StrategyId(config.strategy.strategy_id or cls._short_name(strategy_class))
            strategy_allocation = config.strategy.allocation
            strategy_enabled = config.strategy.enabled
            if config.strategy.account_id is not None and config.strategy.account_id.strip():
                account_id_value = config.strategy.account_id

        raw_symbols = tuple(config.instrument_ids.values()) or tuple(
            InstrumentId(symbol) for symbol in config.symbols
        )
        if not raw_symbols:
            raise ValueError("backtest topology requires at least one instrument")
        subscriptions = tuple(dict.fromkeys(raw_symbols))
        if config.strategies:
            strategy_specs = cls._backtest_strategy_specs(
                config,
                default_account_id=account_id_value,
                subscriptions=subscriptions,
            )
            strategy_account_ids = {strategy.account_id for strategy in strategy_specs}
            if len(strategy_account_ids) != 1:
                raise ValueError("backtest multi-strategy topology requires one account")
            account_id_value = next(iter(strategy_account_ids)).value
        else:
            strategy_specs = (
                StrategyRuntimeSpec(
                    strategy_id=strategy_id,
                    strategy_class=strategy_class,
                    account_id=AccountId(account_id_value),
                    subscriptions=subscriptions,
                    capital_allocation=strategy_allocation,
                    enabled=strategy_enabled,
                ),
            )
        return RuntimeTopology(
            run_id=run_id,
            mode=RuntimeMode.BACKTEST,
            accounts=(
                AccountRuntimeSpec(
                    account_id=AccountId(account_id_value),
                    initial_cash=config.initial_cash,
                    account_environment=AccountEnvironment.SIMULATED,
                ),
            ),
            strategies=strategy_specs,
            broker_routes=(),
            market_data_routes=(
                MarketDataRouteSpec(
                    source_id=config.market_data.source,
                    source_type="replay",
                    provider=config.market_data.source,
                    subscriptions=subscriptions,
                ),
            ),
        )

    @classmethod
    def _backtest_strategy_specs(
        cls,
        config: BacktestRuntimeConfig,
        *,
        default_account_id: str,
        subscriptions: tuple[InstrumentId, ...],
    ) -> tuple[StrategyRuntimeSpec, ...]:
        specs: list[StrategyRuntimeSpec] = []
        for strategy in config.strategies:
            strategy_class = strategy.class_path
            account_id = strategy.account_id or default_account_id
            specs.append(
                StrategyRuntimeSpec(
                    strategy_id=StrategyId(strategy.strategy_id or cls._short_name(strategy_class)),
                    strategy_class=strategy_class,
                    account_id=AccountId(account_id),
                    subscriptions=subscriptions,
                    capital_allocation=strategy.allocation,
                    enabled=strategy.enabled,
                    signal_aggregation_policy=strategy.signal_aggregation_policy,
                    signal_priority=strategy.signal_priority,
                    signal_weight=strategy.signal_weight,
                    conflict_group=strategy.conflict_group,
                )
            )
        return tuple(specs)

    @classmethod
    def from_live_config(
        cls,
        config: BrokerRuntimeConfig,
        run_id: RuntimeRunId,
        *,
        account_id: str,
        strategy_id: str,
        strategy_class: str,
        subscriptions: tuple[InstrumentId, ...],
        broker_id: str | None = None,
        broker_account_code: str | None = None,
        base_currency: str = "USD",
        initial_cash: Decimal = Decimal("0"),
        execution_adapter_type: str | None = None,
        order_transport_type: str | None = None,
        execution_environment: ExecutionEnvironment | None = None,
        market_data_source_id: str = "streaming",
        market_data_source_type: str = "streaming",
        market_data_provider: str = "streaming",
        market_data_subscriptions: tuple[InstrumentId, ...] | None = None,
    ) -> RuntimeTopology:
        """Build a live/paper topology from explicit session routing specs."""
        mode = RuntimeMode.from_value(config.mode)
        return RuntimeTopology(
            run_id=run_id,
            mode=mode,
            accounts=(
                cls.live_account_from_config(
                    config,
                    account_id=account_id,
                    broker_id=broker_id,
                    broker_account_code=broker_account_code,
                    base_currency=base_currency,
                    initial_cash=initial_cash,
                ),
            ),
            strategies=(
                cls.live_strategy_spec(
                    account_id=account_id,
                    strategy_id=strategy_id,
                    strategy_class=strategy_class,
                    subscriptions=(
                        market_data_subscriptions
                        if market_data_subscriptions is not None
                        else subscriptions
                    ),
                ),
            ),
            broker_routes=cls.live_broker_routes(
                config,
                account_id=account_id,
                broker_id=broker_id,
                execution_adapter_type=execution_adapter_type,
                order_transport_type=order_transport_type,
                execution_environment=execution_environment,
            ),
            market_data_routes=cls.live_market_data_routes(
                subscriptions=subscriptions,
                market_data_source_id=market_data_source_id,
                market_data_source_type=market_data_source_type,
                market_data_provider=market_data_provider,
                market_data_subscriptions=market_data_subscriptions,
            ),
        )

    @classmethod
    def live_account_from_config(
        cls,
        config: BrokerRuntimeConfig,
        *,
        account_id: str,
        broker_id: str | None = None,
        broker_account_code: str | None = None,
        base_currency: str = "USD",
        initial_cash: Decimal = Decimal("0"),
    ) -> AccountRuntimeSpec:
        """Build the account partition for a live/paper runtime topology."""

        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        mode = RuntimeMode.from_value(config.mode)
        return AccountRuntimeSpec(
            account_id=AccountId(account_id),
            broker_id=BrokerId(broker_id) if broker_id is not None else None,
            base_currency=base_currency,
            initial_cash=initial_cash,
            broker_account_code=broker_account_code,
            account_environment=AccountEnvironment.from_value(
                config.account_environment,
                mode=mode,
            ),
        )

    @classmethod
    def live_strategy_spec(
        cls,
        *,
        account_id: str,
        strategy_id: str,
        strategy_class: str,
        subscriptions: tuple[InstrumentId, ...],
    ) -> StrategyRuntimeSpec:
        """Build the strategy partition for a live/paper runtime topology."""

        if not strategy_id.strip():
            raise ValueError("strategy_id must not be empty")
        if not strategy_class.strip():
            raise ValueError("strategy_class must not be empty")
        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        if not subscriptions:
            raise ValueError("subscriptions must not be empty")
        return StrategyRuntimeSpec(
            strategy_id=StrategyId(strategy_id),
            strategy_class=strategy_class,
            account_id=AccountId(account_id),
            subscriptions=tuple(dict.fromkeys(subscriptions)),
        )

    @classmethod
    def live_broker_routes(
        cls,
        config: BrokerRuntimeConfig,
        *,
        account_id: str,
        broker_id: str | None = None,
        execution_adapter_type: str | None = None,
        order_transport_type: str | None = None,
        execution_environment: ExecutionEnvironment | None = None,
    ) -> tuple[BrokerRouteSpec, ...]:
        """Build execution adapter routes for a live/paper runtime topology."""

        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        mode = RuntimeMode.from_value(config.mode)
        resolved_execution_environment = ExecutionEnvironment.from_value(
            execution_environment,
            mode=mode,
        )
        account_broker_id = BrokerId(broker_id) if broker_id is not None else None
        if resolved_execution_environment is not ExecutionEnvironment.BROKER:
            if account_broker_id is not None:
                raise ValueError("account_broker_id requires broker route in broker mode")
            return ()
        if account_broker_id is None:
            raise ValueError("broker route requires broker_id")
        if not execution_adapter_type:
            raise ValueError("broker route requires execution_adapter_type")
        if not order_transport_type:
            raise ValueError("broker route requires order_transport_type")
        return (
            BrokerRouteSpec(
                broker_id=account_broker_id,
                account_id=AccountId(account_id),
                execution_adapter_type=execution_adapter_type,
                order_transport_type=order_transport_type,
                execution_environment=resolved_execution_environment,
            ),
        )

    @classmethod
    def live_market_data_routes(
        cls,
        *,
        subscriptions: tuple[InstrumentId, ...],
        market_data_source_id: str = "streaming",
        market_data_source_type: str = "streaming",
        market_data_provider: str = "streaming",
        market_data_subscriptions: tuple[InstrumentId, ...] | None = None,
    ) -> tuple[MarketDataRouteSpec, ...]:
        """Build market-data routes for a live/paper runtime topology."""

        if not subscriptions:
            raise ValueError("subscriptions must not be empty")
        normalized_subscriptions = tuple(
            dict.fromkeys(
                market_data_subscriptions
                if market_data_subscriptions is not None
                else subscriptions
            )
        )
        return (
            MarketDataRouteSpec(
                source_id=market_data_source_id,
                source_type=market_data_source_type,
                provider=market_data_provider,
                subscriptions=normalized_subscriptions,
            ),
        )


__all__ = [
    "AccountRuntimeSpec",
    "BrokerRouteSpec",
    "MarketDataRouteSpec",
    "RuntimeMode",
    "RuntimeTopology",
    "RuntimeTopologyBuilder",
    "RuntimeTopologyManifest",
    "StrategyRuntimeSpec",
]
