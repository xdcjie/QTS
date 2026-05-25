from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from types import SimpleNamespace
from typing import cast

from qts.core.ids import InstrumentId
from qts.strategy_sdk import AssetRef, StrategyContext


class FakeDataView:
    def __init__(self, closes: tuple[str, ...]) -> None:
        self._closes = closes

    def set_closes(self, closes: tuple[str, ...]) -> None:
        self._closes = closes

    def history(
        self,
        asset: AssetRef,
        *,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[SimpleNamespace, ...]:
        _ = asset, timeframe
        return tuple(SimpleNamespace(close=Decimal(value)) for value in self._closes[-bars:])


@dataclass
class FakeContext:
    data: FakeDataView

    def __post_init__(self) -> None:
        self.asset = AssetRef(InstrumentId("FUTURE.CME.GC.GCG6"), "GC")
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []
        self.subscriptions: list[tuple[AssetRef, str, int]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol != "GC":
            raise KeyError(symbol)
        return self.asset

    def symbol(self, symbol: str) -> AssetRef:
        return AssetRef(self.asset.instrument_id, symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> None:
        self.intents.append(("target_quantity", asset, quantity))

    def close(self, asset: AssetRef) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def test_momentum_strategy_suppresses_duplicate_targets_for_unchanged_signal() -> None:
    from examples.strategies.gc_si_momentum import GcSiMomentumStrategy

    ctx = FakeContext(FakeDataView(("100", "101")))
    strategy = GcSiMomentumStrategy(symbols=("GC",), short_window=1, long_window=2)
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), object())
    strategy.on_bar(_ctx(ctx), object())

    assert ctx.intents == [("target_quantity", ctx.asset, Decimal("1"))]


def test_momentum_strategy_closes_once_when_signal_turns_flat() -> None:
    from examples.strategies.gc_si_momentum import GcSiMomentumStrategy

    data = FakeDataView(("100", "101"))
    ctx = FakeContext(data)
    strategy = GcSiMomentumStrategy(symbols=("GC",), short_window=1, long_window=2)
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), object())

    data.set_closes(("101", "100"))
    strategy.on_bar(_ctx(ctx), object())
    strategy.on_bar(_ctx(ctx), object())

    assert ctx.intents == [
        ("target_quantity", ctx.asset, Decimal("1")),
        ("close", ctx.asset, None),
    ]
