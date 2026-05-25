from __future__ import annotations

import json
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from zoneinfo import ZoneInfo

from qts.domain.market_data import Bar
from qts.domain.positions import PositionSide
from qts.indicators.technical import (
    DirectionalMovementValue,
    DonchianChannelValue,
    MACDValue,
)
from qts.strategy_sdk import StrategyContext

from strategies.research.vwap_factor_research import (
    VwapFactorResearchConfig,
    VwapFactorResearchStrategy,
    _State,
)


@dataclass(frozen=True)
class FakeAsset:
    symbol: str


@dataclass
class FakeIndicator:
    ready: bool = True
    value: Any = Decimal("0")


@dataclass(frozen=True)
class FakeBar:
    session_id: str = "2026-05-20"
    start_time: datetime = datetime(2026, 5, 20, 21, 45, tzinfo=UTC)
    end_time: datetime = datetime(2026, 5, 20, 22, 0, tzinfo=UTC)
    open: Decimal = Decimal("100")
    high: Decimal = Decimal("102")
    low: Decimal = Decimal("99")
    close: Decimal = Decimal("101")
    volume: Decimal = Decimal("1000")


class FakeIndicatorFactory:
    def __init__(self) -> None:
        self.created: dict[tuple[str, int | None], FakeIndicator] = {}

    def session_vwap(self, asset: FakeAsset) -> FakeIndicator:
        return self._indicator("session_vwap", None)

    def atr(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("atr", window)

    def volume_ratio(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("volume_ratio", window)

    def rsi(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("rsi", window)

    def adx(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("adx", window)

    def money_flow_index(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("mfi", window)

    def chaikin_money_flow(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("cmf", window)

    def rate_of_change(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("roc", window)

    def cci(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("cci", window)

    def stochastic(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("stochastic", window)

    def williams_r(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("williams_r", window)

    def bollinger_bands(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("bollinger", window)

    def donchian_channel(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("donchian", window)

    def keltner_channel(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("keltner", window)

    def macd(
        self,
        asset: FakeAsset,
        fast_window: int,
        slow_window: int,
        signal_window: int,
    ) -> FakeIndicator:
        return self._indicator("macd", None)

    def sma(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("sma", window)

    def _indicator(self, name: str, window: int | None) -> FakeIndicator:
        indicator = FakeIndicator()
        self.created[(name, window)] = indicator
        return indicator


class FakeContext:
    def __init__(self) -> None:
        self.indicator = FakeIndicatorFactory()
        self.intents: list[tuple[str, FakeAsset, Decimal | None, dict[str, str] | None]] = []
        self.subscriptions: list[tuple[FakeAsset, str, int]] = []

    def symbol(self, symbol: str) -> FakeAsset:
        return FakeAsset(symbol=symbol)

    def subscribe(self, asset: FakeAsset, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(
        self,
        asset: FakeAsset,
        quantity: Decimal,
        *,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        self.intents.append(
            ("target_quantity", asset, quantity, None if metadata is None else dict(metadata))
        )

    def close(self, asset: FakeAsset, *, metadata: dict[str, str] | None = None) -> None:
        self.intents.append(("close", asset, None, metadata))


def test_research_strategy_declares_main_bar_timeframe_subscription() -> None:
    config = VwapFactorResearchConfig(timeframe="3m")
    _strategy, ctx = initialized_strategy(config)

    assert ctx.subscriptions == [(FakeAsset(symbol="GC"), "3m", config.required_warmup_bars)]


def test_ma_50_200_filter_requires_alignment_with_trade_direction() -> None:
    strategy, ctx = initialized_strategy()
    ctx.indicator.created[("sma", 50)].value = Decimal("105")
    ctx.indicator.created[("sma", 200)].value = Decimal("100")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "ma50_200_aligned", _bar(), Decimal("100"), Decimal("2")
    )

    ctx.indicator.created[("sma", 50)].value = Decimal("95")

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "ma50_200_aligned", _bar(), Decimal("100"), Decimal("2")
    )


def test_ma_20_80_min_filter_requires_directional_minimum_spread() -> None:
    strategy, ctx = initialized_strategy(VwapFactorResearchConfig(ma20_80_min_abs=Decimal("2")))
    ctx.indicator.created[("sma", 20)].value = Decimal("103")
    ctx.indicator.created[("sma", 80)].value = Decimal("100")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "ma20_80_min", _bar(), Decimal("100"), Decimal("2")
    )

    ctx.indicator.created[("sma", 20)].value = Decimal("101")

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "ma20_80_min", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)  # noqa: SLF001
    ctx.indicator.created[("sma", 20)].value = Decimal("97")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "ma20_80_min", _bar(), Decimal("100"), Decimal("2")
    )


def test_technical_score_filter_counts_multiple_confirmation_rules() -> None:
    strategy, ctx = initialized_strategy(VwapFactorResearchConfig(technical_score_min=4))
    ctx.indicator.created[("macd", None)].value = MACDValue(
        macd=Decimal("1"),
        signal=Decimal("0"),
        histogram=Decimal("1"),
    )
    ctx.indicator.created[("adx", 14)].value = DirectionalMovementValue(
        plus_di=Decimal("30"),
        minus_di=Decimal("10"),
        dx=Decimal("50"),
        adx=Decimal("20"),
    )
    ctx.indicator.created[("roc", 15)].value = Decimal("0.5")
    ctx.indicator.created[("roc", 60)].value = Decimal("0.2")
    ctx.indicator.created[("sma", 20)].value = Decimal("102")
    ctx.indicator.created[("sma", 80)].value = Decimal("100")
    ctx.indicator.created[("donchian", 60)].value = DonchianChannelValue(
        lower=Decimal("90"),
        middle=Decimal("100"),
        upper=Decimal("110"),
    )
    ctx.indicator.created[("rsi", 14)].value = Decimal("50")
    ctx.indicator.created[("mfi", 14)].value = Decimal("55")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "technical_score_min", _bar(), Decimal("100"), Decimal("2")
    )


def test_vwap_slope_strength_filter_requires_directional_atr_scaled_slope() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(vwap_slope_min_atr=Decimal("0.2"))
    )
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (Decimal("100.0"), Decimal("100.1"), Decimal("100.2"), Decimal("100.4"), Decimal("100.6"))
    )

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_slope_strength", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._session.vwap_history.clear()  # noqa: SLF001
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (Decimal("100.0"), Decimal("100.05"), Decimal("100.1"), Decimal("100.2"), Decimal("100.3"))
    )

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_slope_strength", _bar(), Decimal("100"), Decimal("2")
    )


def test_atr_pct_range_filter_bounds_current_volatility_regime() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            atr_pct_min=Decimal("0.005"),
            atr_pct_max=Decimal("0.015"),
        )
    )

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "atr_pct_range", _bar(close=Decimal("100")), Decimal("100"), Decimal("1")
    )
    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "atr_pct_range", _bar(close=Decimal("100")), Decimal("100"), Decimal("2")
    )


def test_session_sigma_range_filter_bounds_intraday_noise_regime() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            session_sigma_min_atr=Decimal("0.1"),
            session_sigma_max_atr=Decimal("0.6"),
        )
    )
    strategy._session.sum_var_x_vol = Decimal("1")  # noqa: SLF001
    strategy._session.sum_vol = Decimal("4")  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "session_sigma_range", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._session.sum_var_x_vol = Decimal("9")  # noqa: SLF001
    strategy._session.sum_vol = Decimal("1")  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "session_sigma_range", _bar(), Decimal("100"), Decimal("2")
    )


def test_session_sigma_or_ma20_80_min_keeps_sigma_cap() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            ma20_80_min_abs=Decimal("2"),
            session_sigma_min_atr=Decimal("0.9"),
            session_sigma_max_atr=Decimal("1.5"),
        )
    )
    ctx.indicator.created[("sma", 20)].value = Decimal("103")
    ctx.indicator.created[("sma", 80)].value = Decimal("100")
    strategy._session.sum_var_x_vol = Decimal("1")  # noqa: SLF001
    strategy._session.sum_vol = Decimal("1")  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "session_sigma_or_ma20_80_min", _bar(), Decimal("100"), Decimal("2")
    )

    ctx.indicator.created[("sma", 20)].value = Decimal("101")

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "session_sigma_or_ma20_80_min", _bar(), Decimal("100"), Decimal("2")
    )

    ctx.indicator.created[("sma", 20)].value = Decimal("103")
    strategy._session.sum_var_x_vol = Decimal("16")  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "session_sigma_or_ma20_80_min", _bar(), Decimal("100"), Decimal("2")
    )


def test_vwap_acceptance_filter_requires_directional_close_acceptance() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            vwap_acceptance_window=4,
            vwap_acceptance_min=Decimal("0.75"),
        )
    )
    strategy._session.vwap_position_history.extend((1, 1, 1, -1))  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance", _bar(), Decimal("100"), Decimal("2")
    )


def test_trend_efficiency_filter_requires_directional_low_churn_vwap_path() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            trend_efficiency_lookback=4,
            trend_efficiency_min=Decimal("0.80"),
        )
    )
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (Decimal("100"), Decimal("101"), Decimal("102"), Decimal("103"), Decimal("104"))
    )

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "trend_efficiency", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._session.vwap_history.clear()  # noqa: SLF001
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (Decimal("100"), Decimal("102"), Decimal("101"), Decimal("103"), Decimal("102"))
    )

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "trend_efficiency", _bar(), Decimal("100"), Decimal("2")
    )


def test_trend_age_filter_rejects_too_young_and_late_trends() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(trend_age_min_bars=2, trend_age_max_bars=5)
    )
    strategy._session.trend_direction = 1  # noqa: SLF001
    strategy._session.trend_age_bars = 3  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "trend_age", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._session.trend_age_bars = 1  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "trend_age", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._session.trend_age_bars = 6  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "trend_age", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)  # noqa: SLF001
    strategy._session.trend_direction = -1  # noqa: SLF001
    strategy._session.trend_age_bars = 3  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "trend_age", _bar(), Decimal("100"), Decimal("2")
    )


def test_range_expansion_filter_uses_prior_same_minute_ranges() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            range_expansion_min=Decimal("1.4"),
            range_expansion_max=Decimal("1.6"),
        )
    )
    bar = _bar(high=Decimal("103"), low=Decimal("100"))
    minute = strategy._et_minute(bar)  # noqa: SLF001
    strategy._session_range_curve_history[minute] = deque(  # noqa: SLF001
        (Decimal("2"), Decimal("2"), Decimal("2"), Decimal("2"), Decimal("2")),
        maxlen=strategy._config.range_expansion_lookback_sessions + 1,  # noqa: SLF001
    )
    strategy._update_session_state(bar)  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "range_expansion", bar, Decimal("100"), Decimal("2")
    )

    strategy._config = VwapFactorResearchConfig(  # noqa: SLF001
        range_expansion_min=Decimal("1.6"),
        range_expansion_max=Decimal("2.0"),
    )

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "range_expansion", bar, Decimal("100"), Decimal("2")
    )


def test_vwap_acceptance_or_range_expansion_allows_trend_escape() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            vwap_acceptance_window=4,
            vwap_acceptance_min=Decimal("0.75"),
            range_expansion_min=Decimal("1.4"),
            range_expansion_max=Decimal("2.0"),
        )
    )
    bar = _bar(high=Decimal("103"), low=Decimal("100"))
    minute = strategy._et_minute(bar)  # noqa: SLF001
    strategy._session.vwap_position_history.extend((1, -1, -1, -1))  # noqa: SLF001
    strategy._session_range_curve_history[minute] = deque(  # noqa: SLF001
        (Decimal("2"), Decimal("2"), Decimal("2"), Decimal("2"), Decimal("2")),
        maxlen=strategy._config.range_expansion_lookback_sessions + 1,  # noqa: SLF001
    )
    strategy._update_session_state(bar)  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance_or_range_expansion", bar, Decimal("100"), Decimal("2")
    )

    strategy._session.session_high = Decimal("101")  # noqa: SLF001
    strategy._session.session_low = Decimal("100")  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance_or_range_expansion", bar, Decimal("100"), Decimal("2")
    )


def test_vwap_acceptance_if_bad_regime_only_tightens_blocked_regime() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            bad_regime_rule="hard14",
            bad_regime_lookback_sessions=1,
            bad_regime_min_history_sessions=1,
            bad_regime_unready_policy="allow",
            vwap_acceptance_window=4,
            vwap_acceptance_min=Decimal("0.75"),
        )
    )
    strategy._session.vwap_position_history.extend((1, -1, -1, -1))  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance_if_bad_regime", _bar(), Decimal("100"), Decimal("2")
    )

    _feed_bad_regime_sessions(strategy)

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance_if_bad_regime", _bar(session_id="2026-05-23"), Decimal("100"), Decimal("2")
    )

    strategy._session.vwap_position_history.clear()  # noqa: SLF001
    strategy._session.vwap_position_history.extend((1, 1, 1, -1))  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_acceptance_if_bad_regime", _bar(session_id="2026-05-23"), Decimal("100"), Decimal("2")
    )


def test_mom120_min_if_bad_regime_only_tightens_blocked_regime() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            bad_regime_rule="hard14",
            bad_regime_lookback_sessions=1,
            bad_regime_min_history_sessions=1,
            bad_regime_unready_policy="allow",
            ts_momentum_min_abs=Decimal("1.25"),
        )
    )
    ctx.indicator.created[("roc", 120)].value = Decimal("0.5")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "mom120_min_if_bad_regime", _bar(), Decimal("100"), Decimal("2")
    )

    _feed_bad_regime_sessions(strategy)

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "mom120_min_if_bad_regime", _bar(session_id="2026-05-23"), Decimal("100"), Decimal("2")
    )

    ctx.indicator.created[("roc", 120)].value = Decimal("1.5")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "mom120_min_if_bad_regime", _bar(session_id="2026-05-23"), Decimal("100"), Decimal("2")
    )


def test_vwap_slope_strength_if_bad_regime_only_tightens_blocked_regime() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            bad_regime_rule="hard14",
            bad_regime_lookback_sessions=1,
            bad_regime_min_history_sessions=1,
            bad_regime_unready_policy="allow",
            vwap_slope_min_atr=Decimal("0.20"),
        )
    )
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (
            Decimal("100.0"),
            Decimal("100.02"),
            Decimal("100.04"),
            Decimal("100.06"),
            Decimal("100.08"),
        )
    )

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_slope_strength_if_bad_regime", _bar(), Decimal("100"), Decimal("2")
    )

    _feed_bad_regime_sessions(strategy)

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_slope_strength_if_bad_regime",
        _bar(session_id="2026-05-23"),
        Decimal("100"),
        Decimal("2"),
    )

    strategy._session.vwap_history.clear()  # noqa: SLF001
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (
            Decimal("100.0"),
            Decimal("100.2"),
            Decimal("100.4"),
            Decimal("100.6"),
            Decimal("100.8"),
        )
    )

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "vwap_slope_strength_if_bad_regime",
        _bar(session_id="2026-05-23"),
        Decimal("100"),
        Decimal("2"),
    )


def test_rth_drive_min_atr_filter_requires_directional_open_drive_strength() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(rth_drive_min_atr=Decimal("0.5"))
    )
    strategy._session.rth_drive = Decimal("2")  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "rth_drive_min_atr", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._session.rth_drive = Decimal("-2")  # noqa: SLF001

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "rth_drive_min_atr", _bar(), Decimal("100"), Decimal("2")
    )

    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "rth_drive_min_atr", _bar(), Decimal("100"), Decimal("2")
    )


def test_rejection_quality_filter_requires_directional_close_location_and_body() -> None:
    strategy, _ctx = initialized_strategy(
        VwapFactorResearchConfig(
            rejection_close_location_min=Decimal("0.70"),
            rejection_body_ratio_min=Decimal("0.45"),
        )
    )

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "rejection_quality",
        _bar(open=Decimal("100"), high=Decimal("102"), low=Decimal("99"), close=Decimal("101.5")),
        Decimal("100"),
        Decimal("2"),
    )
    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "rejection_quality",
        _bar(open=Decimal("100"), high=Decimal("102"), low=Decimal("99"), close=Decimal("100.5")),
        Decimal("100"),
        Decimal("2"),
    )

    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)  # noqa: SLF001

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "rejection_quality",
        _bar(open=Decimal("101"), high=Decimal("102"), low=Decimal("99"), close=Decimal("99.5")),
        Decimal("100"),
        Decimal("2"),
    )


def test_trend_regime_filter_combines_slope_momentum_and_moving_average_alignment() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(vwap_slope_min_atr=Decimal("0.2"))
    )
    strategy._session.vwap_history.extend(  # noqa: SLF001
        (Decimal("100.0"), Decimal("100.1"), Decimal("100.2"), Decimal("100.4"), Decimal("100.6"))
    )
    ctx.indicator.created[("roc", 120)].value = Decimal("0.5")
    ctx.indicator.created[("sma", 20)].value = Decimal("103")
    ctx.indicator.created[("sma", 80)].value = Decimal("100")

    assert strategy._factor_filter_passes(  # noqa: SLF001
        "trend_regime_aligned", _bar(), Decimal("100"), Decimal("2")
    )

    ctx.indicator.created[("sma", 20)].value = Decimal("99")

    assert not strategy._factor_filter_passes(  # noqa: SLF001
        "trend_regime_aligned", _bar(), Decimal("100"), Decimal("2")
    )


def test_required_warmup_bars_covers_enabled_factor_filters() -> None:
    config = VwapFactorResearchConfig(
        factor_filters=(
            "session_sigma_range",
            "mom120_aligned",
            "technical_score_min",
            "volume_curve_range",
        )
    )

    assert config.required_warmup_bars == 121


def test_factor_diagnostics_record_values_and_failed_filter() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            factor_filters=("session_sigma_range", "mom120_aligned"),
            session_sigma_min_atr=Decimal("0.1"),
            session_sigma_max_atr=Decimal("0.2"),
        )
    )
    strategy._session.sum_var_x_vol = Decimal("9")  # noqa: SLF001
    strategy._session.sum_vol = Decimal("1")  # noqa: SLF001
    ctx.indicator.created[("roc", 120)].value = Decimal("0.5")

    assert not strategy._factor_filters_pass(_bar(), Decimal("100"), Decimal("2"))  # noqa: SLF001

    assert strategy.factor_diagnostics == (
        {
            "filter": "session_sigma_range",
            "passed": False,
            "value": "1.5",
        },
    )


def test_entry_intent_metadata_carries_factor_diagnostics_for_artifacts() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            factor_filters=("session_sigma_range", "mom120_aligned"),
            session_sigma_min_atr=Decimal("0.05"),
            session_sigma_max_atr=Decimal("0.20"),
        )
    )
    strategy._session.sum_var_x_vol = Decimal("0.04")  # noqa: SLF001
    strategy._session.sum_vol = Decimal("1")  # noqa: SLF001
    ctx.indicator.created[("roc", 120)].value = Decimal("0.5")
    ctx.indicator.created[("volume_ratio", 20)].value = Decimal("2")

    strategy._step_wait_rejection(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), close=Decimal("101")),
        Decimal("100"),
        Decimal("2"),
    )

    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert json.loads(metadata["factor_diagnostics"]) == [
        {"filter": "session_sigma_range", "passed": True, "value": "0.1"},
        {"filter": "mom120_aligned", "passed": True, "value": "0.5"},
    ]


def test_overnight_research_time_windows_are_half_open_in_exchange_time() -> None:
    overnight = VwapFactorResearchStrategy(VwapFactorResearchConfig(time_window="overnight_18_06"))

    assert overnight._time_allowed(_bar_at_et(23, 30))  # noqa: SLF001
    assert overnight._time_allowed(_bar_at_et(1, 30))  # noqa: SLF001
    assert not overnight._time_allowed(_bar_at_et(6, 0))  # noqa: SLF001

    extended = VwapFactorResearchStrategy(VwapFactorResearchConfig(time_window="night_18_08"))

    assert extended._time_allowed(_bar_at_et(7, 59))  # noqa: SLF001
    assert not extended._time_allowed(_bar_at_et(8, 0))  # noqa: SLF001
    assert not extended._time_allowed(_bar_at_et(17, 30))  # noqa: SLF001

    late_asia = VwapFactorResearchStrategy(VwapFactorResearchConfig(time_window="asia_22_02"))

    assert not late_asia._time_allowed(_bar_at_et(21, 59))  # noqa: SLF001
    assert late_asia._time_allowed(_bar_at_et(22, 0))  # noqa: SLF001
    assert late_asia._time_allowed(_bar_at_et(1, 59))  # noqa: SLF001
    assert not late_asia._time_allowed(_bar_at_et(2, 0))  # noqa: SLF001


def test_session_open_cooloff_blocks_new_session_opening_noise() -> None:
    strategy = VwapFactorResearchStrategy(
        VwapFactorResearchConfig(
            time_window="evening_18_22",
            min_session_open_minutes=30,
        )
    )

    assert not strategy._time_allowed(_bar_at_et(18, 29))  # noqa: SLF001
    assert strategy._time_allowed(_bar_at_et(18, 30))  # noqa: SLF001
    assert strategy._time_allowed(_bar_at_et(21, 59))  # noqa: SLF001


def test_default_session_open_cooloff_preserves_opening_hour_behavior() -> None:
    strategy = VwapFactorResearchStrategy(VwapFactorResearchConfig(time_window="evening_18_22"))

    assert strategy._time_allowed(_bar_at_et(18, 0))  # noqa: SLF001


def test_blocked_entry_session_mask_resets_setup_without_entry() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(blocked_entry_sessions=("2026-05-20",))
    )
    ctx.indicator.created[("session_vwap", None)].value = Decimal("100")
    ctx.indicator.created[("atr", 14)].value = Decimal("2")
    ctx.indicator.created[("volume_ratio", 20)].value = Decimal("2")

    strategy.on_bar(
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), close=Decimal("101")),
    )

    assert ctx.intents == []
    assert strategy._state == _State.IDLE  # noqa: SLF001


def test_blocked_entry_session_mask_still_allows_existing_position_exit() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(blocked_entry_sessions=("2026-05-20",))
    )
    ctx.indicator.created[("session_vwap", None)].value = Decimal("100")
    ctx.indicator.created[("atr", 14)].value = Decimal("2")
    ctx.indicator.created[("volume_ratio", 20)].value = Decimal("2")
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._entry_price = Decimal("101")  # noqa: SLF001
    strategy._stop_price = Decimal("98")  # noqa: SLF001
    strategy._target_2 = Decimal("107")  # noqa: SLF001

    strategy.on_bar(
        cast(StrategyContext, ctx),
        _bar(high=Decimal("108"), close=Decimal("106")),
    )

    assert ctx.intents[-1][0] == "close"
    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert metadata["exit_reason"] == "long_target_r_touched"


def test_session_entry_limit_blocks_second_entry_in_same_session() -> None:
    strategy, ctx = initialized_strategy(VwapFactorResearchConfig(max_entries_per_session=1))
    ctx.indicator.created[("session_vwap", None)].value = Decimal("100")
    ctx.indicator.created[("atr", 14)].value = Decimal("2")
    ctx.indicator.created[("volume_ratio", 20)].value = Decimal("2")
    strategy._session.session_id = "2026-05-20"  # noqa: SLF001
    strategy._session.entries = 1  # noqa: SLF001
    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.LONG)  # noqa: SLF001

    strategy.on_bar(
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), close=Decimal("101"), session_id="2026-05-20"),
    )

    assert ctx.intents == []
    assert strategy._state == _State.IDLE  # noqa: SLF001


def test_session_entry_limit_resets_with_new_session_state() -> None:
    strategy, ctx = initialized_strategy(VwapFactorResearchConfig(max_entries_per_session=1))
    ctx.indicator.created[("session_vwap", None)].value = Decimal("100")
    strategy._session.session_id = "2026-05-20"  # noqa: SLF001
    strategy._session.entries = 1  # noqa: SLF001

    strategy._update_session_state(_bar(session_id="2026-05-21"))  # noqa: SLF001

    assert strategy._session.session_id == "2026-05-21"  # noqa: SLF001
    assert strategy._session.entries == 0  # noqa: SLF001


def test_long_exit_levels_use_entry_price_atr_and_r_multiple() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            stop_atr_multiple=Decimal("1.5"),
            target_r_multiple=Decimal("2"),
        )
    )

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    assert strategy._entry_price == Decimal("101")  # noqa: SLF001
    assert strategy._stop_price == Decimal("98.0")  # noqa: SLF001
    assert strategy._target_2 == Decimal("107.0")  # noqa: SLF001
    assert ctx.intents[-1] == ("target_quantity", ctx.symbol("GC"), Decimal("1"), None)


def test_short_exit_levels_use_entry_price_atr_and_r_multiple() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            stop_atr_multiple=Decimal("1.5"),
            target_r_multiple=Decimal("2"),
        )
    )
    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.SHORT)  # noqa: SLF001

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), high=Decimal("103")),
        Decimal("100"),
        Decimal("2"),
    )

    assert strategy._entry_price == Decimal("101")  # noqa: SLF001
    assert strategy._stop_price == Decimal("104.0")  # noqa: SLF001
    assert strategy._target_2 == Decimal("95.0")  # noqa: SLF001
    assert ctx.intents[-1] == ("target_quantity", ctx.symbol("GC"), Decimal("-1"), None)


def test_bad_regime_target_r_multiple_only_applies_when_gate_blocks() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            bad_regime_rule="hard14",
            bad_regime_lookback_sessions=1,
            bad_regime_min_history_sessions=1,
            bad_regime_unready_policy="allow",
            bad_regime_target_r_multiple=Decimal("1.5"),
            target_r_multiple=Decimal("2"),
        )
    )
    _feed_bad_regime_sessions(strategy)

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    assert strategy._target_2 == Decimal("104.0")  # noqa: SLF001


def test_sigma_momentum_entry_sizing_reduces_quantity_for_extended_high_noise_entry() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            target_quantity=Decimal("4"),
            entry_size_rule="sigma_momentum_reduce",
            entry_size_session_sigma_min_atr=Decimal("1.0"),
            entry_size_momentum_min_abs=Decimal("2.0"),
            entry_size_reduced_quantity=Decimal("2"),
        )
    )
    strategy._session.sum_var_x_vol = Decimal("9")  # noqa: SLF001
    strategy._session.sum_vol = Decimal("1")  # noqa: SLF001
    ctx.indicator.created[("roc", 120)].value = Decimal("2.5")

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    assert ctx.intents[-1] == (
        "target_quantity",
        ctx.symbol("GC"),
        Decimal("2"),
        {"entry_size_rule": "sigma_momentum_reduce"},
    )


def test_risk_budget_entry_sizing_uses_stop_distance_and_point_value() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            entry_size_rule="risk_budget",
            risk_budget=Decimal("600"),
            risk_budget_point_value=Decimal("100"),
            risk_budget_max_quantity=Decimal("4"),
            stop_atr_multiple=Decimal("1"),
            target_quantity=Decimal("4"),
        )
    )

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    intent = ctx.intents[-1]
    assert intent[0] == "target_quantity"
    assert intent[2] == Decimal("3")
    metadata = intent[3]
    assert metadata is not None
    assert metadata["entry_size_rule"] == "risk_budget"
    assert metadata["entry_quantity"] == "3"
    assert metadata["risk_budget"] == "600"
    assert metadata["risk_per_contract"] == "200"


def test_risk_budget_entry_sizing_skips_entry_when_budget_is_below_one_contract_risk() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            entry_size_rule="risk_budget",
            risk_budget=Decimal("199"),
            risk_budget_point_value=Decimal("100"),
            stop_atr_multiple=Decimal("1"),
            target_quantity=Decimal("4"),
        )
    )

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    assert ctx.intents == []
    assert strategy._state == _State.IDLE  # noqa: SLF001
    assert strategy._session.entries == 0  # noqa: SLF001


def test_partial_runner_reduces_at_first_target_and_keeps_runner_open() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            target_quantity=Decimal("4"),
            stop_atr_multiple=Decimal("1"),
            exit_style="partial_runner",
            partial_target_r_multiple=Decimal("1"),
            partial_exit_fraction=Decimal("0.50"),
            runner_target_r_multiple=Decimal("2.5"),
            runner_stop_to_breakeven=True,
        )
    )

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("100"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), high=Decimal("102.1"), low=Decimal("99"), close=Decimal("102")),
        Decimal("100"),
    )

    assert ctx.intents[-1][0] == "target_quantity"
    assert ctx.intents[-1][2] == Decimal("2")
    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert metadata["partial_exit_reason"] == "long_partial_target_r_touched"
    assert metadata["runner_quantity"] == "2"
    assert metadata["entry_quantity"] == "4"
    assert strategy._state == _State.ENTERED  # noqa: SLF001
    assert strategy._stop_price == Decimal("100")  # noqa: SLF001


def test_partial_runner_final_exit_records_runner_diagnostics() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            target_quantity=Decimal("4"),
            stop_atr_multiple=Decimal("1"),
            exit_style="partial_runner",
            partial_target_r_multiple=Decimal("1"),
            partial_exit_fraction=Decimal("0.50"),
            runner_target_r_multiple=Decimal("2.5"),
        )
    )

    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("100"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )
    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), high=Decimal("102.1"), low=Decimal("99"), close=Decimal("102")),
        Decimal("100"),
    )
    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("102"), high=Decimal("105.2"), low=Decimal("101"), close=Decimal("105")),
        Decimal("100"),
    )

    assert ctx.intents[-1][0] == "close"
    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert metadata["exit_reason"] == "long_target_r_touched"
    assert metadata["partial_taken"] == "true"
    assert metadata["entry_quantity"] == "4"
    assert metadata["runner_quantity"] == "2"


def test_vwap_cross_does_not_exit_when_vwap_cross_exit_is_disabled() -> None:
    strategy, ctx = initialized_strategy(VwapFactorResearchConfig(exit_on_vwap_cross=False))
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._stop_price = Decimal("95")  # noqa: SLF001
    strategy._target_2 = Decimal("110")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("99"), low=Decimal("98"), high=Decimal("100")),
        Decimal("100"),
    )

    assert ctx.intents == []
    assert strategy._state == _State.ENTERED  # noqa: SLF001


def test_early_no_progress_exit_closes_long_after_adverse_move_without_progress() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            early_no_progress_exit_bars=4,
            early_no_progress_adverse_r=Decimal("0.25"),
            early_no_progress_favorable_r=Decimal("0.25"),
        )
    )
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._entry_price = Decimal("100")  # noqa: SLF001
    strategy._stop_price = Decimal("96")  # noqa: SLF001
    strategy._target_2 = Decimal("106")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), high=Decimal("100.5"), low=Decimal("98.8"), close=Decimal("99")),
        Decimal("100"),
    )

    assert ctx.intents[-1][0] == "close"
    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert metadata["exit_reason"] == "long_early_no_progress"


def test_early_no_progress_exit_keeps_long_after_favorable_progress() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            early_no_progress_exit_bars=4,
            early_no_progress_adverse_r=Decimal("0.25"),
            early_no_progress_favorable_r=Decimal("0.25"),
        )
    )
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._entry_price = Decimal("100")  # noqa: SLF001
    strategy._stop_price = Decimal("96")  # noqa: SLF001
    strategy._target_2 = Decimal("106")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(
            open=Decimal("100"),
            high=Decimal("101.2"),
            low=Decimal("98.8"),
            close=Decimal("99.5"),
        ),
        Decimal("100"),
    )

    assert ctx.intents == []
    assert strategy._state == _State.ENTERED  # noqa: SLF001


def test_early_no_progress_exit_closes_short_after_adverse_move_without_progress() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            early_no_progress_exit_bars=4,
            early_no_progress_adverse_r=Decimal("0.25"),
            early_no_progress_favorable_r=Decimal("0.25"),
        )
    )
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.SHORT  # noqa: SLF001
    strategy._entry_price = Decimal("100")  # noqa: SLF001
    strategy._stop_price = Decimal("104")  # noqa: SLF001
    strategy._target_2 = Decimal("94")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), high=Decimal("101.2"), low=Decimal("99.5"), close=Decimal("101")),
        Decimal("100"),
    )

    assert ctx.intents[-1][0] == "close"
    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert metadata["exit_reason"] == "short_early_no_progress"


def test_early_no_progress_reduce_quantity_lowers_long_position_once() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            target_quantity=Decimal("4"),
            early_no_progress_exit_bars=4,
            early_no_progress_adverse_r=Decimal("0.25"),
            early_no_progress_favorable_r=Decimal("0.25"),
            early_no_progress_action="reduce_quantity",
            early_no_progress_reduced_quantity=Decimal("2"),
        )
    )
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._entry_price = Decimal("100")  # noqa: SLF001
    strategy._stop_price = Decimal("96")  # noqa: SLF001
    strategy._target_2 = Decimal("106")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), high=Decimal("100.5"), low=Decimal("98.8"), close=Decimal("99")),
        Decimal("100"),
    )
    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("99"), high=Decimal("100"), low=Decimal("98.7"), close=Decimal("99")),
        Decimal("100"),
    )

    assert ctx.intents == [
        (
            "target_quantity",
            ctx.symbol("GC"),
            Decimal("2"),
            {
                "entry_bars": "1",
                "entry_max_adverse_r": "0.3",
                "entry_max_favorable_r": "0.125",
                "no_progress_action": "reduce_quantity",
                "target_price": "106",
            },
        )
    ]
    assert strategy._state == _State.ENTERED  # noqa: SLF001


def test_early_no_progress_reduce_target_lowers_long_r_target_without_flattening() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(
            early_no_progress_exit_bars=4,
            early_no_progress_adverse_r=Decimal("0.25"),
            early_no_progress_favorable_r=Decimal("0.25"),
            early_no_progress_action="reduce_target",
            early_no_progress_target_r_multiple=Decimal("1.25"),
        )
    )
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._entry_price = Decimal("100")  # noqa: SLF001
    strategy._stop_price = Decimal("96")  # noqa: SLF001
    strategy._target_2 = Decimal("106")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("100"), high=Decimal("100.5"), low=Decimal("98.8"), close=Decimal("99")),
        Decimal("100"),
    )

    assert ctx.intents == []
    assert strategy._target_2 == Decimal("105.00")  # noqa: SLF001
    assert strategy._state == _State.ENTERED  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("104"), high=Decimal("105.1"), low=Decimal("103"), close=Decimal("105")),
        Decimal("100"),
    )

    assert ctx.intents[-1][0] == "close"
    assert ctx.intents[-1][3] == {
        "entry_price": "100",
        "exit_reason": "long_target_r_touched",
        "stop_price": "96",
        "target_price": "105.00",
    }


def test_exit_reason_metadata_is_attached_to_close_intent() -> None:
    strategy, ctx = initialized_strategy()
    strategy._state = _State.ENTERED  # noqa: SLF001
    strategy._direction = PositionSide.LONG  # noqa: SLF001
    strategy._entry_price = Decimal("101")  # noqa: SLF001
    strategy._stop_price = Decimal("98")  # noqa: SLF001
    strategy._target_2 = Decimal("107")  # noqa: SLF001

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("106"), high=Decimal("107.1")),
        Decimal("100"),
    )

    assert ctx.intents[-1][0] == "close"
    assert ctx.intents[-1][3] == {
        "entry_price": "101",
        "exit_reason": "long_target_r_touched",
        "stop_price": "98",
        "target_price": "107",
    }


def test_exit_metadata_records_trade_level_diagnostics_for_real_entries() -> None:
    strategy, ctx = initialized_strategy(
        VwapFactorResearchConfig(stop_atr_multiple=Decimal("1"), target_r_multiple=Decimal("1"))
    )
    strategy._enter_position(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(close=Decimal("101"), low=Decimal("99")),
        Decimal("100"),
        Decimal("2"),
    )

    strategy._step_entered(  # noqa: SLF001
        cast(StrategyContext, ctx),
        _bar(open=Decimal("101"), high=Decimal("103.1"), low=Decimal("100"), close=Decimal("103")),
        Decimal("100"),
    )

    metadata = ctx.intents[-1][3]
    assert metadata is not None
    assert metadata["exit_reason"] == "long_target_r_touched"
    assert metadata["entry_quantity"] == "1"
    assert metadata["entry_bars"] == "1"
    assert metadata["entry_max_adverse_r"] == "0.5"
    assert metadata["entry_max_favorable_r"] == "1.05"


def initialized_strategy(
    config: VwapFactorResearchConfig | None = None,
) -> tuple[VwapFactorResearchStrategy, FakeContext]:
    ctx = FakeContext()
    strategy = VwapFactorResearchStrategy(config or VwapFactorResearchConfig())
    strategy.initialize(cast(StrategyContext, ctx))
    strategy._enter_state(_State.WAIT_REJECTION, PositionSide.LONG)  # noqa: SLF001
    return strategy, ctx


def _bar(
    *,
    session_id: str = "2026-05-20",
    start_time: datetime = datetime(2026, 5, 20, 21, 45, tzinfo=UTC),
    open: Decimal = Decimal("100"),
    high: Decimal = Decimal("102"),
    low: Decimal = Decimal("99"),
    close: Decimal = Decimal("101"),
) -> Bar:
    return cast(
        Bar,
        FakeBar(
            session_id=session_id,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=15),
            open=open,
            high=high,
            low=low,
            close=close,
        ),
    )


def _bar_at_et(hour: int, minute: int) -> Bar:
    et_time = datetime(2026, 5, 20, hour, minute, tzinfo=ZoneInfo("US/Eastern"))
    return cast(Bar, FakeBar(end_time=et_time))


def _feed_bad_regime_sessions(strategy: VwapFactorResearchStrategy) -> None:
    for session, open_, high, low, close in (
        ("2026-05-20", "100", "103", "100", "100.5"),
        ("2026-05-21", "100.5", "103.5", "100.5", "101.0"),
        ("2026-05-22", "101.0", "101.2", "101.0", "101.1"),
    ):
        session_date = datetime.fromisoformat(session)
        strategy._bad_regime_gate.update_bar(  # noqa: SLF001
            "GC",
            _bar(
                session_id=session,
                start_time=datetime(
                    session_date.year,
                    session_date.month,
                    session_date.day,
                    14,
                    0,
                    tzinfo=UTC,
                ),
                open=Decimal(open_),
                high=Decimal(high),
                low=Decimal(low),
                close=Decimal(close),
            ),
        )
