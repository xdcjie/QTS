from __future__ import annotations

import ast
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from qts.domain.market_data import Bar
from qts.strategy_sdk import Strategy, StrategyContext


@dataclass(frozen=True)
class FakeAsset:
    symbol: str


@dataclass
class FakeIndicator:
    ready: bool
    value: Decimal


@dataclass(frozen=True)
class FakeBar:
    session_id: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("1000")


class FakeIndicatorFactory:
    def __init__(self, *, ready: bool = True) -> None:
        self.ready = ready
        self.created: dict[tuple[str, int | None], FakeIndicator] = {}

    def ema(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("ema", window)

    def atr(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("atr", window)

    def rsi(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("rsi", window)

    def session_vwap(self, asset: FakeAsset) -> FakeIndicator:
        return self._indicator("session_vwap", None)

    def volume_ratio(self, asset: FakeAsset, window: int) -> FakeIndicator:
        return self._indicator("volume_ratio", window)

    def _indicator(self, name: str, window: int | None) -> FakeIndicator:
        indicator = FakeIndicator(ready=self.ready, value=Decimal("0"))
        self.created[(name, window)] = indicator
        return indicator


class FakeContext:
    def __init__(self, *, ready: bool = True) -> None:
        self.indicator = FakeIndicatorFactory(ready=ready)
        self.intents: list[tuple[str, FakeAsset, Decimal | None]] = []

    def symbol(self, symbol: str) -> FakeAsset:
        return FakeAsset(symbol=symbol)

    def subscribe(self, asset: FakeAsset, *, timeframe: str, warmup: int = 1) -> None:
        return None

    def target_quantity(self, asset: FakeAsset, quantity: Decimal) -> None:
        self.intents.append(("target_quantity", asset, quantity))

    def close(self, asset: FakeAsset) -> None:
        self.intents.append(("close", asset, None))


def _ctx(ctx: FakeContext) -> StrategyContext:
    return cast(StrategyContext, ctx)


def _bar(bar: FakeBar) -> Bar:
    return cast(Bar, bar)


def test_vwap_pullback_is_strategy_subclass() -> None:
    from examples.strategies.vwap_pullback import VwapPullbackStrategy

    assert issubclass(VwapPullbackStrategy, Strategy)


def test_no_entry_before_indicators_are_ready() -> None:
    from examples.strategies.vwap_pullback import VwapPullbackStrategy

    ctx = FakeContext(ready=False)
    strategy = VwapPullbackStrategy(symbol="AAPL", target_quantity=Decimal("2"))
    strategy.initialize(_ctx(ctx))

    strategy.on_bar(_ctx(ctx), _bar(_long_setup_bar(session_id="session-1")))

    assert ctx.intents == []


def test_long_entry_after_l1_l2_l3_scores_pass() -> None:
    from examples.strategies.vwap_pullback import VwapPullbackStrategy

    ctx = FakeContext()
    strategy = VwapPullbackStrategy(
        symbol="AAPL",
        target_quantity=Decimal("2"),
        opening_range_bars=1,
    )
    strategy.initialize(_ctx(ctx))
    _set_long_setup_indicators(ctx)

    strategy.on_bar(_ctx(ctx), _bar(_opening_range_bar(session_id="session-1")))
    strategy.on_bar(_ctx(ctx), _bar(_long_setup_bar(session_id="session-1")))

    assert ctx.intents == [("target_quantity", FakeAsset("AAPL"), Decimal("2"))]
    assert strategy.last_score is not None
    assert strategy.last_score.direction == "LONG"
    assert strategy.last_score.l1 >= strategy.config.l1_min
    assert strategy.last_score.l2 >= strategy.config.l2_min
    assert strategy.last_score.l3 >= strategy.config.l3_min


def test_short_entry_after_l1_l2_l3_scores_pass() -> None:
    from examples.strategies.vwap_pullback import VwapPullbackStrategy

    ctx = FakeContext()
    strategy = VwapPullbackStrategy(
        symbol="AAPL",
        target_quantity=Decimal("2"),
        opening_range_bars=1,
    )
    strategy.initialize(_ctx(ctx))
    _set_short_setup_indicators(ctx)

    strategy.on_bar(_ctx(ctx), _bar(_opening_range_bar(session_id="session-1")))
    strategy.on_bar(_ctx(ctx), _bar(_short_setup_bar(session_id="session-1")))

    assert ctx.intents == [("target_quantity", FakeAsset("AAPL"), Decimal("-2"))]
    assert strategy.last_score is not None
    assert strategy.last_score.direction == "SHORT"
    assert strategy.last_score.l1 >= strategy.config.l1_min
    assert strategy.last_score.l2 >= strategy.config.l2_min
    assert strategy.last_score.l3 >= strategy.config.l3_min


@pytest.mark.parametrize(
    ("exit_bar", "expected_intent"),
    [
        (
            FakeBar(
                session_id="session-1",
                open=Decimal("101"),
                high=Decimal("101.2"),
                low=Decimal("98.9"),
                close=Decimal("99.2"),
            ),
            ("close", FakeAsset("AAPL"), None),
        ),
        (
            FakeBar(
                session_id="session-1",
                open=Decimal("101"),
                high=Decimal("105.1"),
                low=Decimal("100.8"),
                close=Decimal("104.8"),
            ),
            ("close", FakeAsset("AAPL"), None),
        ),
    ],
)
def test_close_on_stop_or_take_profit(
    exit_bar: FakeBar,
    expected_intent: tuple[str, FakeAsset, Decimal | None],
) -> None:
    from examples.strategies.vwap_pullback import VwapPullbackStrategy

    ctx = FakeContext()
    strategy = VwapPullbackStrategy(
        symbol="AAPL",
        target_quantity=Decimal("2"),
        opening_range_bars=1,
        stop_atr_multiple=Decimal("1"),
        take_profit_atr_multiple=Decimal("2"),
    )
    strategy.initialize(_ctx(ctx))
    _set_long_setup_indicators(ctx)
    strategy.on_bar(_ctx(ctx), _bar(_opening_range_bar(session_id="session-1")))
    strategy.on_bar(_ctx(ctx), _bar(_long_setup_bar(session_id="session-1")))

    strategy.on_bar(_ctx(ctx), _bar(exit_bar))

    assert ctx.intents[-1] == expected_intent


def test_strategy_does_not_import_runtime_execution_broker_or_update_indicators() -> None:
    source = Path("examples/strategies/vwap_pullback.py").read_text()
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )

    assert not {
        module
        for module in imported_modules
        if module.startswith(("qts.runtime", "qts.execution", "qts.broker"))
    }
    assert ".update(" not in source


def test_vwap_pullback_example_does_not_use_any() -> None:
    source = Path("examples/strategies/vwap_pullback.py").read_text()
    tree = ast.parse(source)

    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "typing"
        for alias in node.names
    }
    annotation_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == "Any"
    }

    assert "Any" not in imported_names
    assert annotation_names == set()


def test_vwap_pullback_indicators_use_one_lifecycle_boundary() -> None:
    source = Path("examples/strategies/vwap_pullback.py").read_text()

    assert "class VwapPullbackIndicators" in source
    assert "self._indicators: VwapPullbackIndicators | None" in source
    assert "AssetIndicator | None" not in source
    assert "self._ATR_7" not in source
    assert "def _indicator_value" not in source


def _set_long_setup_indicators(ctx: FakeContext) -> None:
    ctx.indicator.created[("ema", 20)].value = Decimal("103")
    ctx.indicator.created[("ema", 26)].value = Decimal("102")
    ctx.indicator.created[("ema", 32)].value = Decimal("101")
    ctx.indicator.created[("atr", 7)].value = Decimal("2")
    ctx.indicator.created[("rsi", 14)].value = Decimal("55")
    ctx.indicator.created[("session_vwap", None)].value = Decimal("100")
    ctx.indicator.created[("volume_ratio", 20)].value = Decimal("1.8")


def _set_short_setup_indicators(ctx: FakeContext) -> None:
    ctx.indicator.created[("ema", 20)].value = Decimal("97")
    ctx.indicator.created[("ema", 26)].value = Decimal("98")
    ctx.indicator.created[("ema", 32)].value = Decimal("99")
    ctx.indicator.created[("atr", 7)].value = Decimal("2")
    ctx.indicator.created[("rsi", 14)].value = Decimal("45")
    ctx.indicator.created[("session_vwap", None)].value = Decimal("100")
    ctx.indicator.created[("volume_ratio", 20)].value = Decimal("1.8")


def _opening_range_bar(*, session_id: str) -> FakeBar:
    return FakeBar(
        session_id=session_id,
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100.5"),
    )


def _long_setup_bar(*, session_id: str) -> FakeBar:
    return FakeBar(
        session_id=session_id,
        open=Decimal("100.5"),
        high=Decimal("102.2"),
        low=Decimal("99.8"),
        close=Decimal("101"),
    )


def _short_setup_bar(*, session_id: str) -> FakeBar:
    return FakeBar(
        session_id=session_id,
        open=Decimal("99.5"),
        high=Decimal("100.2"),
        low=Decimal("97.8"),
        close=Decimal("99"),
    )
