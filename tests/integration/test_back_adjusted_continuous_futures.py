"""Integration gate: back-adjusted continuous series has no roll jump (DR-027)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.registry.back_adjusted_series import BackAdjustedContinuousSeriesBuilder
from qts.registry.future_roll import FutureRollRegistry, FutureRollSelection

_FRONT = InstrumentId("FUTURE.CME.GC.GCM0")
_NEXT = InstrumentId("FUTURE.CME.GC.GCN0")
_T1 = datetime(2010, 5, 1, tzinfo=UTC)
_T2 = datetime(2010, 6, 1, tzinfo=UTC)


def _rolled_registry() -> tuple[FutureRollRegistry, InstrumentId]:
    registry = FutureRollRegistry()
    continuous_id = registry.register_root(
        root_symbol="GC", exchange="CME", contracts=(_FRONT, _NEXT)
    )
    # Before the roll the front contract is GCM0.
    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=_T1,
            concrete_instrument_id=_FRONT,
            source_symbol="GCM0",
            prices_by_instrument={_FRONT: Decimal("110"), _NEXT: Decimal("100")},
        )
    )
    # At the roll the front switches to GCN0; old=110, new=100 -> factor 1.1.
    registry.record_selection(
        FutureRollSelection(
            continuous_instrument_id=continuous_id,
            root_symbol="GC",
            as_of=_T2,
            concrete_instrument_id=_NEXT,
            source_symbol="GCN0",
            prices_by_instrument={_FRONT: Decimal("110"), _NEXT: Decimal("100")},
        )
    )
    return registry, continuous_id


def test_back_adjusted_series_has_no_artificial_roll_jump() -> None:
    registry, continuous_id = _rolled_registry()
    builder = BackAdjustedContinuousSeriesBuilder(future_roll_registry=registry)

    points = builder.build_adjustment_factors(continuous_id)
    assert len(points) == 1
    assert points[0].adjustment_factor == Decimal("1.1")

    # The pre-roll raw price of the old contract (110), back-adjusted, must line
    # up continuously with the new contract's post-roll price (100): 110 / 1.1.
    adjusted_pre_roll = builder.adjusted_price(
        raw_price=Decimal("110"), as_of=_T1, continuous_id=continuous_id
    )
    assert adjusted_pre_roll == Decimal("100")

    # Post-roll prices are not adjusted (no later rolls).
    adjusted_post_roll = builder.adjusted_price(
        raw_price=Decimal("100"), as_of=_T2, continuous_id=continuous_id
    )
    assert adjusted_post_roll == Decimal("100")


def test_series_hash_is_deterministic_for_same_roll_history() -> None:
    registry, continuous_id = _rolled_registry()
    builder = BackAdjustedContinuousSeriesBuilder(future_roll_registry=registry)
    first = builder.series_hash(continuous_id)
    second = builder.series_hash(continuous_id)
    assert first == second
    assert first.startswith("sha256:")
