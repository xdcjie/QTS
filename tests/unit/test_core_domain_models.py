from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest


def test_id_value_objects_are_typed_immutable_and_non_empty() -> None:
    from qts.core.ids import AccountId, InstrumentId, StrategyId

    account_id = AccountId("acct-001")
    strategy_id: object = StrategyId("acct-001")

    assert account_id == AccountId("acct-001")
    assert account_id != strategy_id
    assert str(account_id) == "acct-001"
    assert account_id.value == "acct-001"
    with pytest.raises(FrozenInstanceError):
        account_id.value = "acct-002"  # type: ignore[misc]
    with pytest.raises(ValueError, match="InstrumentId must not be empty"):
        InstrumentId("")


def test_time_interval_uses_half_open_aware_datetimes() -> None:
    from qts.core.time import TimeInterval

    start = datetime(2026, 1, 2, 9, 30, tzinfo=ZoneInfo("America/New_York"))
    end = start + timedelta(minutes=5)
    interval = TimeInterval(start=start, end=end)

    assert interval.contains(start)
    assert interval.contains(end - timedelta(microseconds=1))
    assert not interval.contains(end)
    assert interval.duration == timedelta(minutes=5)
    with pytest.raises(ValueError, match="start must be before end"):
        TimeInterval(start=end, end=start)
    with pytest.raises(ValueError, match="timezone-aware"):
        TimeInterval(start=datetime(2026, 1, 2, 9, 30), end=end)


def test_instrument_contract_and_derivative_specs_are_pure_domain_objects() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import (
        AssetClass,
        ContractSpec,
        ExerciseStyle,
        FutureSpec,
        Instrument,
        OptionRight,
        OptionSpec,
        SettlementType,
    )

    spec = ContractSpec(
        tick_size=Decimal("0.01"),
        lot_size=Decimal("1"),
        multiplier=Decimal("100"),
        settlement=SettlementType.PHYSICAL,
        calendar_id="XNYS",
    )
    equity = Instrument(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        asset_class=AssetClass.EQUITY,
        exchange="NASDAQ",
        currency="USD",
        contract_spec=spec,
    )
    future_spec = FutureSpec(
        expiry=date(2026, 6, 19),
        underlying=equity.instrument_id,
        root_symbol="AAPL",
    )
    option_spec = OptionSpec(
        expiry=date(2026, 6, 19),
        underlying=equity.instrument_id,
        strike=Decimal("200"),
        right=OptionRight.CALL,
        exercise_style=ExerciseStyle.AMERICAN,
    )

    assert equity.instrument_id == InstrumentId("EQUITY.US.NASDAQ.AAPL")
    assert equity.asset_class is AssetClass.EQUITY
    assert future_spec.underlying == equity.instrument_id
    assert option_spec.right is OptionRight.CALL
    assert not hasattr(equity, "broker_symbol")
    with pytest.raises(FrozenInstanceError):
        equity.currency = "CAD"  # type: ignore[misc]
    with pytest.raises(ValueError, match="tick_size must be positive"):
        ContractSpec(
            tick_size=Decimal("0"),
            lot_size=Decimal("1"),
            multiplier=Decimal("1"),
            settlement=SettlementType.CASH,
            calendar_id="XNYS",
        )


def test_contract_and_market_data_models_keep_scalar_validation_inside_the_models() -> None:
    contract_tree = ast.parse(
        Path("backend/src/qts/domain/instruments/contract_spec.py").read_text(encoding="utf-8")
    )
    market_data_tree = ast.parse(
        Path("backend/src/qts/domain/market_data/bar.py").read_text(encoding="utf-8")
    )

    contract_private_functions = {
        node.name
        for node in contract_tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }
    market_data_private_functions = {
        node.name
        for node in market_data_tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_require_positive" not in contract_private_functions
    assert "_require_non_negative" not in market_data_private_functions


def test_bar_quote_and_tick_validate_market_data_invariants() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar, Quote, Tick

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    start = datetime(2026, 1, 2, 9, 30, tzinfo=UTC)
    end = start + timedelta(minutes=1)
    bar = Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=end,
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume=Decimal("1000"),
        trade_count=10,
    )
    quote = Quote(
        instrument_id=instrument_id,
        time=start,
        bid_price=Decimal("100"),
        ask_price=Decimal("100.01"),
        bid_size=Decimal("10"),
        ask_size=Decimal("12"),
    )
    tick = Tick(instrument_id=instrument_id, time=start, price=Decimal("100.01"), size=Decimal("5"))

    assert bar.interval.contains(start)
    assert not bar.interval.contains(end)
    assert quote.spread == Decimal("0.01")
    assert tick.instrument_id == instrument_id
    with pytest.raises(ValueError, match="high must be greater than or equal"):
        Bar(
            instrument_id=instrument_id,
            start_time=start,
            end_time=end,
            timeframe="1m",
            session_id="2026-01-02",
            open=Decimal("100"),
            high=Decimal("99"),
            low=Decimal("98"),
            close=Decimal("100"),
        )
    with pytest.raises(ValueError, match="bid_price must be less than or equal"):
        Quote(
            instrument_id=instrument_id,
            time=start,
            bid_price=Decimal("101"),
            ask_price=Decimal("100"),
        )


def test_event_metadata_is_immutable_traceable_and_partitioned() -> None:
    from qts.core.ids import AccountId, CorrelationId, EventId, InstrumentId, StrategyId
    from qts.domain.events import EventMetadata

    event_time = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    metadata = EventMetadata(
        event_id=EventId("evt-001"),
        event_type="bar.closed",
        event_time=event_time,
        source_actor="market-data",
        target_actor="strategy",
        account_id=AccountId("acct-001"),
        strategy_id=StrategyId("strat-001"),
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        correlation_id=CorrelationId("corr-001"),
        partition_key="strat-001",
        seq=1,
    )

    assert metadata.event_type == "bar.closed"
    assert metadata.partition_key == "strat-001"
    assert metadata.correlation_id == CorrelationId("corr-001")
    with pytest.raises(FrozenInstanceError):
        metadata.seq = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="event_type must not be empty"):
        EventMetadata(event_id=EventId("evt-002"), event_type="", event_time=event_time)
