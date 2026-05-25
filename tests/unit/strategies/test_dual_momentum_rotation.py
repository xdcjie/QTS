from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar
from qts.strategy_sdk import AssetRef, PortfolioView, StrategyContext

GC_ID = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
SI_ID = InstrumentId("CONTINUOUS_FUTURE.CME.SI")


class FakeDataView:
    def __init__(self, closes_by_symbol: dict[str, tuple[str, ...]]) -> None:
        self._closes_by_symbol = closes_by_symbol
        self._start_offset_days = 0

    def set_closes(self, closes_by_symbol: dict[str, tuple[str, ...]]) -> None:
        self._closes_by_symbol = closes_by_symbol
        self._start_offset_days += 1

    def history(
        self,
        asset: AssetRef,
        *,
        bars: int,
        timeframe: str | None = None,
    ) -> tuple[Bar, ...]:
        _ = timeframe
        if asset.instrument_id == GC_ID:
            return _bars(GC_ID, self._closes_by_symbol["GC"][-bars:], self._start_offset_days)
        if asset.instrument_id == SI_ID:
            return _bars(SI_ID, self._closes_by_symbol["SI"][-bars:], self._start_offset_days)
        return ()


@dataclass
class FakeContext:
    data: FakeDataView
    portfolio: PortfolioView | None = None

    def __post_init__(self) -> None:
        self.gc_asset = AssetRef(GC_ID, "GC")
        self.si_asset = AssetRef(SI_ID, "SI")
        self.intents: list[tuple[str, AssetRef, Decimal | None]] = []
        self.subscriptions: list[tuple[AssetRef, str, int]] = []

    def future(self, symbol: str) -> AssetRef:
        if symbol == "GC":
            return self.gc_asset
        if symbol == "SI":
            return self.si_asset
        raise KeyError(symbol)

    def symbol(self, symbol: str) -> AssetRef:
        return AssetRef(InstrumentId(f"RESEARCH.TEST.{symbol}"), symbol)

    def subscribe(self, asset: AssetRef, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset, timeframe, warmup))

    def target_quantity(self, asset: AssetRef, quantity: Decimal) -> None:
        self.intents.append(("target_quantity", asset, quantity))

    def close(self, asset: AssetRef) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bars(
    instrument_id: InstrumentId,
    closes: tuple[str, ...],
    start_offset_days: int = 0,
) -> tuple[Bar, ...]:
    start = datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=start_offset_days)
    output: list[Bar] = []
    for index, close_text in enumerate(closes):
        close = Decimal(close_text)
        output.append(
            Bar(
                instrument_id=instrument_id,
                start_time=start + timedelta(days=index),
                end_time=start + timedelta(days=index + 1),
                timeframe="1d",
                session_id=(start + timedelta(days=index)).date().isoformat(),
                open=close,
                high=close,
                low=close,
                close=close,
                volume=Decimal("100"),
                is_complete=True,
            )
        )
    return tuple(output)


def _bar(instrument_id: InstrumentId = GC_ID) -> Bar:
    return _bars(instrument_id, ("100", "102", "106"))[-1]


def test_dual_momentum_rotation_subscribes_to_all_trade_assets() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    ctx = FakeContext(FakeDataView({"GC": ("100", "101", "102"), "SI": ("20", "21", "22")}))
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        history_buffer_bars=3,
    )

    strategy.initialize(_ctx(ctx))

    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 6),
        (ctx.si_asset, "1d", 6),
    ]


def test_dual_momentum_rotation_targets_only_strongest_positive_asset() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    ctx = FakeContext(FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")}))
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        min_absolute_momentum=Decimal("0.02"),
        min_relative_momentum=Decimal("0.05"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [("target_quantity", ctx.gc_asset, Decimal("1"))]


def test_dual_momentum_rotation_can_average_multiple_lookback_horizons() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    ctx = FakeContext(
        FakeDataView(
            {
                "GC": ("100", "112", "113", "114", "115"),
                "SI": ("100", "100", "100", "108", "116"),
            }
        )
    )
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=(2, 4),
        rebalance_bars=1,
        min_absolute_momentum=Decimal("0.02"),
        min_relative_momentum=Decimal("0.01"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 5),
        (ctx.si_asset, "1d", 5),
    ]
    assert ctx.intents == [("target_quantity", ctx.si_asset, Decimal("1"))]


def test_dual_momentum_rotation_closes_old_winner_before_rotating() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data)
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=1,
        min_relative_momentum=Decimal("0.05"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("106", "106", "105"), "SI": ("19", "20", "22")})
    strategy.on_bar(_ctx(ctx), _bar(SI_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("1")),
        ("close", ctx.gc_asset, None),
        ("target_quantity", ctx.si_asset, Decimal("1")),
    ]


def test_dual_momentum_rotation_moves_to_cash_when_no_asset_passes_thresholds() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data)
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=1,
        min_absolute_momentum=Decimal("0.02"),
        min_relative_momentum=Decimal("0.05"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("106", "106", "106"), "SI": ("19", "19", "19")})
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("1")),
        ("close", ctx.gc_asset, None),
    ]


def test_dual_momentum_rotation_waits_for_rebalance_interval() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data)
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=2,
        min_relative_momentum=Decimal("0.05"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("106", "106", "105"), "SI": ("19", "20", "22")})
    strategy.on_bar(_ctx(ctx), _bar(SI_ID))
    assert ctx.intents == [("target_quantity", ctx.gc_asset, Decimal("1"))]

    data.set_closes({"GC": ("106", "105", "104"), "SI": ("20", "22", "24")})
    strategy.on_bar(_ctx(ctx), _bar(SI_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("1")),
        ("close", ctx.gc_asset, None),
        ("target_quantity", ctx.si_asset, Decimal("1")),
    ]


def test_dual_momentum_rotation_requires_confirmation_in_high_volatility() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data)
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=1,
        volatility_lookback_bars=2,
        high_volatility_threshold=Decimal("0.01"),
        high_volatility_confirmation_bars=2,
        min_relative_momentum=Decimal("0.05"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))
    assert ctx.intents == []

    data.set_closes({"GC": ("102", "106", "110"), "SI": ("20", "19", "18")})
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [("target_quantity", ctx.gc_asset, Decimal("1"))]


def test_dual_momentum_rotation_low_volatility_signal_does_not_wait_for_high_vol_confirmation() -> (
    None
):
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data)
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=1,
        volatility_lookback_bars=2,
        high_volatility_threshold=Decimal("1.00"),
        high_volatility_confirmation_bars=3,
        min_relative_momentum=Decimal("0.05"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [("target_quantity", ctx.gc_asset, Decimal("1"))]


def test_dual_momentum_rotation_closes_when_portfolio_drawdown_breaches_gate() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data, portfolio=PortfolioView(cash=Decimal("0"), equity=Decimal("100000")))
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=1,
        min_relative_momentum=Decimal("0.05"),
        max_drawdown_fraction=Decimal("0.15"),
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("102", "106", "110"), "SI": ("20", "19", "18")})
    ctx.portfolio = PortfolioView(cash=Decimal("0"), equity=Decimal("84000"))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("1")),
        ("close", ctx.gc_asset, None),
    ]


def test_dual_momentum_rotation_waits_for_drawdown_cooldown_before_reentering() -> None:
    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    data = FakeDataView({"GC": ("100", "102", "106"), "SI": ("20", "20", "19")})
    ctx = FakeContext(data, portfolio=PortfolioView(cash=Decimal("0"), equity=Decimal("100000")))
    strategy = DualMomentumRotationStrategy(
        symbols=("GC", "SI"),
        lookback_bars=2,
        rebalance_bars=1,
        min_relative_momentum=Decimal("0.05"),
        max_drawdown_fraction=Decimal("0.15"),
        drawdown_cooldown_bars=1,
        target_quantities={"GC": "1", "SI": "1"},
        history_buffer_bars=0,
    )
    strategy.initialize(_ctx(ctx))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("102", "106", "110"), "SI": ("20", "19", "18")})
    ctx.portfolio = PortfolioView(cash=Decimal("0"), equity=Decimal("84000"))
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("106", "110", "114"), "SI": ("19", "18", "17")})
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    data.set_closes({"GC": ("110", "114", "118"), "SI": ("18", "17", "16")})
    strategy.on_bar(_ctx(ctx), _bar(GC_ID))

    assert ctx.intents == [
        ("target_quantity", ctx.gc_asset, Decimal("1")),
        ("close", ctx.gc_asset, None),
        ("target_quantity", ctx.gc_asset, Decimal("1")),
    ]


def test_backtest_loader_can_instantiate_dual_momentum_rotation_with_yaml_params() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.dual_momentum_rotation:DualMomentumRotationStrategy",
        {
            "symbols": ["GC", "SI"],
            "timeframe": "1d",
            "lookback_bars": 63,
            "rebalance_bars": 21,
            "min_absolute_momentum": "0",
            "min_relative_momentum": "0.05",
            "volatility_lookback_bars": 40,
            "high_volatility_threshold": "0.25",
            "high_volatility_confirmation_bars": 2,
            "max_drawdown_fraction": "0.20",
            "drawdown_cooldown_bars": 21,
            "target_quantities": {"GC": "1", "SI": "1"},
            "history_buffer_bars": 10,
        },
    )
    ctx = FakeContext(FakeDataView({"GC": ("100", "101", "102"), "SI": ("20", "21", "22")}))

    strategy.initialize(_ctx(ctx))

    assert isinstance(strategy, DualMomentumRotationStrategy)
    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 74),
        (ctx.si_asset, "1d", 74),
    ]


def test_backtest_loader_can_instantiate_dual_momentum_rotation_with_multi_horizon_yaml() -> None:
    from qts.backtest.pipeline import BacktestPipeline

    from examples.strategies.dual_momentum_rotation import DualMomentumRotationStrategy

    strategy = BacktestPipeline.load_strategy(
        "examples.strategies.dual_momentum_rotation:DualMomentumRotationStrategy",
        {
            "symbols": ["GC", "SI"],
            "timeframe": "1d",
            "lookback_bars": [21, 63, 126],
            "rebalance_bars": 1,
            "min_absolute_momentum": "0.02",
            "min_relative_momentum": "0.05",
            "target_quantities": {"GC": "1", "SI": "1"},
            "history_buffer_bars": 10,
        },
    )
    ctx = FakeContext(FakeDataView({"GC": ("100", "101", "102"), "SI": ("20", "21", "22")}))

    strategy.initialize(_ctx(ctx))

    assert isinstance(strategy, DualMomentumRotationStrategy)
    assert ctx.subscriptions == [
        (ctx.gc_asset, "1d", 137),
        (ctx.si_asset, "1d", 137),
    ]
