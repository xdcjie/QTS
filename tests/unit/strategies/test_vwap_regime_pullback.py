from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]
from qts.config.ibkr import IbkrEnvironmentConfig
from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar

from strategies.production.vwap_production_pullback import (
    GcVwapProductionPullbackStrategy,
    SiVwapProductionPullbackStrategy,
    VwapProductionPullbackConfig,
    VwapProductionPullbackStrategy,
    VwapProductionRegimeGateConfig,
    _TrailingRegimeGate,
)
from strategies.research.vwap_factor_research import VwapFactorResearchStrategy

_GC_INSTRUMENT = InstrumentId("FUTURE.CME.GC.GCG6")
_SI_INSTRUMENT = InstrumentId("FUTURE.CME.SI.SIH6")


class _FakeIndicatorFactory:
    def session_vwap(self, _asset: object) -> object:
        return object()

    def atr(self, _asset: object, _window: int) -> object:
        return object()

    def volume_ratio(self, _asset: object, _window: int) -> object:
        return object()

    def rate_of_change(self, _asset: object, _window: int) -> object:
        return object()

    def sma(self, _asset: object, _window: int) -> object:
        return object()


class _FakeStrategyContext:
    def __init__(self) -> None:
        self.indicator = _FakeIndicatorFactory()
        self.assets: dict[str, Any] = {}
        self.subscriptions: list[tuple[str, str, int]] = []

    def symbol(self, symbol: str) -> Any:
        instrument_id = _GC_INSTRUMENT if symbol == "GC" else _SI_INSTRUMENT
        asset = type("FakeAsset", (), {"instrument_id": instrument_id, "symbol": symbol})()
        self.assets[symbol] = asset
        return asset

    def subscribe(self, asset: Any, *, timeframe: str, warmup: int = 1) -> None:
        self.subscriptions.append((asset.symbol, timeframe, warmup))


def _bar(
    symbol: str,
    *,
    session: str,
    open_: str,
    high: str,
    low: str,
    close: str,
    start_hour_utc: int = 14,
    volume: str = "1000",
) -> Bar:
    session_date = datetime.fromisoformat(session).date()
    start = datetime(
        session_date.year,
        session_date.month,
        session_date.day,
        start_hour_utc,
        0,
        tzinfo=UTC,
    )
    return Bar(
        instrument_id=_GC_INSTRUMENT if symbol == "GC" else _SI_INSTRUMENT,
        start_time=start,
        end_time=start + timedelta(minutes=15),
        timeframe="15m",
        session_id=session,
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
        is_complete=True,
    )


def _feed_session(
    gate: _TrailingRegimeGate,
    symbol: str,
    *,
    session: str,
    open_: str,
    high: str,
    low: str,
    close: str,
) -> None:
    gate.update_bar(
        symbol,
        _bar(
            symbol,
            session=session,
            open_=open_,
            high=high,
            low=low,
            close=close,
        ),
    )


def test_gc_strategy_uses_best_stable_production_candidate_parameters() -> None:
    strategy = GcVwapProductionPullbackStrategy()

    assert strategy._config.symbol == "GC"
    assert strategy._config.target_quantity == Decimal("4")
    assert strategy._config.min_volume_ratio == Decimal("1.3")
    assert strategy._config.entry_window == "asia_20_02"
    assert strategy._config.confirmation_profile == "session_sigma_mom120"
    assert strategy._regime_config.rule == "hard_churn225"


def test_si_strategy_uses_best_stable_production_candidate_parameters() -> None:
    strategy = SiVwapProductionPullbackStrategy()

    assert strategy._config.symbol == "SI"
    assert strategy._config.target_quantity == Decimal("3")
    assert strategy._config.min_volume_ratio == Decimal("1.5")
    assert strategy._config.entry_window == "asia_20_02"
    assert strategy._config.confirmation_profile == "trend_session_sigma"
    assert strategy._regime_config.rule == "hard14_ccvol17"


def test_production_strategy_does_not_depend_on_research_strategy() -> None:
    assert not issubclass(VwapProductionPullbackStrategy, VwapFactorResearchStrategy)


def test_production_strategy_declares_main_bar_timeframe_subscription() -> None:
    config = VwapProductionPullbackConfig(
        symbol="GC",
        timeframe="3m",
        regime_gate=VwapProductionRegimeGateConfig(rule="off"),
    )
    strategy = VwapProductionPullbackStrategy(config)
    ctx: Any = _FakeStrategyContext()

    strategy.initialize(ctx)

    assert ctx.subscriptions == [("GC", "3m", config.required_warmup_bars)]


def test_production_regime_subscriptions_follow_strategy_timeframe_config() -> None:
    config = VwapProductionPullbackConfig(
        symbol="GC",
        timeframe="2m",
        regime_gate=VwapProductionRegimeGateConfig(
            symbols=("GC", "SI"),
            timeframe="15m",
            lookback_sessions=2,
            min_history_sessions=2,
        ),
    )
    strategy = VwapProductionPullbackStrategy(config)
    ctx: Any = _FakeStrategyContext()

    strategy.initialize(ctx)

    assert ctx.subscriptions == [
        ("GC", "2m", 1382),
        ("SI", "2m", 1382),
    ]


def test_trailing_gate_blocks_only_after_prior_completed_sessions_are_ready() -> None:
    gate = _TrailingRegimeGate(
        VwapProductionRegimeGateConfig(
            rule="hard_churn225",
            symbols=("GC", "SI"),
            lookback_sessions=2,
            min_history_sessions=2,
        )
    )

    assert not gate.allows_new_entries()

    for symbol in ("GC", "SI"):
        _feed_session(
            gate,
            symbol,
            session="2025-01-01",
            open_="100",
            high="103",
            low="100",
            close="100.5",
        )
        _feed_session(
            gate,
            symbol,
            session="2025-01-02",
            open_="100.5",
            high="103.5",
            low="100.5",
            close="101.0",
        )

    assert not gate.allows_new_entries()

    for symbol in ("GC", "SI"):
        _feed_session(
            gate,
            symbol,
            session="2025-01-03",
            open_="101.0",
            high="101.4",
            low="101.0",
            close="101.1",
        )

    assert not gate.allows_new_entries()


def test_hard14_ccvol17_does_not_block_high_close_to_close_volatility() -> None:
    gate = _TrailingRegimeGate(
        VwapProductionRegimeGateConfig(
            rule="hard14_ccvol17",
            symbols=("GC", "SI"),
            lookback_sessions=2,
            min_history_sessions=2,
        )
    )

    for symbol in ("GC", "SI"):
        _feed_session(
            gate,
            symbol,
            session="2025-01-01",
            open_="100",
            high="103",
            low="100",
            close="100",
        )
        _feed_session(
            gate,
            symbol,
            session="2025-01-02",
            open_="100",
            high="104",
            low="100",
            close="104",
        )
        _feed_session(
            gate,
            symbol,
            session="2025-01-03",
            open_="104",
            high="107.12",
            low="100",
            close="100",
        )
        _feed_session(
            gate,
            symbol,
            session="2025-01-04",
            open_="100",
            high="100",
            low="100",
            close="100",
        )

    assert gate.allows_new_entries()


def test_generic_formal_config_rejects_research_blocked_session_shortcut() -> None:
    with pytest.raises(TypeError):
        VwapProductionPullbackConfig(blocked_entry_sessions=("2025-01-02",))  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        VwapProductionPullbackConfig(factor_filters=("session_sigma_range",))  # type: ignore[call-arg]


def test_formal_strategy_configs_point_to_gc_and_si_wrappers() -> None:
    gc_payload = yaml.safe_load(
        Path("configs/strategies/vwap_production_pullback_gc.yaml").read_text(encoding="utf-8")
    )
    si_payload = yaml.safe_load(
        Path("configs/strategies/vwap_production_pullback_si.yaml").read_text(encoding="utf-8")
    )

    assert gc_payload["class_path"] == (
        "strategies.production.vwap_production_pullback:GcVwapProductionPullbackStrategy"
    )
    assert si_payload["class_path"] == (
        "strategies.production.vwap_production_pullback:SiVwapProductionPullbackStrategy"
    )
    assert gc_payload["params"] == {"timeframe": "15m"}
    assert si_payload["params"] == {"timeframe": "15m"}


def test_formal_backtest_configs_feed_gc_and_si_for_online_regime_gate() -> None:
    for path, expected_class in (
        (
            Path("configs/backtest.vwap_production_pullback_gc.yaml"),
            "strategies.production.vwap_production_pullback:GcVwapProductionPullbackStrategy",
        ),
        (
            Path("configs/backtest.vwap_production_pullback_si.yaml"),
            "strategies.production.vwap_production_pullback:SiVwapProductionPullbackStrategy",
        ),
    ):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert payload["roots"] == ["GC", "SI"]
        assert payload["symbols"] == ["GC", "SI"]
        assert payload["start"] == "2025-01-01T00:00:00Z"
        assert payload["end"] == "2026-04-10T00:00:00Z"
        assert payload["timeframe"] == "15m"
        assert payload["strategy_class"] == expected_class
        assert payload["strategy_params"] == {"timeframe": "15m"}
        assert payload["warmup_bars"] >= 120 * 92


def test_formal_paper_example_configs_point_to_gc_and_si_wrappers() -> None:
    for path, expected_class in (
        (
            Path("configs/paper.vwap_production_pullback_gc.example.yaml"),
            "strategies.production.vwap_production_pullback:GcVwapProductionPullbackStrategy",
        ),
        (
            Path("configs/paper.vwap_production_pullback_si.example.yaml"),
            "strategies.production.vwap_production_pullback:SiVwapProductionPullbackStrategy",
        ),
    ):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert payload["mode"] == "paper"
        assert payload["provider"] == "ibkr"
        assert payload["observe_only"] is True
        assert payload["strategy"]["class_path"] == expected_class
        assert payload["strategy"]["params"] == {"timeframe": "15m"}
        ibkr_config = IbkrEnvironmentConfig.from_yaml(path)
        assert ibkr_config.mode == "paper"
        assert ibkr_config.observe_only is True
        assert ibkr_config.account_classification() == "paper"
