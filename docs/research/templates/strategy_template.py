"""Template for wiring a reviewed factor through the Strategy SDK."""

from __future__ import annotations

from qts.strategy_sdk import AssetRef, Strategy, StrategyContext


class ReviewedFactorStrategyTemplate(Strategy):
    """Strategy SDK sketch for reviewed factor implementation."""

    def on_bar(self, ctx: StrategyContext) -> None:
        asset = AssetRef("GC")
        signal = ctx.data.factor("replace_with_reviewed_factor_name", asset)
        if signal > 0:
            ctx.target_percent(asset, 0.10)
        else:
            ctx.close(asset)
