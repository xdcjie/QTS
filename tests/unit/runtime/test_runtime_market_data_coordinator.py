from __future__ import annotations

import inspect
from datetime import UTC, datetime, time, timedelta
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


def test_runtime_market_data_coordinator_accepts_narrow_context_for_subscription_delta() -> None:
    from qts.runtime.market_data_coordinator import RuntimeMarketDataCoordinator

    class MarketDataContext:
        def __init__(self) -> None:
            self.strategy_subscriptions: tuple[InstrumentId, ...] = (
                InstrumentId("EQUITY.US.NASDAQ.AAPL"),
                InstrumentId("EQUITY.US.NASDAQ.MSFT"),
            )

        def replace_strategy_subscriptions(
            self,
            subscriptions: tuple[InstrumentId, ...],
        ) -> None:
            self.strategy_subscriptions = subscriptions

        def write(self, event: object) -> None:
            del event

    context = MarketDataContext()
    coordinator = RuntimeMarketDataCoordinator(context)

    delta = coordinator.materialize_universe_subscription_delta(
        (
            InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            InstrumentId("EQUITY.US.NASDAQ.NVDA"),
        )
    )

    assert delta.subscribe == (InstrumentId("EQUITY.US.NASDAQ.NVDA"),)
    assert delta.unsubscribe == (InstrumentId("EQUITY.US.NASDAQ.MSFT"),)
    assert context.strategy_subscriptions == (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.NVDA"),
    )


def test_runtime_market_data_coordinator_has_named_dispatch_stages() -> None:
    from qts.runtime.market_data_coordinator import RuntimeMarketDataCoordinator

    required_stages = (
        "route_source_bar",
        "derive_market_data",
        "trigger_strategy_for_bar",
        "finish_market_data_dispatch",
    )

    for stage in required_stages:
        method = getattr(RuntimeMarketDataCoordinator, stage, None)
        assert method is not None, f"missing market-data dispatch stage: {stage}"

    source_lines = inspect.getsourcelines(RuntimeMarketDataCoordinator.on_market_data)[0]
    assert len(source_lines) <= 80


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


def test_runtime_session_derives_session_daily_bars_with_runtime_session_window() -> None:
    from qts.data.sessions import RegularSessionWindow
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
                account_id=AccountId("acct-coordinator-session-daily"),
            ),
            instrument_registry=_registry(),
            portfolio_view=_portfolio_view,
            multiplier_for=lambda instrument_id: Decimal("1"),
            account_id=AccountId("acct-coordinator-session-daily"),
            target_timeframe="1d",
            exchange_timezone_by_instrument={instrument_id: UTC},
            session_window_by_instrument={
                instrument_id: RegularSessionWindow(
                    exchange_timezone="UTC",
                    open_time=time(22, 0),
                    close_time=time(22, 3),
                )
            },
        )
    )

    session.start()
    start = datetime(2026, 1, 2, 22, 0, tzinfo=UTC)
    for minute in range(2):
        result = session.on_market_data(_bar(start + timedelta(minutes=minute)))
        assert result.market_data == ()
        assert result.orders == ()

    result = session.on_market_data(_bar(start + timedelta(minutes=2)))

    assert len(result.market_data) == 1
    [bar] = result.market_data
    assert bar.timeframe == "1d"
    assert bar.start_time == start
    assert bar.end_time == start + timedelta(minutes=3)
    assert bar.is_complete
    assert not bar.is_partial
    assert len(result.orders) == 1
