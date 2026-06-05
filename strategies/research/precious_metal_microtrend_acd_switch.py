from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data.bar import Bar
from qts.strategy_sdk.asset_ref import AssetRef
from qts.strategy_sdk.context import StrategyContext
from qts.strategy_sdk.data_view import DataView
from qts.strategy_sdk.strategy import Strategy


_BPS = Decimal("10000")


@dataclass
class _AcdSession:
    session_id: str | None = None
    bar_count: int = 0
    opening_high: Decimal | None = None
    opening_low: Decimal | None = None
    opening_complete: bool = False
    entries: int = 0

    @property
    def width(self) -> Decimal | None:
        if self.opening_high is None or self.opening_low is None:
            return None
        return self.opening_high - self.opening_low


class PreciousMetalMicrotrendAcdSwitchStrategy(Strategy):
    """Research-only SI/GC switch between microtrend continuation and ACD breakout."""

    def __init__(
        self,
        *,
        symbol: str = "SI",
        timeframe: str = "3m",
        micro_fast_bars: int = 3,
        micro_slow_bars: int = 12,
        micro_vwap_lookback_bars: int = 30,
        micro_volume_lookback_bars: int = 20,
        micro_atr_lookback_bars: int = 14,
        micro_entry_return_threshold: Decimal = Decimal("0.00035"),
        micro_min_volume_ratio: Decimal = Decimal("1.10"),
        micro_min_vwap_distance_bps: Decimal = Decimal("3"),
        micro_max_vwap_distance_bps: Decimal = Decimal("60"),
        micro_signal_confirm_bars: int = 1,
        micro_min_atr_bps: Decimal = Decimal("3"),
        micro_stop_atr_multiple: Decimal = Decimal("1.20"),
        micro_take_profit_atr_multiple: Decimal = Decimal("2.20"),
        micro_max_holding_bars: int = 8,
        micro_max_entries_per_session: int = 2,
        micro_min_bars_between_entries: int = 120,
        micro_post_exit_cooldown_bars: int = 60,
        micro_require_acd_opening_range: bool = False,
        micro_min_opening_range_bps: Decimal = Decimal("0"),
        acd_mode: str = "breakout",
        acd_opening_range_bars: int = 3,
        acd_max_entry_bars: int = 18,
        acd_entry_buffer_ratio: Decimal = Decimal("0.05"),
        acd_stop_range_multiple: Decimal = Decimal("0.75"),
        acd_target_range_multiple: Decimal = Decimal("1.75"),
        acd_max_holding_bars: int = 12,
        acd_max_entries_per_session: int = 1,
        target_quantity: Decimal = Decimal("1"),
        allow_short: bool = True,
        history_buffer_bars: int = 5,
    ) -> None:
        normalized_symbol = str(symbol).strip().upper()
        if not normalized_symbol:
            raise ValueError("symbol must not be empty")
        normalized_acd_mode = str(acd_mode).strip().lower()
        if normalized_acd_mode not in {"breakout", "failure"}:
            raise ValueError("acd_mode must be 'breakout' or 'failure'")
        for name, value in {
            "micro_fast_bars": micro_fast_bars,
            "micro_slow_bars": micro_slow_bars,
            "micro_vwap_lookback_bars": micro_vwap_lookback_bars,
            "micro_volume_lookback_bars": micro_volume_lookback_bars,
            "micro_atr_lookback_bars": micro_atr_lookback_bars,
            "micro_signal_confirm_bars": micro_signal_confirm_bars,
            "micro_max_holding_bars": micro_max_holding_bars,
            "micro_max_entries_per_session": micro_max_entries_per_session,
            "micro_min_bars_between_entries": micro_min_bars_between_entries,
            "micro_post_exit_cooldown_bars": micro_post_exit_cooldown_bars,
            "acd_opening_range_bars": acd_opening_range_bars,
            "acd_max_entry_bars": acd_max_entry_bars,
            "acd_max_holding_bars": acd_max_holding_bars,
            "acd_max_entries_per_session": acd_max_entries_per_session,
        }.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if micro_slow_bars < micro_fast_bars:
            raise ValueError("micro_slow_bars must be greater than or equal to micro_fast_bars")
        if acd_max_entry_bars <= acd_opening_range_bars:
            raise ValueError("acd_max_entry_bars must be greater than acd_opening_range_bars")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._symbol = normalized_symbol
        self._timeframe = str(timeframe)
        self._micro_fast_bars = micro_fast_bars
        self._micro_slow_bars = micro_slow_bars
        self._micro_vwap_lookback_bars = micro_vwap_lookback_bars
        self._micro_volume_lookback_bars = micro_volume_lookback_bars
        self._micro_atr_lookback_bars = micro_atr_lookback_bars
        self._micro_entry_return_threshold = _decimal(micro_entry_return_threshold)
        self._micro_min_volume_ratio = _decimal(micro_min_volume_ratio)
        self._micro_min_vwap_distance_bps = _decimal(micro_min_vwap_distance_bps)
        self._micro_max_vwap_distance_bps = _decimal(micro_max_vwap_distance_bps)
        self._micro_signal_confirm_bars = micro_signal_confirm_bars
        self._micro_min_atr_bps = _decimal(micro_min_atr_bps)
        self._micro_stop_atr_multiple = _decimal(micro_stop_atr_multiple)
        self._micro_take_profit_atr_multiple = _decimal(micro_take_profit_atr_multiple)
        self._micro_max_holding_bars = micro_max_holding_bars
        self._micro_max_entries_per_session = micro_max_entries_per_session
        self._micro_min_bars_between_entries = micro_min_bars_between_entries
        self._micro_post_exit_cooldown_bars = micro_post_exit_cooldown_bars
        self._micro_require_acd_opening_range = micro_require_acd_opening_range
        self._micro_min_opening_range_bps = _decimal(micro_min_opening_range_bps)
        self._acd_mode = normalized_acd_mode
        self._acd_opening_range_bars = acd_opening_range_bars
        self._acd_max_entry_bars = acd_max_entry_bars
        self._acd_entry_buffer_ratio = _decimal(acd_entry_buffer_ratio)
        self._acd_stop_range_multiple = _decimal(acd_stop_range_multiple)
        self._acd_target_range_multiple = _decimal(acd_target_range_multiple)
        self._acd_max_holding_bars = acd_max_holding_bars
        self._acd_max_entries_per_session = acd_max_entries_per_session
        self._target_quantity = _decimal(target_quantity)
        self._allow_short = allow_short
        self._history_buffer_bars = history_buffer_bars

        for name, value in {
            "micro_entry_return_threshold": self._micro_entry_return_threshold,
            "micro_min_volume_ratio": self._micro_min_volume_ratio,
            "micro_min_vwap_distance_bps": self._micro_min_vwap_distance_bps,
            "micro_max_vwap_distance_bps": self._micro_max_vwap_distance_bps,
            "micro_min_atr_bps": self._micro_min_atr_bps,
            "micro_stop_atr_multiple": self._micro_stop_atr_multiple,
            "micro_take_profit_atr_multiple": self._micro_take_profit_atr_multiple,
            "micro_min_opening_range_bps": self._micro_min_opening_range_bps,
            "acd_entry_buffer_ratio": self._acd_entry_buffer_ratio,
            "acd_stop_range_multiple": self._acd_stop_range_multiple,
            "acd_target_range_multiple": self._acd_target_range_multiple,
            "target_quantity": self._target_quantity,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._micro_min_vwap_distance_bps > self._micro_max_vwap_distance_bps:
            raise ValueError("micro_min_vwap_distance_bps must be <= micro_max_vwap_distance_bps")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")

        self._asset: AssetRef | None = None
        self._acd_session = _AcdSession()
        self._micro_session_id: str | None = None
        self._micro_session_bar_index = 0
        self._micro_session_entries = 0
        self._micro_last_entry_bar_index: int | None = None
        self._micro_last_exit_bar_index: int | None = None
        self._side = 0
        self._source: str | None = None
        self._entry_price: Decimal | None = None
        self._entry_width: Decimal | None = None
        self._entry_atr: Decimal | None = None
        self._bars_held = 0
        self._last_decision_time_by_timeframe: dict[str, object] = {}

    @property
    def _micro_required_history(self) -> int:
        return max(
            self._micro_slow_bars,
            self._micro_vwap_lookback_bars,
            self._micro_volume_lookback_bars + 1,
            self._micro_atr_lookback_bars + 1,
            self._micro_signal_confirm_bars + 1,
        )

    def initialize(self, ctx: StrategyContext) -> None:
        self._asset = ctx.future(self._symbol, contract="front")
        ctx.subscribe(
            self._asset,
            timeframe=self._timeframe,
            warmup=max(self._micro_required_history, self._acd_opening_range_bars)
            + self._history_buffer_bars,
        )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._asset is None or bar.instrument_id != self._asset.instrument_id:
            return
        if bar.timeframe != self._timeframe:
            return
        if self._last_decision_time_by_timeframe.get(self._timeframe) == bar.end_time:
            return
        self._last_decision_time_by_timeframe[self._timeframe] = bar.end_time
        self._roll_micro_session(ctx, str(bar.session_id))
        self._roll_acd_session(ctx, str(bar.session_id))
        if self._source == "microtrend":
            self._manage_micro_position(ctx, bar)
        elif self._source == "acd":
            self._manage_acd_position(ctx, bar)
        if self._side == 0:
            self._evaluate_microtrend_entry(ctx, bar)
        if self._side == 0:
            self._evaluate_acd_entry(ctx, bar)

    def _roll_micro_session(self, ctx: StrategyContext, session_id: str) -> None:
        if self._micro_session_id is None:
            self._micro_session_id = session_id
            self._micro_session_bar_index = 1
            return
        if self._micro_session_id == session_id:
            self._micro_session_bar_index += 1
            return
        if self._source == "microtrend":
            self._close(ctx, source="microtrend", reason="session_roll_flat")
        self._micro_session_id = session_id
        self._micro_session_bar_index = 1
        self._micro_session_entries = 0
        self._micro_last_entry_bar_index = None
        self._micro_last_exit_bar_index = None

    def _roll_acd_session(self, ctx: StrategyContext, session_id: str) -> None:
        if self._acd_session.session_id is None:
            self._acd_session = _AcdSession(session_id=session_id)
            return
        if self._acd_session.session_id == session_id:
            return
        if self._source == "acd":
            self._close(ctx, source="acd", reason="session_roll_flat")
        self._acd_session = _AcdSession(session_id=session_id)

    def _evaluate_microtrend_entry(self, ctx: StrategyContext, bar: Bar) -> None:
        if ctx.data is None or self._asset is None:
            return
        if self._micro_entry_blocked():
            return
        if not self._micro_opening_range_quality_allows(bar):
            return
        history = ctx.data.history(
            self._asset,
            bars=self._micro_required_history,
            timeframe=self._timeframe,
        )
        if len(history) < self._micro_required_history:
            return
        latest = history[-1]
        fast_return = _return_over_bars(history, self._micro_fast_bars)
        slow_return = _return_over_bars(history, self._micro_slow_bars)
        if abs(fast_return) < self._micro_entry_return_threshold:
            return
        if fast_return * slow_return <= Decimal("0"):
            return
        if not self._confirmed_direction(history, fast_return):
            return
        atr = _atr(history[-(self._micro_atr_lookback_bars + 1) :])
        atr_bps = (atr / latest.close * _BPS) if latest.close else Decimal("0")
        if atr_bps < self._micro_min_atr_bps:
            return
        volume_ratio = _volume_ratio(history[-(self._micro_volume_lookback_bars + 1) :])
        if volume_ratio < self._micro_min_volume_ratio:
            return
        vwap = _vwap(history[-self._micro_vwap_lookback_bars :])
        if vwap is None or vwap == Decimal("0"):
            return
        distance_bps = abs(latest.close - vwap) / vwap * _BPS
        if (
            distance_bps < self._micro_min_vwap_distance_bps
            or distance_bps > self._micro_max_vwap_distance_bps
        ):
            return
        side = 1 if fast_return > 0 else -1
        if side < 0 and not self._allow_short:
            return
        self._enter(
            ctx,
            side=side,
            price=bar.close,
            source="microtrend",
            entry_atr=atr,
            entry_width=None,
        )

    def _micro_entry_blocked(self) -> bool:
        if self._micro_session_entries >= self._micro_max_entries_per_session:
            return True
        if self._micro_last_entry_bar_index is not None:
            bars_since_entry = self._micro_session_bar_index - self._micro_last_entry_bar_index
            if bars_since_entry < self._micro_min_bars_between_entries:
                return True
        if self._micro_last_exit_bar_index is not None:
            bars_since_exit = self._micro_session_bar_index - self._micro_last_exit_bar_index
            if bars_since_exit < self._micro_post_exit_cooldown_bars:
                return True
        return False

    def _micro_opening_range_quality_allows(self, bar: Bar) -> bool:
        if not self._micro_require_acd_opening_range:
            return True
        if not self._acd_session.opening_complete:
            return False
        width = self._acd_session.width
        if width is None or bar.close == Decimal("0"):
            return False
        range_bps = width / bar.close * _BPS
        return range_bps >= self._micro_min_opening_range_bps

    def _confirmed_direction(self, history: tuple[Bar, ...], score: Decimal) -> bool:
        if self._micro_signal_confirm_bars <= 1:
            return True
        recent = history[-(self._micro_signal_confirm_bars + 1) :]
        for before, after in zip(recent, recent[1:], strict=True):
            change = after.close - before.close
            if score > 0 and change <= 0:
                return False
            if score < 0 and change >= 0:
                return False
        return True

    def _evaluate_acd_entry(self, ctx: StrategyContext, bar: Bar) -> None:
        session = self._acd_session
        session.bar_count += 1
        if session.bar_count <= self._acd_opening_range_bars:
            session.opening_high = (
                bar.high if session.opening_high is None else max(session.opening_high, bar.high)
            )
            session.opening_low = (
                bar.low if session.opening_low is None else min(session.opening_low, bar.low)
            )
            if session.bar_count == self._acd_opening_range_bars:
                session.opening_complete = True
            return
        if not session.opening_complete:
            return
        if (
            session.bar_count > self._acd_max_entry_bars
            or session.entries >= self._acd_max_entries_per_session
        ):
            return
        width = session.width
        if width is None or session.opening_high is None or session.opening_low is None:
            return
        buffer = width * self._acd_entry_buffer_ratio
        breakout_side = 0
        if bar.close > session.opening_high + buffer:
            breakout_side = 1
        elif bar.close < session.opening_low - buffer:
            breakout_side = -1
        if breakout_side == 0:
            return
        side = breakout_side if self._acd_mode == "breakout" else -breakout_side
        if side < 0 and not self._allow_short:
            return
        self._enter(
            ctx,
            side=side,
            price=bar.close,
            source="acd",
            entry_atr=None,
            entry_width=width,
        )
        session.entries += 1

    def _manage_micro_position(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._entry_price is None or self._entry_atr is None:
            return
        self._bars_held += 1
        stop = self._entry_atr * self._micro_stop_atr_multiple
        target = self._entry_atr * self._micro_take_profit_atr_multiple
        if self._side > 0:
            if bar.low <= self._entry_price - stop:
                self._close(ctx, source="microtrend", reason="stop")
            elif bar.high >= self._entry_price + target:
                self._close(ctx, source="microtrend", reason="target")
        else:
            if bar.high >= self._entry_price + stop:
                self._close(ctx, source="microtrend", reason="stop")
            elif bar.low <= self._entry_price - target:
                self._close(ctx, source="microtrend", reason="target")
        if self._source == "microtrend" and self._bars_held >= self._micro_max_holding_bars:
            self._close(ctx, source="microtrend", reason="max_holding")

    def _manage_acd_position(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._entry_price is None or self._entry_width is None:
            return
        self._bars_held += 1
        stop = self._entry_width * self._acd_stop_range_multiple
        target = self._entry_width * self._acd_target_range_multiple
        if self._side > 0:
            if bar.low <= self._entry_price - stop:
                self._close(ctx, source="acd", reason="stop")
            elif bar.high >= self._entry_price + target:
                self._close(ctx, source="acd", reason="target")
        else:
            if bar.high >= self._entry_price + stop:
                self._close(ctx, source="acd", reason="stop")
            elif bar.low <= self._entry_price - target:
                self._close(ctx, source="acd", reason="target")
        if self._source == "acd" and self._bars_held >= self._acd_max_holding_bars:
            self._close(ctx, source="acd", reason="max_holding")

    def _enter(
        self,
        ctx: StrategyContext,
        *,
        side: int,
        price: Decimal,
        source: str,
        entry_atr: Decimal | None,
        entry_width: Decimal | None,
    ) -> None:
        if self._asset is None:
            return
        self._side = side
        self._source = source
        self._entry_price = price
        self._entry_atr = entry_atr
        self._entry_width = entry_width
        self._bars_held = 0
        if source == "microtrend":
            self._micro_session_entries += 1
            self._micro_last_entry_bar_index = self._micro_session_bar_index
        ctx.target_quantity(
            self._asset,
            self._target_quantity * Decimal(side),
            metadata={"source": source, "reason": "entry"},
        )

    def _close(self, ctx: StrategyContext, *, source: str, reason: str) -> None:
        if self._asset is None or self._side == 0:
            return
        ctx.close(self._asset, metadata={"source": source, "reason": reason})
        self._side = 0
        self._source = None
        self._entry_price = None
        self._entry_atr = None
        self._entry_width = None
        self._bars_held = 0
        if source == "microtrend":
            self._micro_last_exit_bar_index = self._micro_session_bar_index


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _return_over_bars(history: tuple[Bar, ...], lookback: int) -> Decimal:
    previous = history[-lookback].close
    if previous == Decimal("0"):
        return Decimal("0")
    return history[-1].close / previous - Decimal("1")


def _volume_ratio(history: tuple[Bar, ...]) -> Decimal:
    if len(history) < 2:
        return Decimal("0")
    previous = history[:-1]
    average = sum((bar.volume for bar in previous), Decimal("0")) / Decimal(len(previous))
    if average == Decimal("0"):
        return Decimal("0")
    return history[-1].volume / average


def _vwap(history: tuple[Bar, ...]) -> Decimal | None:
    volume = sum((bar.volume for bar in history), Decimal("0"))
    if volume == Decimal("0"):
        return None
    return sum((bar.close * bar.volume for bar in history), Decimal("0")) / volume


def _atr(history: tuple[Bar, ...]) -> Decimal:
    if len(history) < 2:
        return Decimal("0")
    ranges: list[Decimal] = []
    for previous, current in zip(history[:-1], history[1:], strict=True):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    if not ranges:
        return Decimal("0")
    return sum(ranges, Decimal("0")) / Decimal(len(ranges))


__all__ = ["PreciousMetalMicrotrendAcdSwitchStrategy"]
