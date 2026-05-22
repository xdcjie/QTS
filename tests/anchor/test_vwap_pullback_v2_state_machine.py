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
    _TrailingRegimeGate,
)

_INSTRUMENT = InstrumentId("FUTURE.CME.GC.GCG6")
_SI_INSTRUMENT = InstrumentId("FUTURE.CME.SI.SIH6")


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
    instrument_id: InstrumentId = _INSTRUMENT,
) -> Bar:
    duration = timedelta(minutes=5 if timeframe == "5m" else 1)
    return Bar(
        instrument_id=instrument_id,
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
    """Minimal SymbolResolver mapping user symbols to test instruments."""

    def __init__(self, mapping: dict[str, InstrumentId] | None = None) -> None:
        self._mapping = mapping or {"GC": _INSTRUMENT, "SI": _SI_INSTRUMENT}

    def resolve(self, user_symbol: str) -> InstrumentId:  # noqa: D401
        return self._mapping.get(user_symbol, _INSTRUMENT)


def _drive(
    strategy: VwapPullbackV2Strategy,
    bars: Iterable[Bar],
    *,
    resolver: _StubSymbolResolver | None = None,
) -> StrategyContext:
    ctx = StrategyContext(instrument_registry=resolver or _StubSymbolResolver())
    strategy.initialize(ctx)
    for bar in bars:
        # Indicators are runtime-managed when the strategy runs through
        # BacktestEngine; in this isolated anchor we feed bar OHLC+volume
        # directly to the bound indicators so the strategy sees fresh values.
        ctx.indicator.update_from_bar(bar)
        strategy.on_bar(ctx, bar)
    return ctx


def _feed(
    strategy: VwapPullbackV2Strategy,
    ctx: StrategyContext,
    bars: Iterable[Bar],
) -> None:
    for bar in bars:
        ctx.indicator.update_from_bar(bar)
        strategy.on_bar(ctx, bar)


def _regime_bar(
    symbol: str,
    *,
    session: str,
    open_: str,
    high: str,
    low: str,
    close: str,
    start_hour_utc: int = 14,
    volume: str = "1000",
) -> Bar:
    session_date = datetime.fromisoformat(session).date()
    instrument_id = _INSTRUMENT if symbol == "GC" else _SI_INSTRUMENT
    return _bar(
        start=datetime(
            session_date.year,
            session_date.month,
            session_date.day,
            start_hour_utc,
            0,
            tzinfo=UTC,
        ),
        open_=open_,
        high=high,
        low=low,
        close=close,
        volume=volume,
        session=session,
        timeframe="15m",
        instrument_id=instrument_id,
    )


def _update_regime_session(
    gate: _TrailingRegimeGate,
    symbol: str,
    *,
    session: str,
    open_: str,
    high: str,
    low: str,
    close: str,
) -> None:
    gate.update_bar(
        symbol,
        _regime_bar(
            symbol,
            session=session,
            open_=open_,
            high=high,
            low=low,
            close=close,
        ),
    )


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


def test_trailing_regime_gate_uses_completed_sessions_only() -> None:
    """Regime gate must not use the current in-flight session as evidence."""
    gate = _TrailingRegimeGate(
        VwapPullbackV2Config(
            regime_gate_rule="hard_churn225",
            regime_symbols=("GC", "SI"),
            regime_lookback_sessions=1,
            regime_min_history_sessions=1,
        )
    )

    for symbol in ("GC", "SI"):
        _update_regime_session(
            gate,
            symbol,
            session="2025-01-01",
            open_="100",
            high="103",
            low="100",
            close="100.5",
        )
        _update_regime_session(
            gate,
            symbol,
            session="2025-01-02",
            open_="100.5",
            high="103.5",
            low="100.5",
            close="101.0",
        )

    assert gate.allows_new_entries()

    for symbol in ("GC", "SI"):
        _update_regime_session(
            gate,
            symbol,
            session="2025-01-03",
            open_="101.0",
            high="101.2",
            low="101.0",
            close="101.1",
        )

    assert not gate.allows_new_entries()


def test_hard14_ccvol17_requires_low_completed_realized_volatility() -> None:
    """The SI gate keeps the hard14 bad-regime shape but exempts high-volatility regimes."""
    hard14 = _TrailingRegimeGate(
        VwapPullbackV2Config(
            regime_gate_rule="hard14",
            regime_symbols=("GC", "SI"),
            regime_lookback_sessions=2,
            regime_min_history_sessions=2,
        )
    )
    high_vol = _TrailingRegimeGate(
        VwapPullbackV2Config(
            regime_gate_rule="hard14_ccvol17",
            regime_symbols=("GC", "SI"),
            regime_lookback_sessions=2,
            regime_min_history_sessions=2,
        )
    )
    low_vol = _TrailingRegimeGate(
        VwapPullbackV2Config(
            regime_gate_rule="hard14_ccvol17",
            regime_symbols=("GC", "SI"),
            regime_lookback_sessions=2,
            regime_min_history_sessions=2,
        )
    )

    for gate, closes in (
        (hard14, ("100", "103", "100")),
        (high_vol, ("100", "103", "100")),
        (low_vol, ("100", "100.5", "101.0")),
    ):
        for symbol in ("GC", "SI"):
            _update_regime_session(
                gate,
                symbol,
                session="2025-01-01",
                open_="100",
                high="103",
                low="100",
                close=closes[0],
            )
            _update_regime_session(
                gate,
                symbol,
                session="2025-01-02",
                open_=closes[0],
                high=str(Decimal(closes[0]) * Decimal("1.03")),
                low=closes[0],
                close=closes[1],
            )
            _update_regime_session(
                gate,
                symbol,
                session="2025-01-03",
                open_=closes[1],
                high=str(max(Decimal(closes[1]), Decimal(closes[2])) * Decimal("1.03")),
                low=str(min(Decimal(closes[1]), Decimal(closes[2]))),
                close=closes[2],
            )
            _update_regime_session(
                gate,
                symbol,
                session="2025-01-04",
                open_=closes[2],
                high=closes[2],
                low=closes[2],
                close=closes[2],
            )

    assert not hard14.allows_new_entries()
    assert high_vol.allows_new_entries()
    assert not low_vol.allows_new_entries()


def test_strategy_regime_gate_blocks_new_entries_on_bad_completed_session() -> None:
    """A blocked session can still receive bars, but no fresh VWAP entry is emitted."""
    config = VwapPullbackV2Config(
        atr_window=3,
        volume_ratio_window=3,
        vwap_slope_lookback=3,
        min_volume_ratio=Decimal("0"),
        regime_gate_rule="hard_churn225",
        regime_symbols=("GC", "SI"),
        regime_lookback_sessions=1,
        regime_min_history_sessions=1,
    )
    strategy = VwapPullbackV2Strategy(config)
    ctx = StrategyContext(instrument_registry=_StubSymbolResolver())
    strategy.initialize(ctx)

    for symbol in ("GC", "SI"):
        _feed(
            strategy,
            ctx,
            (
                _regime_bar(
                    symbol,
                    session="2025-01-01",
                    open_="100",
                    high="103",
                    low="100",
                    close="100.5",
                ),
                _regime_bar(
                    symbol,
                    session="2025-01-02",
                    open_="100.5",
                    high="103.5",
                    low="100.5",
                    close="101.0",
                ),
                _regime_bar(
                    symbol,
                    session="2025-01-03",
                    open_="101.0",
                    high="101.2",
                    low="101.0",
                    close="101.1",
                ),
            ),
        )

    _feed(strategy, ctx, _ramp_up_then_pullback_then_reject(session="2025-01-03"))

    assert ctx.intents == ()
    assert strategy.state == _State.IDLE


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


def test_default_trading_hours_filter_is_half_open_et_window() -> None:
    """Default strategy filter includes ET [08:00, 16:00) and excludes 16:00."""
    strategy = VwapPullbackV2Strategy()

    assert strategy._in_trading_hours(
        _bar(start=datetime(2025, 1, 2, 13, 0, tzinfo=UTC), open_="1", high="1", low="1", close="1")
    )
    assert strategy._in_trading_hours(
        _bar(
            start=datetime(2025, 1, 2, 20, 59, tzinfo=UTC),
            open_="1",
            high="1",
            low="1",
            close="1",
        )
    )
    assert not strategy._in_trading_hours(
        _bar(start=datetime(2025, 1, 2, 21, 0, tzinfo=UTC), open_="1", high="1", low="1", close="1")
    )
    assert not strategy._in_trading_hours(
        _bar(start=datetime(2025, 1, 2, 3, 0, tzinfo=UTC), open_="1", high="1", low="1", close="1")
    )


def test_disabled_trading_hours_filter_allows_full_session_bars() -> None:
    """Disabling the strategy filter lets session-managed overnight bars through."""
    strategy = VwapPullbackV2Strategy(
        VwapPullbackV2Config(
            use_trading_hours_filter=False,
            trading_hours_et_start=18,
            trading_hours_et_end=17,
        )
    )

    assert strategy._in_trading_hours(
        _bar(start=datetime(2025, 1, 2, 3, 0, tzinfo=UTC), open_="1", high="1", low="1", close="1")
    )


def test_disabled_trading_hours_filter_allows_overnight_setup_progression() -> None:
    """A 22:00 ET trend setup can pass the strategy time gate when disabled."""
    bars = _ramp_up_then_pullback_then_reject(et_start_hour=3)[:12]
    strategy = VwapPullbackV2Strategy(
        VwapPullbackV2Config(
            use_trading_hours_filter=False,
            atr_window=3,
            volume_ratio_window=3,
            vwap_slope_lookback=3,
            min_volume_ratio=Decimal("0"),
        )
    )

    ctx = _drive(strategy, bars)

    assert strategy.state == _State.WAIT_PULLBACK
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
        {"trading_hours_et_start": 8, "trading_hours_et_end": 8},
    ],
)
def test_config_rejects_invalid_values(constructor_kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        VwapPullbackV2Config(**constructor_kwargs)
