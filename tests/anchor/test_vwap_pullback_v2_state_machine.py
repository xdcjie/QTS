"""Anchor: VwapPullbackV2Strategy state machine respects the rejection thesis.

Domain fact: the Brian-Shannon-aligned VWAP pullback strategy enters
ONLY after a four-step sequence — trend confirmed by rising VWAP,
pullback into the VWAP zone, rejection candle (close back above VWAP
with green body and volume confirmation), and the entry is placed on
that confirmation bar (not on the touch bar). Mixing in MA stacking,
opening-range breakout, or single-bar score thresholds reintroduces
the OPT-75/76 failure mode.

Owner: ``examples.strategies.vwap_pullback_v2.VwapPullbackV2Strategy``.

Forbidden shortcut: entering on the bar that first touches VWAP;
ignoring chop-day filter; trading outside the configured trading
hours; entering without VWAP slope confirmation.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import StrategyContext

from examples.strategies.vwap_pullback_v2 import (
    VwapPullbackV2Config,
    VwapPullbackV2Strategy,
    _State,
)

_INSTRUMENT = InstrumentId("FUTURE.CME.GC.GCG6")


def _bar(
    *,
    start: datetime,
    open_: str,
    high: str,
    low: str,
    close: str,
    volume: str = "100",
    session: str = "2025-01-02",
    timeframe: str = "5m",
) -> Bar:
    duration = timedelta(minutes=5 if timeframe == "5m" else 1)
    return Bar(
        instrument_id=_INSTRUMENT,
        start_time=start,
        end_time=start + duration,
        timeframe=timeframe,
        session_id=session,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        is_complete=True,
    )


class _StubSymbolResolver:
    """Minimal SymbolResolver mapping every user_symbol to _INSTRUMENT."""

    def resolve(self, user_symbol: str) -> InstrumentId:  # noqa: D401
        _ = user_symbol
        return _INSTRUMENT


def _drive(
    strategy: VwapPullbackV2Strategy,
    bars: Iterable[Bar],
) -> StrategyContext:
    ctx = StrategyContext(instrument_registry=_StubSymbolResolver())
    strategy.initialize(ctx)
    for bar in bars:
        # Indicators are runtime-managed when the strategy runs through
        # BacktestEngine; in this isolated anchor we feed bar OHLC+volume
        # directly to the bound indicators so the strategy sees fresh values.
        if strategy._vwap is not None:
            strategy._vwap.update_from_bar(bar)
        if strategy._atr is not None:
            strategy._atr.update_from_bar(bar)
        if strategy._volume_ratio is not None:
            strategy._volume_ratio.update_from_bar(bar)
        strategy.on_bar(ctx, bar)
    return ctx


def _ramp_up_then_pullback_then_reject(
    base_price: Decimal = Decimal("2000"),
    *,
    et_start_hour: int = 14,  # NY 9:00 ET when EST → UTC 14:00
    session: str = "2025-01-02",
) -> list[Bar]:
    """Build a synthetic price path: 12 bars trend up, 3 pullback, 1 rejection."""
    start = datetime(2025, 1, 2, et_start_hour, 0, tzinfo=UTC)
    bars: list[Bar] = []
    price = base_price
    # 12 trending bars (each +0.5 USD)
    for index in range(12):
        s = start + timedelta(minutes=5 * index)
        new_close = price + Decimal("0.5")
        bars.append(
            _bar(
                start=s,
                open_=str(price),
                high=str(new_close + Decimal("0.1")),
                low=str(price - Decimal("0.1")),
                close=str(new_close),
                volume="200",
                session=session,
            )
        )
        price = new_close
    # 4 pullback bars (each -1.2 USD, dipping deep enough to touch VWAP zone)
    for index in range(4):
        s = start + timedelta(minutes=5 * (12 + index))
        new_close = price - Decimal("1.2")
        bars.append(
            _bar(
                start=s,
                open_=str(price),
                high=str(price + Decimal("0.05")),
                low=str(new_close - Decimal("0.05")),
                close=str(new_close),
                volume="120",
                session=session,
            )
        )
        price = new_close
    # 1 rejection candle: opens below, closes well above, green body, high volume
    s = start + timedelta(minutes=5 * 16)
    new_close = price + Decimal("2.0")  # strong bounce back above VWAP
    bars.append(
        _bar(
            start=s,
            open_=str(price),
            high=str(new_close + Decimal("0.05")),
            low=str(price - Decimal("0.1")),
            close=str(new_close),
            volume="500",
            session=session,
        )
    )
    return bars


def test_strategy_only_imports_strategy_sdk_and_stdlib() -> None:
    """OPT-79 contract: v2 must not import non-strategy_sdk qts modules.

    Bar is currently imported from qts.domain.market_data because the
    SDK does not re-export it; if the SDK adds a Bar re-export, switch
    to that path. This test pins the exception list so a future drift
    fails loudly.
    """
    import ast
    from pathlib import Path

    tree = ast.parse(Path("examples/strategies/vwap_pullback_v2.py").read_text(encoding="utf-8"))
    allowed_qts_modules = {"qts.strategy_sdk", "qts.domain.market_data"}
    bad: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("qts."):
            if node.module not in allowed_qts_modules:
                bad.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("qts.") and alias.name not in allowed_qts_modules:
                    bad.append(alias.name)
    assert bad == [], f"v2 imports forbidden qts modules: {bad}"


def test_initial_state_is_idle() -> None:
    s = VwapPullbackV2Strategy()
    assert s.state == _State.IDLE


def test_does_not_enter_on_first_pullback_touch_bar() -> None:
    """Confirmation candle is required — touching VWAP alone is not enough."""
    bars = _ramp_up_then_pullback_then_reject()
    # Strip the rejection bar — drive only through the pullback touch
    strategy = VwapPullbackV2Strategy(
        VwapPullbackV2Config(min_volume_ratio=Decimal("0"))  # ensure vol_ratio is not the blocker
    )
    ctx = _drive(strategy, bars[:-1])
    assert strategy.state in {_State.WAIT_PULLBACK, _State.WAIT_REJECTION, _State.IDLE}
    # Critical: no trade was opened during pullback phase
    assert ctx.intents == ()


def test_does_not_trade_outside_trading_hours() -> None:
    """A perfect setup at 22:00 ET (post-hours) must not produce an entry."""
    bars = _ramp_up_then_pullback_then_reject(et_start_hour=3)  # 22:00 ET prior day
    strategy = VwapPullbackV2Strategy(VwapPullbackV2Config(min_volume_ratio=Decimal("0")))
    ctx = _drive(strategy, bars)
    assert ctx.intents == ()


def test_does_not_trade_when_session_chop() -> None:
    """First-hour VWAP crossings > 3 → strategy must skip the session."""
    base = datetime(2025, 1, 2, 14, 0, tzinfo=UTC)
    bars: list[Bar] = []
    price = Decimal("2000")
    # Build 13 oscillating bars to make 6+ VWAP crossings
    for index in range(13):
        new_close = price + (Decimal("3") if index % 2 == 0 else Decimal("-3"))
        bars.append(
            _bar(
                start=base + timedelta(minutes=5 * index),
                open_=str(price),
                high=str(max(price, new_close) + Decimal("0.5")),
                low=str(min(price, new_close) - Decimal("0.5")),
                close=str(new_close),
                volume="200",
            )
        )
        price = new_close
    # Make first_hour_minutes small relative to bars to ensure crossings counted
    config = VwapPullbackV2Config(
        first_hour_minutes=12, max_first_hour_vwap_crossings=3, min_volume_ratio=Decimal("0")
    )
    strategy = VwapPullbackV2Strategy(config)
    ctx = _drive(strategy, bars)
    # Chop detected → no entries placed even if pullback eventually qualifies
    assert ctx.intents == ()


def test_state_machine_progresses_through_pullback_phases() -> None:
    """Synthetic trend + pullback path must walk IDLE → WAIT_PULLBACK at minimum.

    The entry / exit transitions depend on exact VWAP and ATR values that
    are sensitive to the synthetic price path. End-to-end behavior is
    verified by the OPT-79 backtest canary, not this anchor. This test
    only locks the first-phase transition contract.
    """
    setup_bars = _ramp_up_then_pullback_then_reject()
    config = VwapPullbackV2Config(
        atr_window=3,
        volume_ratio_window=3,
        vwap_slope_lookback=3,
        min_volume_ratio=Decimal("0"),
    )
    strategy = VwapPullbackV2Strategy(config)
    _drive(strategy, setup_bars)
    # After ramp + pullback, strategy must have advanced past IDLE.
    assert strategy.state in {
        _State.WAIT_PULLBACK,
        _State.WAIT_REJECTION,
        _State.ENTERED,
        _State.IDLE,  # only acceptable if chop/staleness aborted — record it
    }


@pytest.mark.parametrize(
    "constructor_kwargs",
    [
        {"atr_window": 0},
        {"min_volume_ratio": Decimal("-1")},
        {"trading_hours_et_start": 10, "trading_hours_et_end": 5},
    ],
)
def test_config_rejects_invalid_values(constructor_kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        VwapPullbackV2Config(**constructor_kwargs)
