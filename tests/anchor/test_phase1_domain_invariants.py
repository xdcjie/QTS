from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal


def test_half_open_interval_end_boundary_belongs_to_next_interval() -> None:
    from qts.core.time import TimeInterval

    first_start = datetime(2026, 1, 2, 9, 30, tzinfo=UTC)
    boundary = first_start + timedelta(minutes=5)
    first = TimeInterval(start=first_start, end=boundary)
    second = TimeInterval(start=boundary, end=boundary + timedelta(minutes=5))

    assert first.contains(first_start)
    assert not first.contains(boundary)
    assert second.contains(boundary)


def test_bar_domain_model_preserves_explicit_start_end_semantics() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.market_data import Bar

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    end = start + timedelta(minutes=1)
    bar = Bar(
        instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
        start_time=start,
        end_time=end,
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("2350.10"),
        high=Decimal("2351.00"),
        low=Decimal("2349.80"),
        close=Decimal("2350.50"),
        volume=Decimal("42"),
    )

    assert bar.start_time == start
    assert bar.end_time == end
    assert bar.interval.contains(start)
    assert not bar.interval.contains(end)


def test_instrument_identity_uses_internal_id_not_broker_symbol() -> None:
    from qts.core.ids import InstrumentId
    from qts.domain.instruments import (
        AssetClass,
        ContractSpec,
        FutureSpec,
        Instrument,
        SettlementType,
    )

    instrument = Instrument(
        instrument_id=InstrumentId("FUTURE.COMEX.GC.202606"),
        asset_class=AssetClass.FUTURE,
        exchange="COMEX",
        currency="USD",
        contract_spec=ContractSpec(
            tick_size=Decimal("0.10"),
            lot_size=Decimal("1"),
            multiplier=Decimal("100"),
            settlement=SettlementType.PHYSICAL,
            calendar_id="CMES",
        ),
        derivative=FutureSpec(
            expiry=date(2026, 6, 26),
            underlying=InstrumentId("FUTURE_ROOT.COMEX.GC"),
            root_symbol="GC",
        ),
    )

    assert instrument.instrument_id == InstrumentId("FUTURE.COMEX.GC.202606")
    assert not hasattr(instrument, "symbol")
    assert not hasattr(instrument, "broker_symbol")
