from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from qts.core.ids import (
    AccountId,
    BrokerId,
    InstrumentId,
    RuntimeRunId,
    StrategyId,
)
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRuntimeConfig,
    BacktestStrategyConfig,
    LiveRuntimeConfig,
)
from qts.runtime.mode import AccountEnvironment, ExecutionEnvironment, RuntimeMode
from qts.runtime.topology import (
    AccountRuntimeSpec,
    BrokerRouteSpec,
    MarketDataRouteSpec,
    RuntimeTopology,
    RuntimeTopologyBuilder,
    StrategyRuntimeSpec,
)


def test_runtime_topology_builder_from_backtest_config() -> None:
    config = BacktestRuntimeConfig(
        roots=("GC",),
        symbols=("GC",),
        start=datetime(2020, 1, 1, tzinfo=UTC),
        end=datetime(2020, 1, 2, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="examples.strategies.gc_si_momentum:GcSiMomentumStrategy",
        strategy=BacktestStrategyConfig(
            strategy_id="gc-strategy",
            class_path="examples.strategies.gc_si_momentum:GcSiMomentumStrategy",
            account_id="backtest-acct",
            allocation=Decimal("0.5"),
            enabled=True,
            params={"symbols": ["GC"]},
        ),
        strategy_params={},
        instrument_ids={"GC": InstrumentId("F.US.CME.GC")},
        market_data=BacktestMarketDataReference(
            config_path=Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
        ),
    )
    topology = RuntimeTopologyBuilder.from_backtest_config(
        config,
        RuntimeRunId("run-backtest-builder"),
    )

    assert topology.mode == RuntimeMode.BACKTEST
    assert len(topology.accounts) == 1
    assert len(topology.strategies) == 1
    assert topology.strategies[0].strategy_id == StrategyId("gc-strategy")
    assert topology.strategies[0].strategy_class == (
        "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
    )
    assert topology.strategies[0].subscriptions == (InstrumentId("F.US.CME.GC"),)
    assert topology.market_data_routes[0].source_id == "local_historical"
    assert topology.to_manifest_payload()["topology_hash"].startswith("sha256:")


def test_backtest_topology_builder_falls_back_to_symbols_when_instrument_ids_missing() -> None:
    config = BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=datetime(2020, 1, 1, tzinfo=UTC),
        end=datetime(2020, 1, 2, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.integration.test_live_runtime_evidence_output:NoopPaperStrategy",
        strategy=BacktestStrategyConfig(
            class_path="tests.integration.test_live_runtime_evidence_output:NoopPaperStrategy",
            strategy_id="aapl-strategy",
            allocation=Decimal("1"),
            enabled=True,
            params={},
        ),
        strategy_params={},
        market_data=BacktestMarketDataReference(
            config_path=Path("configs/data/historical.local.yaml"),
            catalog="research_equities",
        ),
    )
    topology = RuntimeTopologyBuilder.from_backtest_config(
        config,
        RuntimeRunId("run-backtest-symbol-fallback"),
    )

    assert topology.strategies[0].subscriptions == (InstrumentId("AAPL"),)


def test_live_topology_builder_broker_mode_requires_route() -> None:
    config = LiveRuntimeConfig(
        mode=RuntimeMode.LIVE.value,
        broker_configured=True,
        account_configured=True,
        risk_configured=True,
        calendar_configured=True,
        kill_switch_configured=True,
        allow_live_orders=True,
        operator_signoff_id="ops-001",
        broker_account_code="U123",
        broker_port=4001,
        broker_account_kind="live",
    )

    with pytest.raises(ValueError, match="execution_adapter_type"):
        RuntimeTopologyBuilder.from_live_config(
            config,
            RuntimeRunId("run-live-builder"),
            account_id="acct-live",
            strategy_id="live-strategy",
            strategy_class="examples.strategies.gc_si_momentum:GcSiMomentumStrategy",
            subscriptions=(InstrumentId("F.US.CME.GC"),),
            broker_id="broker-live",
        )

    topology = RuntimeTopologyBuilder.from_live_config(
        config,
        RuntimeRunId("run-live-builder"),
        account_id="acct-live",
        strategy_id="live-strategy",
        strategy_class="examples.strategies.gc_si_momentum:GcSiMomentumStrategy",
        subscriptions=(InstrumentId("F.US.CME.GC"),),
        broker_id="broker-live",
        execution_adapter_type="ibkr",
        order_transport_type="ib_async",
    )

    assert topology.mode == RuntimeMode.LIVE
    assert len(topology.broker_routes) == 1
    assert topology.broker_routes[0].broker_id.value == "broker-live"
    assert topology.market_data_routes[0].source_type == "streaming"


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
