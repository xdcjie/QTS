from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.backtest.instrument_context import BacktestInstrumentContext
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, FutureRollSelection
from qts.strategy_sdk import TargetIntent
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.target import TargetIntentType


def _bar(start: datetime, instrument_id: InstrumentId, close: str = "100") -> Bar:
    return Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(close),
        high=Decimal(close),
        low=Decimal(close),
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_instrument_context_builds_registry_without_engine_string_parsing() -> None:
    bars = [
        _bar(
            datetime(2026, 1, 2, 14, 30, tzinfo=UTC),
            InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            "100",
        ),
        _bar(
            datetime(2026, 1, 2, 14, 31, tzinfo=UTC),
            InstrumentId("EQUITY.US.NYSE.GOOGL"),
            "120",
        ),
    ]
    context = BacktestInstrumentContext(registry_bars=tuple(bars), contract_multipliers={})
    registry = context.instrument_registry()

    assert registry.resolve("AAPL") == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert registry.resolve("GOOGL") == InstrumentId("EQUITY.US.NYSE.GOOGL")
    assert registry.get_instrument(InstrumentId("EQUITY.US.NASDAQ.AAPL")).exchange == "US"


def test_instrument_context_handles_continuous_roll_helpers() -> None:
    registry = FutureRollRegistry()
    concrete_front = InstrumentId("FUT.CME.ESU25")
    concrete_next = InstrumentId("FUT.CME.ESZ25")
    continuous = registry.register_root(
        root_symbol="ES",
        exchange="CME",
        contracts=(concrete_front, concrete_next),
    )
    t = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous,
            root_symbol="ES",
            as_of=t.replace(tzinfo=UTC),
            concrete_instrument_id=concrete_front,
            source_symbol="ESU25",
            prices_by_instrument={
                concrete_front: Decimal("5000"),
                concrete_next: Decimal("4900"),
            },
        )
    )

    context = BacktestInstrumentContext(
        future_roll_registry=registry,
        registry_bars=(
            Bar(
                instrument_id=continuous,
                start_time=t.replace(tzinfo=UTC),
                end_time=t.replace(tzinfo=UTC) + timedelta(minutes=1),
                timeframe="1m",
                session_id="2026-01-02",
                open=Decimal("5000"),
                high=Decimal("5000"),
                low=Decimal("5000"),
                close=Decimal("5000"),
                volume=Decimal("100"),
                is_complete=True,
            ),
        ),
    )
    intent = TargetIntent(
        intent_type=TargetIntentType.QUANTITY,
        asset=AssetRef(instrument_id=continuous, symbol="ES"),
        value=Decimal("1"),
    )
    bar = _bar(t, continuous, close="5000")

    assert context.order_instrument_for_intent(intent, bar=bar) == concrete_front
    assert context.market_price_for_intent(
        intent, instrument_id=concrete_front, bar=bar
    ) == Decimal("5000")
    assert context.related_contracts_for(continuous) == frozenset({concrete_front, concrete_next})

    latest_prices: dict[InstrumentId, Decimal] = {}
    context.update_rolling_prices(bar, latest_prices=latest_prices)
    assert latest_prices[concrete_front] == Decimal("5000")
