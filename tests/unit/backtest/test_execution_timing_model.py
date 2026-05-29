"""Unit gates for the backtest execution timing model (DR-008 / Task 3.1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from qts.backtest.execution_timing import ExecutionTimingModel, FillPolicy
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(*, open_: str, close: str, minute: int = 0) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=minute)
    low = min(Decimal(open_), Decimal(close))
    high = max(Decimal(open_), Decimal(close))
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal(open_),
        high=high,
        low=low,
        close=Decimal(close),
        volume=Decimal("100"),
        is_complete=True,
    )


def test_same_bar_close_returns_decision_bar_close() -> None:
    model = ExecutionTimingModel.research_only()
    decision_bar = _bar(open_="100", close="105", minute=0)

    assert model.fill_policy is FillPolicy.SAME_BAR_CLOSE
    assert not model.defers_to_next_bar
    assert model.price_for_execution_bar(decision_bar) == Decimal("105")


def test_next_bar_open_returns_next_bar_open_for_decision_at_bar_n() -> None:
    model = ExecutionTimingModel.promotion_grade()
    next_bar = _bar(open_="106", close="108", minute=1)

    assert model.fill_policy is FillPolicy.NEXT_BAR_OPEN
    assert model.defers_to_next_bar
    # The loop passes bar N+1 as the execution bar; the realized fill price is
    # that bar's open, not bar N's close.
    assert model.price_for_execution_bar(next_bar) == Decimal("106")


def test_promotion_grade_default_is_next_bar_open() -> None:
    model = ExecutionTimingModel.promotion_grade()

    assert model.fill_policy is FillPolicy.NEXT_BAR_OPEN
    assert model.is_promotion_grade
    assert not model.is_optimistic


def test_same_bar_close_is_flagged_optimistic_and_not_promotion_grade() -> None:
    model = ExecutionTimingModel.research_only()

    assert model.is_optimistic
    assert not model.is_promotion_grade
    payload = model.to_manifest_payload()
    assert payload["fill_policy"] == "same_bar_close"
    assert payload["optimistic"] is True
    assert payload["promotion_grade"] is False
    assert payload["optimistic_waiver"] is False


def test_same_bar_close_with_explicit_waiver_is_promotion_grade() -> None:
    model = ExecutionTimingModel.research_only(optimistic_waiver=True)

    assert model.is_optimistic
    assert model.is_promotion_grade
    payload = model.to_manifest_payload()
    assert payload["optimistic"] is True
    assert payload["optimistic_waiver"] is True
    assert payload["promotion_grade"] is True


def test_construction_default_is_backward_compatible_same_bar_close() -> None:
    model = ExecutionTimingModel()

    assert model.fill_policy is FillPolicy.SAME_BAR_CLOSE
    assert model.is_optimistic


def test_next_bar_open_manifest_payload_is_promotion_grade() -> None:
    payload = ExecutionTimingModel.promotion_grade().to_manifest_payload()

    assert payload["fill_policy"] == "next_bar_open"
    assert payload["fill_timing_basis"] == "next_bar_open"
    assert payload["optimistic"] is False
    assert payload["promotion_grade"] is True


def test_fill_policy_from_value_round_trips_and_rejects_unknown() -> None:
    assert FillPolicy.from_value("next_bar_open") is FillPolicy.NEXT_BAR_OPEN
    assert FillPolicy.from_value(" Same_Bar_Close ") is FillPolicy.SAME_BAR_CLOSE
    assert ExecutionTimingModel.from_value("next_bar_open").fill_policy is FillPolicy.NEXT_BAR_OPEN
    with pytest.raises(ValueError, match="unsupported fill_policy"):
        FillPolicy.from_value("tick_vwap")
