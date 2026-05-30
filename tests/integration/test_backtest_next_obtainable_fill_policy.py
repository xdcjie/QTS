"""Integration gate: promotion-grade backtests fill at the next obtainable price.

A decision made at the close of completed bar N must fill at bar N+1's open
under the promotion-grade ``next_bar_open`` policy, never at bar N's own close
(which is look-ahead). DR-008 / Task 3.1.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.backtest.engine import BacktestEngine
from qts.backtest.execution_timing import ExecutionTimingModel
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)
from qts.strategy_sdk import Strategy

from tests.support.backtest_streaming import run_engine_streaming

_INSTRUMENT = InstrumentId("EQUITY.US.NASDAQ.AAPL")


def _make_config(*, fill_policy: str = "same_bar_close") -> BacktestRuntimeConfig:
    """A minimal config-driven backtest identity (bars are injected separately)."""
    return BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=datetime(2026, 1, 2, tzinfo=UTC),
        end=datetime(2026, 1, 3, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("10000"),
        strategy_class="tests.support.fill_policy.BuyOnce",
        market_data=BacktestMarketDataReference(config_path=Path("md.yaml"), catalog="research"),
        instrument_ids={"AAPL": _INSTRUMENT},
        risk_config=BacktestRiskConfig(max_notional=Decimal("1000000")),
        fill_policy=fill_policy,
    )


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


class _BuyOnceStrategy(Strategy):
    """Submit a single target on the first bar, then hold."""

    def initialize(self, ctx: Any) -> None:
        self.asset = ctx.symbol("AAPL")
        self._placed = False

    def on_bar(self, ctx: Any, bar: object) -> None:
        if not self._placed:
            ctx.target_quantity(self.asset, Decimal("10"))
            self._placed = True


def _bars() -> list[Bar]:
    # Signal fires on bar 0 (close 105). The next obtainable price is bar 1's
    # open (110), which is intentionally different from bar 0's close.
    return [
        _bar(0, open_="100", close="105"),
        _bar(1, open_="110", close="115"),
    ]


def test_promotion_grade_default_fills_on_next_bar_open(tmp_path: Path) -> None:
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=_BuyOnceStrategy(),
            bars=_bars(),
            initial_cash=Decimal("10000"),
            execution_timing=ExecutionTimingModel.promotion_grade(),
        ),
        tmp_path / "next-bar-open",
    )

    # Fill price is the next bar's OPEN (110), not the signal bar's close (105).
    assert len(captured.fills) == 1
    assert Decimal(captured.fills[0]["price"]) == Decimal("110")
    assert captured.fills[0]["instrument_id"] == _INSTRUMENT.value

    # Cash and position reflect the next-obtainable fill price.
    assert captured.result.final_account.positions[_INSTRUMENT].quantity == Decimal("10")
    assert captured.result.final_account.cash["USD"] == Decimal("8900")

    # Manifest records the chosen fill policy and that it is promotion-grade.
    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "next_bar_open"
    assert assumptions["optimistic"] is False
    assert assumptions["promotion_grade"] is True


def test_same_bar_close_fills_on_signal_bar_close_and_is_optimistic(tmp_path: Path) -> None:
    # The research-only policy is the contrast case: it fills at the signal
    # bar's own close (105) and the manifest flags it as optimistic.
    captured = run_engine_streaming(
        BacktestEngine(
            strategy=_BuyOnceStrategy(),
            bars=_bars(),
            initial_cash=Decimal("10000"),
            execution_timing=ExecutionTimingModel.research_only(),
        ),
        tmp_path / "same-bar-close",
    )

    assert len(captured.fills) == 1
    assert Decimal(captured.fills[0]["price"]) == Decimal("105")
    assert captured.result.final_account.cash["USD"] == Decimal("8950")

    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "same_bar_close"
    assert assumptions["optimistic"] is True
    assert assumptions["promotion_grade"] is False


def test_config_fill_policy_next_bar_open_is_promotion_grade(tmp_path: Path) -> None:
    # The config-driven path (BacktestEngine.from_config) must honor the
    # config's fill_policy. This is the gap C1 closes: previously from_config
    # ignored the config and always defaulted to optimistic same_bar_close.
    engine = BacktestEngine.from_config(
        _make_config(fill_policy="next_bar_open"),
        bars=_bars(),
        strategy=_BuyOnceStrategy(),
    )
    captured = run_engine_streaming(engine, tmp_path / "cfg-next-bar-open")

    assert Decimal(captured.fills[0]["price"]) == Decimal("110")
    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "next_bar_open"
    assert assumptions["promotion_grade"] is True


def test_config_default_fill_policy_is_optimistic_same_bar_close(tmp_path: Path) -> None:
    # A config that does not opt into next_bar_open stays backward-compatible
    # (same_bar_close) and the manifest flags it as not promotion-grade.
    engine = BacktestEngine.from_config(
        _make_config(),
        bars=_bars(),
        strategy=_BuyOnceStrategy(),
    )
    captured = run_engine_streaming(engine, tmp_path / "cfg-default")

    assert Decimal(captured.fills[0]["price"]) == Decimal("105")
    assumptions = captured.manifest["execution_assumptions"]
    assert assumptions["fill_policy"] == "same_bar_close"
    assert assumptions["promotion_grade"] is False


def test_next_bar_open_decision_on_final_bar_has_no_fill(tmp_path: Path) -> None:
    # A decision at the last bar has no next obtainable price, so it never
    # fills -- the next_bar_open policy refuses to invent a price.
    class _BuyOnLastBar(Strategy):
        def initialize(self, ctx: Any) -> None:
            self.asset = ctx.symbol("AAPL")
            self._seen = 0

        def on_bar(self, ctx: Any, bar: object) -> None:
            self._seen += 1
            if self._seen == 2:
                ctx.target_quantity(self.asset, Decimal("10"))

    captured = run_engine_streaming(
        BacktestEngine(
            strategy=_BuyOnLastBar(),
            bars=_bars(),
            initial_cash=Decimal("10000"),
            execution_timing=ExecutionTimingModel.promotion_grade(),
        ),
        tmp_path / "final-bar-no-fill",
    )

    assert captured.fills == ()
    assert captured.result.final_account.positions == {}
    assert captured.result.final_account.cash["USD"] == Decimal("10000")
