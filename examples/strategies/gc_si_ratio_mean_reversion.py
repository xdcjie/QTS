"""GC/SI daily ratio mean-reversion example."""

from __future__ import annotations

from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class GcSiRatioMeanReversionStrategy(Strategy):
    """Trade GC and SI legs from a completed-bar rolling ratio z-score."""

    def __init__(
        self,
        *,
        gc_symbol: str = "GC",
        si_symbol: str = "SI",
        timeframe: str = "1d",
        lookback_bars: int = 60,
        entry_z: Decimal = Decimal("1.5"),
        exit_z: Decimal = Decimal("0.25"),
        gc_contracts: Decimal = Decimal("1"),
        si_contracts: Decimal = Decimal("2"),
        min_ratio_std: Decimal = Decimal("0.0001"),
    ) -> None:
        if lookback_bars < 3:
            raise ValueError("lookback_bars must be at least 3")
        normalized_entry_z = Decimal(str(entry_z))
        normalized_exit_z = Decimal(str(exit_z))
        normalized_gc_contracts = Decimal(str(gc_contracts))
        normalized_si_contracts = Decimal(str(si_contracts))
        normalized_min_ratio_std = Decimal(str(min_ratio_std))
        if normalized_entry_z <= Decimal("0"):
            raise ValueError("entry_z must be positive")
        if normalized_exit_z < Decimal("0"):
            raise ValueError("exit_z must be non-negative")
        if normalized_exit_z >= normalized_entry_z:
            raise ValueError("exit_z must be less than entry_z")
        if normalized_gc_contracts <= Decimal("0"):
            raise ValueError("gc_contracts must be positive")
        if normalized_si_contracts <= Decimal("0"):
            raise ValueError("si_contracts must be positive")
        if normalized_gc_contracts != normalized_gc_contracts.to_integral_value():
            raise ValueError("gc_contracts must be an integer quantity")
        if normalized_si_contracts != normalized_si_contracts.to_integral_value():
            raise ValueError("si_contracts must be an integer quantity")
        if normalized_min_ratio_std <= Decimal("0"):
            raise ValueError("min_ratio_std must be positive")

        self._gc_symbol = gc_symbol
        self._si_symbol = si_symbol
        self._timeframe = timeframe
        self._lookback_bars = lookback_bars
        self._entry_z = normalized_entry_z
        self._exit_z = normalized_exit_z
        self._gc_contracts = normalized_gc_contracts
        self._si_contracts = normalized_si_contracts
        self._min_ratio_std = normalized_min_ratio_std
        self._gc_asset: AssetRef | None = None
        self._si_asset: AssetRef | None = None
        self._position_side = 0
        self._last_decision_time: object | None = None

    def initialize(self, ctx: StrategyContext) -> None:
        self._gc_asset = self._asset_for_symbol(ctx, self._gc_symbol)
        self._si_asset = self._asset_for_symbol(ctx, self._si_symbol)
        ctx.subscribe(self._gc_asset, timeframe=self._timeframe, warmup=self._lookback_bars)
        ctx.subscribe(self._si_asset, timeframe=self._timeframe, warmup=self._lookback_bars)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._gc_asset is None or self._si_asset is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        if ctx.data is None:
            return
        if bar.instrument_id not in {self._gc_asset.instrument_id, self._si_asset.instrument_id}:
            return
        gc_history = ctx.data.history(
            self._gc_asset,
            bars=self._lookback_bars,
            timeframe=self._timeframe,
        )
        si_history = ctx.data.history(
            self._si_asset,
            bars=self._lookback_bars,
            timeframe=self._timeframe,
        )
        if len(gc_history) < self._lookback_bars or len(si_history) < self._lookback_bars:
            return
        aligned_histories = self._aligned_histories(gc_history, si_history)
        if aligned_histories is None:
            return
        gc_history, si_history = aligned_histories
        decision_time = gc_history[-1].end_time
        if decision_time == self._last_decision_time:
            return
        self._last_decision_time = decision_time

        side = self._side_for_histories(gc_history, si_history)
        if side == self._position_side:
            return
        if side == 0:
            self._close_pair(ctx)
        else:
            self._target_pair(ctx, side)
        self._position_side = side

    def _aligned_histories(
        self, gc_history: tuple[Bar, ...], si_history: tuple[Bar, ...]
    ) -> tuple[tuple[Bar, ...], tuple[Bar, ...]] | None:
        gc_times = tuple(item.end_time for item in gc_history)
        si_times = tuple(item.end_time for item in si_history)
        if gc_times != si_times:
            return None
        return gc_history, si_history

    def _side_for_histories(self, gc_history: tuple[Bar, ...], si_history: tuple[Bar, ...]) -> int:
        ratios: list[Decimal] = []
        for gc_bar, si_bar in zip(gc_history, si_history, strict=True):
            if si_bar.close <= Decimal("0"):
                return 0
            ratios.append(gc_bar.close / si_bar.close)
        mean = sum(ratios, Decimal("0")) / Decimal(len(ratios))
        variance = sum((ratio - mean) ** 2 for ratio in ratios) / Decimal(len(ratios))
        std = variance.sqrt()
        z_score = Decimal("0") if std < self._min_ratio_std else (ratios[-1] - mean) / std
        if z_score >= self._entry_z:
            return -1
        if z_score <= -self._entry_z:
            return 1
        if self._position_side != 0 and abs(z_score) <= self._exit_z:
            return 0
        return self._position_side

    def _target_pair(self, ctx: StrategyContext, side: int) -> None:
        if self._gc_asset is None or self._si_asset is None:
            raise RuntimeError("strategy must be initialized before targeting")
        multiplier = Decimal(side)
        ctx.target_quantity(self._gc_asset, multiplier * self._gc_contracts)
        ctx.target_quantity(self._si_asset, -multiplier * self._si_contracts)

    def _close_pair(self, ctx: StrategyContext) -> None:
        if self._gc_asset is None or self._si_asset is None:
            raise RuntimeError("strategy must be initialized before closing")
        ctx.close(self._gc_asset)
        ctx.close(self._si_asset)

    def _asset_for_symbol(self, ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


__all__ = ["GcSiRatioMeanReversionStrategy"]
