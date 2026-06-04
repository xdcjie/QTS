"""UTC time-window seasonal strategy for precious-metal futures."""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


@dataclass(slots=True)
class _WindowState:
    invested: bool = False
    last_decision_time: object | None = None
    last_regime_key: object | None = None
    last_regime_allowed: bool | None = None
    recent_closes: list[Decimal] = field(default_factory=list)
    entry_price: Decimal | None = None
    high_watermark: Decimal | None = None


class PreciousMetalUtcWindowStrategy(Strategy):
    """Hold configured symbols only during a fixed UTC hour window."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC", "SI"),
        timeframe: str = "1m",
        start_hour_utc: int = 20,
        duration_hours: int = 6,
        target_quantities: Mapping[str, Decimal | str | int] | None = None,
        regime_timeframe: str = "1d",
        regime_lookback_bars: int = 0,
        min_regime_return: Decimal = Decimal("0"),
        realized_vol_lookback_bars: int = 0,
        min_realized_vol: Decimal = Decimal("0"),
        max_realized_vol: Decimal | None = None,
        atr_lookback_bars: int = 0,
        stop_atr_multiple: Decimal = Decimal("0"),
        trailing_atr_multiple: Decimal = Decimal("0"),
        allowed_weekdays: Iterable[int] | None = None,
        allowed_month_days: Iterable[int] | None = None,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        if start_hour_utc < 0 or start_hour_utc > 23:
            raise ValueError("start_hour_utc must be between 0 and 23")
        if duration_hours <= 0 or duration_hours > 24:
            raise ValueError("duration_hours must be in 1..24")
        normalized_weekdays = (
            None if allowed_weekdays is None else tuple(int(day) for day in allowed_weekdays)
        )
        if normalized_weekdays is not None and (
            not normalized_weekdays or any(day < 0 or day > 6 for day in normalized_weekdays)
        ):
            raise ValueError("allowed_weekdays must contain integers in 0..6")
        normalized_month_days = (
            None if allowed_month_days is None else tuple(int(day) for day in allowed_month_days)
        )
        if normalized_month_days is not None and (
            not normalized_month_days or any(day < 1 or day > 31 for day in normalized_month_days)
        ):
            raise ValueError("allowed_month_days must contain integers in 1..31")
        if not str(regime_timeframe).strip():
            raise ValueError("regime_timeframe must not be empty")
        if regime_lookback_bars < 0:
            raise ValueError("regime_lookback_bars must be non-negative")
        if regime_lookback_bars > 0 and str(regime_timeframe) != str(timeframe):
            raise ValueError("regime_timeframe must match timeframe when regime is enabled")
        if realized_vol_lookback_bars < 0:
            raise ValueError("realized_vol_lookback_bars must be non-negative")
        if atr_lookback_bars < 0:
            raise ValueError("atr_lookback_bars must be non-negative")
        raw_quantities = target_quantities or {
            symbol: Decimal("1") for symbol in normalized_symbols
        }
        quantities = {
            str(symbol).strip().upper(): _decimal(quantity)
            for symbol, quantity in raw_quantities.items()
        }
        missing = [symbol for symbol in normalized_symbols if symbol not in quantities]
        if missing:
            raise ValueError("target_quantities must contain every symbol")
        if any(quantities[symbol] <= Decimal("0") for symbol in normalized_symbols):
            raise ValueError("target quantities must be positive")

        self._symbols = normalized_symbols
        self._timeframe = str(timeframe)
        self._start_hour_utc = start_hour_utc
        self._duration_hours = duration_hours
        self._target_quantities = quantities
        self._regime_timeframe = str(regime_timeframe)
        self._regime_lookback_bars = regime_lookback_bars
        self._min_regime_return = _decimal(min_regime_return)
        self._realized_vol_lookback_bars = realized_vol_lookback_bars
        self._min_realized_vol = _decimal(min_realized_vol)
        self._max_realized_vol = None if max_realized_vol is None else _decimal(max_realized_vol)
        self._atr_lookback_bars = atr_lookback_bars
        self._stop_atr_multiple = _decimal(stop_atr_multiple)
        self._trailing_atr_multiple = _decimal(trailing_atr_multiple)
        self._allowed_weekdays = (
            None if normalized_weekdays is None else frozenset(normalized_weekdays)
        )
        self._allowed_month_days = (
            None if normalized_month_days is None else frozenset(normalized_month_days)
        )
        self._recent_close_limit = max(1, self._realized_vol_lookback_bars + 1)
        if self._min_realized_vol < Decimal("0"):
            raise ValueError("min_realized_vol must be non-negative")
        if self._max_realized_vol is not None and self._max_realized_vol < Decimal("0"):
            raise ValueError("max_realized_vol must be non-negative")
        if self._max_realized_vol is not None and self._min_realized_vol > self._max_realized_vol:
            raise ValueError("min_realized_vol must be <= max_realized_vol")
        if self._stop_atr_multiple < Decimal("0"):
            raise ValueError("stop_atr_multiple must be non-negative")
        if self._trailing_atr_multiple < Decimal("0"):
            raise ValueError("trailing_atr_multiple must be non-negative")
        if (
            self._stop_atr_multiple > Decimal("0") or self._trailing_atr_multiple > Decimal("0")
        ) and self._atr_lookback_bars == 0:
            raise ValueError("atr_lookback_bars must be positive when ATR stops are enabled")
        self._assets: dict[str, AssetRef] = {}
        self._instrument_to_symbol: dict[object, str] = {}
        self._state_by_symbol = {symbol: _WindowState() for symbol in normalized_symbols}

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            asset = _asset_for_symbol(ctx, symbol)
            self._assets[symbol] = asset
            self._instrument_to_symbol[asset.instrument_id] = symbol
            warmup = max(
                1,
                self._regime_lookback_bars + 1,
                self._realized_vol_lookback_bars + 1,
                self._atr_lookback_bars + 1,
            )
            ctx.subscribe(asset, timeframe=self._timeframe, warmup=warmup)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        symbol = self._instrument_to_symbol.get(bar.instrument_id)
        if symbol is None:
            return
        if bar.timeframe != self._timeframe:
            return
        state = self._state_by_symbol[symbol]
        state.recent_closes.append(bar.close)
        if len(state.recent_closes) > self._recent_close_limit:
            del state.recent_closes[: len(state.recent_closes) - self._recent_close_limit]
        if state.last_decision_time == bar.end_time:
            return
        state.last_decision_time = bar.end_time
        if state.invested and self._atr_exit_triggered(ctx, symbol, state, bar):
            ctx.close(
                self._assets[symbol],
                metadata={"reason": "utc_window_atr_exit", "symbol": symbol},
            )
            state.invested = False
            state.entry_price = None
            state.high_watermark = None
            return
        in_window = self._in_window(bar.end_time)
        should_hold = (
            in_window
            and self._weekday_allows(bar.end_time)
            and self._month_day_allows(bar.end_time)
            and self._regime_allows(ctx, symbol, state, bar.end_time)
            and self._realized_vol_allows(state)
        )
        if should_hold and not state.invested:
            ctx.target_quantity(
                self._assets[symbol],
                self._target_quantities[symbol],
                metadata={"reason": "utc_window_entry", "symbol": symbol},
            )
            state.invested = True
            state.entry_price = bar.close
            state.high_watermark = bar.high
        elif not should_hold and state.invested:
            ctx.close(
                self._assets[symbol],
                metadata={"reason": "utc_window_exit", "symbol": symbol},
            )
            state.invested = False
            state.entry_price = None
            state.high_watermark = None

    def _in_window(self, end_time: object) -> bool:
        hour = getattr(end_time, "hour", None)
        if not isinstance(hour, int):
            return False
        elapsed = (hour - self._start_hour_utc) % 24
        return elapsed < self._duration_hours

    def _weekday_allows(self, end_time: object) -> bool:
        if self._allowed_weekdays is None:
            return True
        weekday_method = getattr(end_time, "weekday", None)
        if not callable(weekday_method):
            return False
        return int(weekday_method()) in self._allowed_weekdays

    def _month_day_allows(self, end_time: object) -> bool:
        if self._allowed_month_days is None:
            return True
        day = getattr(end_time, "day", None)
        if not isinstance(day, int):
            return False
        return day in self._allowed_month_days

    def _regime_allows(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _WindowState,
        end_time: object,
    ) -> bool:
        if self._regime_lookback_bars == 0:
            return True
        date_method = getattr(end_time, "date", None)
        regime_key = date_method() if callable(date_method) else end_time
        if state.last_regime_key == regime_key and state.last_regime_allowed is not None:
            return state.last_regime_allowed
        if ctx.data is None:
            return False
        history = ctx.data.history(
            self._assets[symbol],
            bars=self._regime_lookback_bars + 1,
            timeframe=self._regime_timeframe,
        )
        if len(history) < self._regime_lookback_bars + 1:
            return False
        previous = history[0].close
        latest = history[-1].close
        if previous <= Decimal("0"):
            return False
        allowed = latest / previous - Decimal("1") >= self._min_regime_return
        state.last_regime_key = regime_key
        state.last_regime_allowed = allowed
        return allowed

    def _realized_vol_allows(self, state: _WindowState) -> bool:
        if self._realized_vol_lookback_bars == 0:
            return True
        if len(state.recent_closes) < self._realized_vol_lookback_bars + 1:
            return False
        returns: list[Decimal] = []
        for previous, current in zip(state.recent_closes, state.recent_closes[1:], strict=False):
            if previous <= Decimal("0"):
                return False
            returns.append(current / previous - Decimal("1"))
        if not returns:
            return False
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((item - mean) ** 2 for item in returns) / Decimal(len(returns))
        realized_vol = variance.sqrt()
        if realized_vol < self._min_realized_vol:
            return False
        return not (self._max_realized_vol is not None and realized_vol >= self._max_realized_vol)

    def _atr_exit_triggered(
        self,
        ctx: StrategyContext,
        symbol: str,
        state: _WindowState,
        bar: Bar,
    ) -> bool:
        if self._stop_atr_multiple == Decimal("0") and self._trailing_atr_multiple == Decimal("0"):
            return False
        if ctx.data is None or state.entry_price is None:
            return False
        history = ctx.data.history(
            self._assets[symbol],
            bars=self._atr_lookback_bars + 1,
            timeframe=self._timeframe,
        )
        if len(history) < self._atr_lookback_bars + 1:
            return False
        atr = self._atr(history)
        if atr <= Decimal("0"):
            return False
        state.high_watermark = (
            bar.high if state.high_watermark is None else max(state.high_watermark, bar.high)
        )
        stop_price: Decimal | None = None
        if self._stop_atr_multiple > Decimal("0"):
            stop_price = state.entry_price - self._stop_atr_multiple * atr
        if self._trailing_atr_multiple > Decimal("0") and state.high_watermark is not None:
            trailing_price = state.high_watermark - self._trailing_atr_multiple * atr
            stop_price = trailing_price if stop_price is None else max(stop_price, trailing_price)
        return stop_price is not None and bar.close <= stop_price

    @staticmethod
    def _atr(history: tuple[Bar, ...]) -> Decimal:
        ranges: list[Decimal] = []
        for previous, current in itertools.pairwise(history):
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


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


__all__ = ["PreciousMetalUtcWindowStrategy"]
