from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import AccountId, InstrumentId, RuntimeRunId, StrategyId
from qts.runtime.topology import (
    AccountRuntimeSpec,
    MarketDataRouteSpec,
    RuntimeMode,
    RuntimeTopology,
    StrategyRuntimeSpec,
)

from tests.unit.runtime.test_runtime_session import (
    _bar,
    _bar_for_instrument,
    _BuyOnceStrategy,
    _InstrumentContext,
    _portfolio_view,
    _RecordingExecutionAdapter,
    _registry,
)


def test_runtime_market_data_coordinator_matches_session_unsubscribed_result() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.market_data_coordinator import RuntimeMarketDataCoordinator
    from qts.runtime.session import RuntimeSession

    topology = RuntimeTopology(
        run_id=RuntimeRunId("coordinator-topology-run"),
        mode=RuntimeMode.PAPER_SIMULATED,
        accounts=(
            AccountRuntimeSpec(
                account_id=AccountId("acct-coordinator"),
                initial_cash=Decimal("10000"),
            ),
        ),
        strategies=(
            StrategyRuntimeSpec(
                strategy_id=StrategyId("strat-coordinator"),
                strategy_class="tests.unit.runtime.test_runtime_session._BuyOnceStrategy",
                account_id=AccountId("acct-coordinator"),
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
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=_RecordingExecutionAdapter(),
            account_actor=AccountActor(initial_cash={"USD": Decimal("10000")}),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            runtime_topology=topology,
        )
    )

    coordinator = RuntimeMarketDataCoordinator(session)
    session.start()
    result = coordinator.on_market_data(
        _bar_for_instrument(
            datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            InstrumentId("EQUITY.US.NASDAQ.GOOG"),
        )
    )

    assert result.market_data == ()
    assert result.orders == ()
    assert result.fills == ()
    assert result.reason_code == "INSTRUMENT_NOT_SUBSCRIBED"
    assert len(result.account_snapshots) == 1


def test_runtime_market_data_coordinator_matches_session_subscribed_result() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    adapter = _RecordingExecutionAdapter()
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=AccountId("acct-coordinator-subscribed"),
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=AccountId("acct-coordinator-subscribed"),
        )
    )

    session.start()
    result = session.on_market_data(_bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC)))

    assert result.reason_code is None
    assert len(result.market_data) == 1
    assert len(result.orders) == 1
    assert adapter.seen


def test_runtime_market_data_coordinator_delivers_only_complete_derived_timeframe() -> None:
    from qts.risk.risk_engine import RiskEngine
    from qts.runtime.actors.account_actor import AccountActor
    from qts.runtime.dependencies import RuntimeSessionDependencies
    from qts.runtime.session import RuntimeSession

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    adapter = _RecordingExecutionAdapter()
    session = RuntimeSession(
        RuntimeSessionDependencies(
            strategy=_BuyOnceStrategy(),
            risk_engine=RiskEngine([]),
            instrument_context=_InstrumentContext(),
            execution_adapter=adapter,
            account_actor=AccountActor(
                initial_cash={"USD": Decimal("10000")},
                account_id=AccountId("acct-coordinator-derived"),
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=AccountId("acct-coordinator-derived"),
            target_timeframe="5m",
            exchange_timezone_by_instrument={instrument_id: UTC},
        )
    )

    session.start()
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    for minute in range(4):
        result = session.on_market_data(_bar(start.replace(minute=30 + minute)))
        assert result.market_data == ()
        assert result.orders == ()

    result = session.on_market_data(_bar(start.replace(minute=34)))

    assert len(result.market_data) == 1
    [bar] = result.market_data
    assert bar.timeframe == "5m"
    assert bar.start_time == start
    assert bar.end_time == start.replace(minute=35)
    assert len(result.orders) == 1
