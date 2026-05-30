"""Lock the C1 config -> execution-timing -> manifest wiring.

``BacktestRuntimeConfig`` carries ``fill_policy`` / ``optimistic_fill_waiver``.
``BacktestEngine.from_config`` derives the ``ExecutionTimingModel`` from those
fields when no explicit model is passed, and the backtest manifest records the
fill-timing honesty facts (``optimistic`` / ``promotion_grade``) so the
promotion path can gate on them.

Domain rule: ``same_bar_close`` fills are look-ahead and are never
promotion-grade; ``next_bar_open`` is the promotion-grade policy and the
default. A config that does not set ``fill_policy`` produces a next-obtainable,
promotion-grade manifest, and selecting ``same_bar_close`` requires an explicit
``optimistic_fill_waiver``.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qts.backtest.engine import BacktestEngine
from qts.core.ids import InstrumentId
from qts.domain.execution_timing import ExecutionTimingModel, FillPolicy
from qts.domain.market_data import Bar
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import run_engine_streaming

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _make_config(**overrides: Any) -> BacktestRuntimeConfig:
    params: dict[str, Any] = {
        "roots": ("AAPL",),
        "symbols": ("AAPL",),
        "start": datetime(2026, 1, 2, tzinfo=UTC),
        "end": datetime(2026, 1, 3, tzinfo=UTC),
        "timeframe": "1m",
        "initial_cash": Decimal("10000"),
        "strategy_class": "tests.support.fill_policy.BuyOnce",
        "market_data": BacktestMarketDataReference(config_path=Path("md.yaml"), catalog="research"),
        "instrument_ids": {"AAPL": _INSTRUMENT},
        "risk_config": BacktestRiskConfig(max_notional=Decimal("1000000")),
    }
    params.update(overrides)
    return BacktestRuntimeConfig(**params)


# ---------------------------------------------------------------------------
# Config defaults and timing-model derivation (the exact from_config derivation)
# ---------------------------------------------------------------------------


def test_config_without_fill_policy_defaults_to_next_bar_open() -> None:
    config = _make_config()

    assert config.fill_policy == "next_bar_open"
    assert config.optimistic_fill_waiver is False

    # from_config derives the timing model from these fields when no explicit
    # model is supplied; the default derived model is promotion-grade.
    derived = ExecutionTimingModel.from_value(
        config.fill_policy, optimistic_waiver=config.optimistic_fill_waiver
    )
    payload = derived.to_manifest_payload()
    assert derived.fill_policy is FillPolicy.NEXT_BAR_OPEN
    assert payload["optimistic"] is False
    assert payload["promotion_grade"] is True


def test_config_next_bar_open_derives_promotion_grade_timing() -> None:
    config = _make_config(fill_policy="next_bar_open")

    derived = ExecutionTimingModel.from_value(
        config.fill_policy, optimistic_waiver=config.optimistic_fill_waiver
    )
    payload = derived.to_manifest_payload()
    assert derived.fill_policy is FillPolicy.NEXT_BAR_OPEN
    assert payload["optimistic"] is False
    assert payload["promotion_grade"] is True


def test_config_same_bar_close_requires_waiver_and_is_never_promotion_grade() -> None:
    # same_bar_close without the explicit waiver is rejected at config validation.
    with pytest.raises(ValueError, match="optimistic_fill_waiver"):
        _make_config(fill_policy="same_bar_close")

    config = _make_config(fill_policy="same_bar_close", optimistic_fill_waiver=True)
    assert config.optimistic_fill_waiver is True
    derived = ExecutionTimingModel.from_value(
        config.fill_policy, optimistic_waiver=config.optimistic_fill_waiver
    )
    payload = derived.to_manifest_payload()
    # The waiver authorizes research use; the look-ahead fill is never promotion-grade.
    assert payload["optimistic"] is True
    assert payload["optimistic_waiver"] is True
    assert payload["promotion_grade"] is False


# ---------------------------------------------------------------------------
# Config -> from_config -> manifest end-to-end facts
# ---------------------------------------------------------------------------


def test_from_config_default_manifest_is_next_bar_open_promotion_grade(
    tmp_path: Path,
) -> None:
    engine = BacktestEngine.from_config(
        _make_config(),
        bars=_bars(),
        strategy=_BuyOnceStrategy(),
    )
    captured = run_engine_streaming(engine, tmp_path / "default")

    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "next_bar_open"
    assert assumptions["optimistic"] is False
    assert assumptions["promotion_grade"] is True


def test_from_config_same_bar_close_manifest_records_not_promotion_grade(
    tmp_path: Path,
) -> None:
    engine = BacktestEngine.from_config(
        _make_config(fill_policy="same_bar_close", optimistic_fill_waiver=True),
        bars=_bars(),
        strategy=_BuyOnceStrategy(),
    )
    captured = run_engine_streaming(engine, tmp_path / "same-bar-close")

    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "same_bar_close"
    assert assumptions["optimistic"] is True
    assert assumptions["promotion_grade"] is False
    assert assumptions["optimistic_waiver"] is True


def test_from_config_next_bar_open_manifest_is_promotion_grade(tmp_path: Path) -> None:
    engine = BacktestEngine.from_config(
        _make_config(fill_policy="next_bar_open"),
        bars=_bars(),
        strategy=_BuyOnceStrategy(),
    )
    captured = run_engine_streaming(engine, tmp_path / "next-bar-open")

    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "next_bar_open"
    assert assumptions["optimistic"] is False
    assert assumptions["promotion_grade"] is True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _BuyOnceStrategy(Strategy):
    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self._placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self._placed:
            ctx.target_quantity(self.asset, Decimal("10"))
            self._placed = True


def _bar(minute: int, *, open_: str, close: str) -> Bar:
    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=minute)
    low = min(Decimal(open_), Decimal(close))
    high = max(Decimal(open_), Decimal(close))
    return Bar(
        instrument_id=_INSTRUMENT,
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


def _bars() -> list[Bar]:
    return [
        _bar(0, open_="100", close="105"),
        _bar(1, open_="110", close="115"),
    ]
