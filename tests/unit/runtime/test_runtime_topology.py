from __future__ import annotations

from decimal import Decimal

import pytest
from qts.core.ids import AccountId, BrokerId, InstrumentId, RuntimeRunId, StrategyId
from qts.runtime.mode import AccountEnvironment, ExecutionEnvironment, RuntimeMode
from qts.runtime.topology import (
    AccountRuntimeSpec,
    BrokerRouteSpec,
    MarketDataRouteSpec,
    RuntimeTopology,
    StrategyRuntimeSpec,
)


def test_two_strategies_one_account_topology() -> None:
    account_id = AccountId("acct-a")
    broker_id = BrokerId("broker-a")
    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")

    topology = RuntimeTopology(
        run_id=RuntimeRunId("run-1"),
        mode=RuntimeMode.PAPER_BROKER,
        accounts=(
            AccountRuntimeSpec(
                account_id=account_id,
                broker_id=broker_id,
                base_currency="USD",
                initial_cash=Decimal("100000"),
                broker_account_code="DU1234567",
                account_environment=AccountEnvironment.PAPER,
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-a"),
                strategy_class="tests.StrategyA",
                account_id=account_id,
                subscriptions=(instrument_id,),
                capital_allocation=Decimal("0.5"),
                risk_profile_id="risk-a",
            ),
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-b"),
                strategy_class="tests.StrategyB",
                account_id=account_id,
                subscriptions=(instrument_id,),
                capital_allocation=Decimal("0.5"),
                risk_profile_id="risk-a",
            ),
        ),
        broker_routes=(
            BrokerRouteSpec(
                broker_id=broker_id,
                account_id=account_id,
                execution_adapter_type="ibkr",
                order_transport_type="ib_async",
                execution_environment=ExecutionEnvironment.BROKER,
            ),
        ),
        market_data_routes=(
            MarketDataRouteSpec(
                source_id="ibkr-md",
                source_type="streaming",
                provider="ibkr",
                subscriptions=(instrument_id,),
            ),
        ),
    )

    payload = topology.to_manifest_payload()
    assert payload["strategy_count"] == 2
    assert payload["account_count"] == 1
    assert payload["topology_hash"].startswith("sha256:")


def test_strategy_referencing_missing_account_fails() -> None:
    with pytest.raises(ValueError, match="missing account"):
        RuntimeTopology(
            run_id=RuntimeRunId("run-1"),
            mode=RuntimeMode.PAPER_SIMULATED,
            accounts=(),
            strategies=(
                StrategyRuntimeSpec(
                    strategy_id=StrategyId("strategy-a"),
                    strategy_class="tests.StrategyA",
                    account_id=AccountId("missing"),
                    subscriptions=(),
                ),
            ),
            broker_routes=(),
            market_data_routes=(),
        )


def test_duplicate_strategy_id_fails() -> None:
    account_id = AccountId("acct-a")
    strategy_id = StrategyId("strategy-a")

    with pytest.raises(ValueError, match="duplicate strategy_id"):
        RuntimeTopology(
            run_id=RuntimeRunId("run-1"),
            mode=RuntimeMode.PAPER_SIMULATED,
            accounts=(AccountRuntimeSpec(account_id=account_id),),
            strategies=(
                StrategyRuntimeSpec(
                    strategy_id=strategy_id,
                    strategy_class="tests.StrategyA",
                    account_id=account_id,
                ),
                StrategyRuntimeSpec(
                    strategy_id=strategy_id,
                    strategy_class="tests.StrategyB",
                    account_id=account_id,
                ),
            ),
            broker_routes=(),
            market_data_routes=(),
        )


def test_missing_broker_route_fails_for_broker_execution_account() -> None:
    account_id = AccountId("acct-a")

    with pytest.raises(ValueError, match="missing broker route"):
        RuntimeTopology(
            run_id=RuntimeRunId("run-1"),
            mode=RuntimeMode.PAPER_BROKER,
            accounts=(
                AccountRuntimeSpec(
                    account_id=account_id,
                    broker_id=BrokerId("broker-a"),
                    account_environment=AccountEnvironment.PAPER,
                ),
            ),
            strategies=(),
            broker_routes=(),
            market_data_routes=(),
        )


def test_topology_hash_stable() -> None:
    account_id = AccountId("acct-a")

    left = RuntimeTopology(
        run_id=RuntimeRunId("run-1"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(AccountRuntimeSpec(account_id=account_id),),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-a"),
                strategy_class="tests.StrategyA",
                account_id=account_id,
            ),
        ),
        broker_routes=(),
        market_data_routes=(),
    )
    right = RuntimeTopology(
        run_id=RuntimeRunId("run-1"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(AccountRuntimeSpec(account_id=account_id),),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strategy-a"),
                strategy_class="tests.StrategyA",
                account_id=account_id,
            ),
        ),
        broker_routes=(),
        market_data_routes=(),
    )

    assert left.topology_hash == right.topology_hash
