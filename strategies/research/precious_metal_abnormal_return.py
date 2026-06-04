"""Research-only abnormal-return continuation/reversal strategy."""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


@dataclass(slots=True)
class _AbnormalReturnState:
    side: int = 0
    bars_held: int = 0
    last_decision_time: object | None = None


class PreciousMetalAbnormalReturnStrategy(Strategy):
    """Trade short-horizon response after completed-bar abnormal returns."""

    def __init__(
        self,
        *,
        symbols: Sequence[str] = ("GC", "SI"),
        timeframe: str = "1d",
        lookback_bars: int = 60,
        entry_z: Decimal = Decimal("1.50"),
        mode: str = "momentum",
        holding_bars: int = 3,
        target_quantity: Decimal = Decimal("1"),
        allow_short: bool = True,
        min_return_std: Decimal = Decimal("0.0001"),
        history_buffer_bars: int = 2,
    ) -> None:
        normalized_symbols = tuple(str(symbol).strip().upper() for symbol in symbols)
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("symbols must not be empty")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("symbols must be unique")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        if lookback_bars < 3:
            raise ValueError("lookback_bars must be at least 3")
        normalized_mode = str(mode).strip().lower()
        if normalized_mode not in {"momentum", "reversal"}:
            raise ValueError("mode must be 'momentum' or 'reversal'")
        if holding_bars <= 0:
            raise ValueError("holding_bars must be positive")
        if history_buffer_bars < 0:
            raise ValueError("history_buffer_bars must be non-negative")

        self._symbols = normalized_symbols
        self._timeframe = str(timeframe)
        self._lookback_bars = lookback_bars
        self._entry_z = _decimal(entry_z)
        self._mode = normalized_mode
        self._holding_bars = holding_bars
        self._target_quantity = _decimal(target_quantity)
        self._allow_short = allow_short
        self._min_return_std = _decimal(min_return_std)
        self._history_buffer_bars = history_buffer_bars
        for name, value in {
            "entry_z": self._entry_z,
            "target_quantity": self._target_quantity,
            "min_return_std": self._min_return_std,
        }.items():
            if value < Decimal("0"):
                raise ValueError(f"{name} must be non-negative")
        if self._entry_z == Decimal("0"):
            raise ValueError("entry_z must be positive")
        if self._target_quantity == Decimal("0"):
            raise ValueError("target_quantity must be non-zero")
        if self._min_return_std == Decimal("0"):
            raise ValueError("min_return_std must be positive")

        self._assets: dict[str, AssetRef] = {}
        self._instrument_to_symbol: dict[object, str] = {}
        self._state_by_symbol = {symbol: _AbnormalReturnState() for symbol in normalized_symbols}

    @property
    def _required_history(self) -> int:
        return self._lookback_bars + 1

    def initialize(self, ctx: StrategyContext) -> None:
        for symbol in self._symbols:
            asset = _asset_for_symbol(ctx, symbol)
            self._assets[symbol] = asset
            self._instrument_to_symbol[asset.instrument_id] = symbol
            ctx.subscribe(
                asset,
                timeframe=self._timeframe,
                warmup=self._required_history + self._history_buffer_bars,
            )

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        symbol = self._instrument_to_symbol.get(bar.instrument_id)
        if symbol is None or ctx.data is None:
            return
        if bar.end_time == self._state_by_symbol[symbol].last_decision_time:
            return
        state = self._state_by_symbol[symbol]
        state.last_decision_time = bar.end_time
        if state.side != 0:
            state.bars_held += 1
            if state.bars_held >= self._holding_bars:
                ctx.close(
                    self._assets[symbol],
                    metadata={"reason": "abnormal_return_exit", "symbol": symbol},
                )
                state.side = 0
                state.bars_held = 0
            return

        history = ctx.data.history(
            self._assets[symbol],
            bars=self._required_history,
            timeframe=self._timeframe,
        )
        if len(history) < self._required_history:
            return
        side = self._entry_side(history)
        if side == 0:
            return
        if side < 0 and not self._allow_short:
            return
        ctx.target_quantity(
            self._assets[symbol],
            Decimal(side) * self._target_quantity,
            metadata={"reason": "abnormal_return_entry", "symbol": symbol},
        )
        state.side = side
        state.bars_held = 0

    def _entry_side(self, history: tuple[Bar, ...]) -> int:
        returns = _returns(history)
        if len(returns) < self._lookback_bars:
            return 0
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((item - mean) ** 2 for item in returns) / Decimal(len(returns))
        std = variance.sqrt()
        if std < self._min_return_std:
            return 0
        z_score = (returns[-1] - mean) / std
        if abs(z_score) < self._entry_z:
            return 0
        raw_side = 1 if z_score > Decimal("0") else -1
        return raw_side if self._mode == "momentum" else -raw_side


def _returns(history: tuple[Bar, ...]) -> tuple[Decimal, ...]:
    values: list[Decimal] = []
    for previous, current in itertools.pairwise(history):
        if previous.close <= Decimal("0"):
            return ()
        values.append(current.close / previous.close - Decimal("1"))
    return tuple(values)


def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
    try:
        return ctx.future(symbol)
    except (KeyError, RuntimeError):
        return ctx.symbol(symbol)


def _decimal(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value))


__all__ = ["PreciousMetalAbnormalReturnStrategy"]
