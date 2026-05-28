"""Unit tests for backtest strategy loading."""

from __future__ import annotations

import sys
import textwrap
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pytest
from qts.backtest.pipeline import BacktestPipeline
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata
from qts.data.sources.replay_market_data_source import ReplayMarketDataBundle
from qts.domain.market_data import Bar
from qts.registry.instrument_registry import InstrumentRegistry
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)


def test_load_strategy_supports_module_and_class_syntax() -> None:
    """Load strategies from both supported class path formats."""
    colon_strategy = BacktestPipeline.load_strategy(
        "tests.integration.test_backtest_gc_si:BuyOneGcStrategy",
        {},
    )
    dotted_strategy = BacktestPipeline.load_strategy(
        "tests.integration.test_backtest_gc_si.BuyOneGcStrategy",
        {},
    )

    assert colon_strategy.__class__.__name__ == "BuyOneGcStrategy"
    assert dotted_strategy.__class__.__name__ == "BuyOneGcStrategy"


def test_load_strategy_loads_from_relative_python_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Load a strategy from a file when module import fails but .py exists."""
    module_name = "tmp_backtest_strategy_fixture"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from qts.strategy_sdk import Strategy


            class FileBacktestStrategy(Strategy):
                def __init__(self, note: str = "ok") -> None:
                    self.note = note
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    strategy = BacktestPipeline.load_strategy(
        f"{module_name}:FileBacktestStrategy", {"note": "loaded"}
    )
    assert cast(Any, strategy).note == "loaded"


def test_load_strategy_file_fallback_registers_module_for_dataclass_slots(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_name = "tmp_backtest_dataclass_strategy"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass
            from qts.strategy_sdk import Strategy


            @dataclass(frozen=True, slots=True)
            class FileStrategyConfig:
                note: str = "ok"


            class FileDataclassStrategy(Strategy):
                def __init__(self, note: str = "ok") -> None:
                    self.config = FileStrategyConfig(note=note)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    sys.modules.pop(module_name, None)

    strategy = BacktestPipeline.load_strategy(
        f"{module_name}:FileDataclassStrategy",
        {"note": "loaded"},
    )

    assert cast(Any, strategy).config.note == "loaded"
    assert sys.modules[module_name].__name__ == module_name


def test_load_strategy_rejects_invalid_class_path() -> None:
    """Reject malformed strategy class references."""
    with pytest.raises(ValueError, match="strategy_class must be 'module:Class'"):
        BacktestPipeline.load_strategy("not_a_path", {})


def test_load_strategy_rejects_missing_class() -> None:
    """Reject when class name does not exist in module."""
    with pytest.raises(ValueError, match="not found in module"):
        BacktestPipeline.load_strategy(
            "tests.integration.test_backtest_gc_si:MissingBacktestStrategy",
            {},
        )


def test_load_strategy_rejects_non_strategy_class(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject classes that do not subclass qts.strategy_sdk.Strategy."""
    module_name = "tmp_backtest_not_strategy"
    module_path = tmp_path / f"{module_name}.py"
    module_path.write_text(
        textwrap.dedent(
            """
            class NotStrategy:
                pass
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    with pytest.raises(TypeError, match="must subclass"):
        BacktestPipeline.load_strategy(f"{module_name}:NotStrategy", {})


def test_materialized_replay_cache_reuses_aggregated_bars_without_consuming_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache hit must preserve isolated engines while skipping source replay work."""

    instrument_id = InstrumentId("EQUITY.US.NASDAQ.AAPL")
    source_bars = (
        _bar(instrument_id, 0, close="100"),
        _bar(instrument_id, 1, close="102"),
    )
    build_count = 0
    captured_engine_bars: list[tuple[Bar, ...]] = []

    def failing_source() -> Any:
        raise AssertionError("source bars must not be consumed on materialized cache hit")
        yield  # pragma: no cover

    class FakeReplayMarketDataSource:
        def __init__(self, config: object, catalog: object) -> None:
            self._config = config
            self._catalog = catalog

        def build(self) -> ReplayMarketDataBundle:
            nonlocal build_count
            build_count += 1
            return ReplayMarketDataBundle(
                bars=iter(source_bars) if build_count == 1 else failing_source(),
                dataset_stats={},
                exchange_timezone_by_instrument={instrument_id: "UTC"},
                session_window_by_instrument={},
                instrument_registry=InstrumentRegistry(),
                dataset_metadata=(
                    DatasetMetadata(
                        dataset_id="fixture",
                        source="fixture.csv",
                        instrument_id=instrument_id,
                        timeframe="2m",
                        timezone_policy="UTC",
                        adjustment_policy="raw",
                        normalization_version="fixture-v1",
                        created_at=datetime(2026, 1, 1, tzinfo=UTC),
                        content_hash="sha256:fixture",
                        row_count=2,
                    ),
                ),
                contract_multipliers={},
                future_roll_registry=None,
            )

    def fake_from_config(config: object, *, bars: Any, **kwargs: object) -> object:
        captured = tuple(bars)
        captured_engine_bars.append(captured)
        return type("FakeEngine", (), {"bars": captured})()

    monkeypatch.setattr("qts.backtest.pipeline.ReplayMarketDataSource", FakeReplayMarketDataSource)
    monkeypatch.setattr("qts.backtest.pipeline.BacktestEngine.from_config", fake_from_config)
    monkeypatch.setattr(BacktestPipeline, "catalog", lambda self: object())

    pipeline = BacktestPipeline(_backtest_config(tmp_path)).with_materialized_replay_cache(
        tmp_path / "replay-cache"
    )

    first_engine, _ = pipeline.build_engine()
    second_engine, _ = pipeline.with_strategy_params({"quantity": "2"}).build_engine()

    assert build_count == 2
    assert len(captured_engine_bars) == 2
    assert captured_engine_bars[0] == captured_engine_bars[1]
    assert captured_engine_bars[0][0].timeframe == "2m"
    assert captured_engine_bars[0][0].start_time == source_bars[0].start_time
    assert captured_engine_bars[0][0].end_time == source_bars[-1].end_time
    assert captured_engine_bars[0][0].open == Decimal("100")
    assert captured_engine_bars[0][0].close == Decimal("102")
    assert cast(Any, first_engine).bars == cast(Any, second_engine).bars
    assert list((tmp_path / "replay-cache").glob("*.jsonl"))


def _backtest_config(tmp_path: Path) -> BacktestRuntimeConfig:
    return BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            source="local_historical",
            config_path=tmp_path / "historical.local.yaml",
            catalog="research",
        ),
        roots=("EQUITY",),
        symbols=("AAPL",),
        instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
        timeframe="2m",
        initial_cash=Decimal("100000"),
        strategy_class="tests.integration.test_optimizer_consumes_backtest_config:ParametrizedBuyStrategy",
        strategy_params={"quantity": "1"},
        risk_config=BacktestRiskConfig(max_notional=Decimal("100000000")),
    )


def _bar(instrument_id: InstrumentId, minute: int, *, close: str) -> Bar:
    start = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=minute)
    value = Decimal(close)
    return Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=start + timedelta(minutes=1),
        timeframe="1m",
        session_id="2026-01-01",
        open=value,
        high=value,
        low=value,
        close=value,
        volume=Decimal("10"),
        is_complete=True,
    )
