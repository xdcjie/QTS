"""Research-only two-leg ratio mean-reversion strategy."""

from __future__ import annotations

from decimal import Decimal

from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class RatioMeanReversionStrategy(Strategy):
    """Trade two legs from a completed-bar rolling ratio z-score."""

    def __init__(
        self,
        *,
        leg_a_symbol: str = "GC",
        leg_b_symbol: str = "SI",
        timeframe: str = "1d",
        lookback_bars: int = 60,
        entry_z: Decimal = Decimal("1.75"),
        exit_z: Decimal = Decimal("0.25"),
        leg_a_quantity: Decimal = Decimal("1"),
        leg_b_quantity: Decimal = Decimal("2"),
        min_ratio_std: Decimal = Decimal("0.0001"),
    ) -> None:
        normalized_leg_a = str(leg_a_symbol).strip().upper()
        normalized_leg_b = str(leg_b_symbol).strip().upper()
        if not normalized_leg_a or not normalized_leg_b:
            raise ValueError("leg symbols must not be empty")
        if normalized_leg_a == normalized_leg_b:
            raise ValueError("leg symbols must be different")
        if not str(timeframe).strip():
            raise ValueError("timeframe must not be empty")
        if lookback_bars < 3:
            raise ValueError("lookback_bars must be at least 3")
        normalized_entry_z = Decimal(str(entry_z))
        normalized_exit_z = Decimal(str(exit_z))
        normalized_leg_a_quantity = Decimal(str(leg_a_quantity))
        normalized_leg_b_quantity = Decimal(str(leg_b_quantity))
        normalized_min_ratio_std = Decimal(str(min_ratio_std))
        if normalized_entry_z <= Decimal("0"):
            raise ValueError("entry_z must be positive")
        if normalized_exit_z < Decimal("0"):
            raise ValueError("exit_z must be non-negative")
        if normalized_exit_z >= normalized_entry_z:
            raise ValueError("exit_z must be less than entry_z")
        if normalized_leg_a_quantity <= Decimal("0"):
            raise ValueError("leg_a_quantity must be positive")
        if normalized_leg_b_quantity <= Decimal("0"):
            raise ValueError("leg_b_quantity must be positive")
        if normalized_min_ratio_std <= Decimal("0"):
            raise ValueError("min_ratio_std must be positive")

        self._leg_a_symbol = normalized_leg_a
        self._leg_b_symbol = normalized_leg_b
        self._timeframe = str(timeframe)
        self._lookback_bars = lookback_bars
        self._entry_z = normalized_entry_z
        self._exit_z = normalized_exit_z
        self._leg_a_quantity = normalized_leg_a_quantity
        self._leg_b_quantity = normalized_leg_b_quantity
        self._min_ratio_std = normalized_min_ratio_std
        self._leg_a_asset: AssetRef | None = None
        self._leg_b_asset: AssetRef | None = None
        self._position_side = 0
        self._last_decision_time: object | None = None

    def initialize(self, ctx: StrategyContext) -> None:
        self._leg_a_asset = self._asset_for_symbol(ctx, self._leg_a_symbol)
        self._leg_b_asset = self._asset_for_symbol(ctx, self._leg_b_symbol)
        ctx.subscribe(self._leg_a_asset, timeframe=self._timeframe, warmup=self._lookback_bars)
        ctx.subscribe(self._leg_b_asset, timeframe=self._timeframe, warmup=self._lookback_bars)

    def on_bar(self, ctx: StrategyContext, bar: Bar) -> None:
        if self._leg_a_asset is None or self._leg_b_asset is None:
            raise RuntimeError("strategy must be initialized before on_bar")
        if ctx.data is None:
            return
        if bar.instrument_id not in {
            self._leg_a_asset.instrument_id,
            self._leg_b_asset.instrument_id,
        }:
            return
        leg_a_history = ctx.data.history(
            self._leg_a_asset,
            bars=self._lookback_bars,
            timeframe=self._timeframe,
        )
        leg_b_history = ctx.data.history(
            self._leg_b_asset,
            bars=self._lookback_bars,
            timeframe=self._timeframe,
        )
        if len(leg_a_history) < self._lookback_bars or len(leg_b_history) < self._lookback_bars:
            return
        aligned_histories = self._aligned_histories(leg_a_history, leg_b_history)
        if aligned_histories is None:
            return
        leg_a_history, leg_b_history = aligned_histories
        decision_time = leg_a_history[-1].end_time
        if decision_time == self._last_decision_time:
            return
        self._last_decision_time = decision_time

        side = self._side_for_histories(leg_a_history, leg_b_history)
        if side == self._position_side:
            return
        if side == 0:
            self._close_pair(ctx)
        else:
            self._target_pair(ctx, side)
        self._position_side = side

    @staticmethod
    def _aligned_histories(
        leg_a_history: tuple[Bar, ...],
        leg_b_history: tuple[Bar, ...],
    ) -> tuple[tuple[Bar, ...], tuple[Bar, ...]] | None:
        leg_a_times = tuple(item.end_time for item in leg_a_history)
        leg_b_times = tuple(item.end_time for item in leg_b_history)
        if leg_a_times != leg_b_times:
            return None
        return leg_a_history, leg_b_history

    def _side_for_histories(
        self,
        leg_a_history: tuple[Bar, ...],
        leg_b_history: tuple[Bar, ...],
    ) -> int:
        ratios: list[Decimal] = []
        for leg_a_bar, leg_b_bar in zip(leg_a_history, leg_b_history, strict=True):
            if leg_b_bar.close <= Decimal("0"):
                return 0
            ratios.append(leg_a_bar.close / leg_b_bar.close)
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
        if self._leg_a_asset is None or self._leg_b_asset is None:
            raise RuntimeError("strategy must be initialized before targeting")
        multiplier = Decimal(side)
        ctx.target_quantity(self._leg_a_asset, multiplier * self._leg_a_quantity)
        ctx.target_quantity(self._leg_b_asset, -multiplier * self._leg_b_quantity)

    def _close_pair(self, ctx: StrategyContext) -> None:
        if self._leg_a_asset is None or self._leg_b_asset is None:
            raise RuntimeError("strategy must be initialized before closing")
        ctx.close(self._leg_a_asset)
        ctx.close(self._leg_b_asset)

    @staticmethod
    def _asset_for_symbol(ctx: StrategyContext, symbol: str) -> AssetRef:
        try:
            return ctx.future(symbol)
        except (KeyError, RuntimeError):
            return ctx.symbol(symbol)


__all__ = ["RatioMeanReversionStrategy"]
