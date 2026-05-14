from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from qts.core.ids import InstrumentId
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.instrument_registry import InstrumentRegistry
from qts.strategy_sdk import PortfolioView, Strategy


def _bar(start: datetime) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        volume=Decimal("10"),
        is_complete=True,
    )


def _portfolio_view(*args: Any, **kwargs: Any) -> PortfolioView:
    return PortfolioView(cash=Decimal("10000"), equity=Decimal("10000"))


def _registry() -> InstrumentRegistry:
    registry = InstrumentRegistry()
    registry.register(
        "AAPL",
        Instrument(
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            asset_class=AssetClass.EQUITY,
            exchange="NASDAQ",
            currency="USD",
            contract_spec=ContractSpec(
                tick_size=Decimal("0.01"),
                lot_size=Decimal("1"),
                multiplier=Decimal("1"),
                settlement=SettlementType.CASH,
                calendar_id="NASDAQ",
            ),
        ),
    )
    return registry


def test_strategy_execution_pipeline_emits_aggregated_intents() -> None:
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    class BuyOnceStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self.done = False

        def on_bar(self, ctx: Any, bar: object) -> None:
            if not self.done:
                ctx.target_quantity(self.asset, Decimal("1"))
                self.done = True

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    pipeline = StrategyExecutionPipeline(
        strategy=BuyOnceStrategy(),
        instrument_registry=_registry(),
        future_chain_registry=None,
        portfolio_view=_portfolio_view,
        prune_history=True,
    )

    result = pipeline.execute_bar(
        bar,
        account_snapshot=object(),
        latest_prices={bar.instrument_id: bar.close},
        aggregate_signals=True,
    )

    assert result.bar == bar
    assert [intent.value for intent in result.intents] == [Decimal("1")]


def test_strategy_execution_pipeline_suppresses_warmup_signals() -> None:
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    class WarmupStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")

        def on_bar(self, ctx: Any, bar: object) -> None:
            ctx.target_quantity(self.asset, Decimal("1"))

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    pipeline = StrategyExecutionPipeline(
        strategy=WarmupStrategy(),
        instrument_registry=_registry(),
        future_chain_registry=None,
        portfolio_view=_portfolio_view,
        prune_history=True,
    )

    result = pipeline.execute_bar(
        bar,
        account_snapshot=object(),
        latest_prices={bar.instrument_id: bar.close},
        aggregate_signals=False,
    )

    assert result.intents == ()


def test_strategy_execution_pipeline_no_signal_when_strategy_idle() -> None:
    from qts.runtime.strategy_execution_pipeline import StrategyExecutionPipeline

    class IdleStrategy(Strategy):
        def initialize(self, ctx: Any) -> None:
            pass

        def on_bar(self, ctx: Any, bar: object) -> None:
            return None

    bar = _bar(datetime(2026, 1, 2, 14, 30, tzinfo=UTC))
    pipeline = StrategyExecutionPipeline(
        strategy=IdleStrategy(),
        instrument_registry=_registry(),
        future_chain_registry=None,
        portfolio_view=_portfolio_view,
        prune_history=True,
    )

    result = pipeline.execute_bar(
        bar,
        account_snapshot=object(),
        latest_prices={bar.instrument_id: bar.close},
        aggregate_signals=True,
    )

    assert result.intents == ()
    assert result.raw_intents == ()
    assert result.signal_batches == ()
