"""Unit tests for universe-driven market data subscription planning."""

from __future__ import annotations

from qts.core.ids import InstrumentId
from qts.data.subscriptions import UniverseSubscriptionPlanner


def test_universe_subscription_plan_materializes_deterministic_delta() -> None:
    planner = UniverseSubscriptionPlanner()

    delta = planner.plan(
        current=[
            InstrumentId("EQUITY.US.NASDAQ.MSFT"),
            InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        ],
        target=[
            InstrumentId("FUTURE.CME.GC.202606"),
            InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            InstrumentId("EQUITY.US.NASDAQ.NVDA"),
            InstrumentId("EQUITY.US.NASDAQ.NVDA"),
        ],
    )

    assert delta.subscribe == (
        InstrumentId("EQUITY.US.NASDAQ.NVDA"),
        InstrumentId("FUTURE.CME.GC.202606"),
    )
    assert delta.unsubscribe == (InstrumentId("EQUITY.US.NASDAQ.MSFT"),)


def test_universe_subscription_plan_is_empty_when_duplicates_do_not_change_membership() -> None:
    planner = UniverseSubscriptionPlanner()
    aapl = InstrumentId("EQUITY.US.NASDAQ.AAPL")

    delta = planner.plan(current=[aapl], target=[aapl, aapl])

    assert delta.subscribe == ()
    assert delta.unsubscribe == ()


def test_runtime_market_data_coordinator_materializes_universe_subscription_delta() -> None:
    from qts.runtime.market_data_coordinator import RuntimeMarketDataCoordinator

    class Session:
        _strategy_subscriptions = (
            InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            InstrumentId("EQUITY.US.NASDAQ.MSFT"),
        )

        def _write(self, event: object) -> None:
            del event

    session = Session()
    coordinator = RuntimeMarketDataCoordinator(session)

    delta = coordinator.materialize_universe_subscription_delta(
        (
            InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            InstrumentId("EQUITY.US.NASDAQ.NVDA"),
        )
    )

    assert delta.subscribe == (InstrumentId("EQUITY.US.NASDAQ.NVDA"),)
    assert delta.unsubscribe == (InstrumentId("EQUITY.US.NASDAQ.MSFT"),)
    assert session._strategy_subscriptions == (
        InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        InstrumentId("EQUITY.US.NASDAQ.NVDA"),
    )
