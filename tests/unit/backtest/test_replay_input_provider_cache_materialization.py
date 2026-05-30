"""QTS-FINAL-015: BacktestReplayInputProvider caches the catalog and wires the
materialized replay cache.

The catalog is expensive/read-only, so it loads once and can be shared with
sweep siblings; the materialized cache is applied only when a cache dir is set.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from qts.backtest import replay_input as replay_input_module
from qts.backtest.replay_input import BacktestReplayInputProvider
from qts.data.historical.catalog import HistoricalCatalog
from qts.runtime.config import (
    BacktestMarketDataReference,
    BacktestRiskConfig,
    BacktestRuntimeConfig,
)


def _config() -> BacktestRuntimeConfig:
    return BacktestRuntimeConfig(
        roots=("AAPL",),
        symbols=("AAPL",),
        start=datetime(2026, 1, 2, tzinfo=UTC),
        end=datetime(2026, 1, 3, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("10000"),
        strategy_class="tests.support.fill_policy.BuyOnce",
        market_data=BacktestMarketDataReference(config_path=Path("md.yaml"), catalog="research"),
        risk_config=BacktestRiskConfig(max_notional=Decimal("1000000")),
    )


class _SentinelCatalog:
    pass


def _sentinel_catalog() -> HistoricalCatalog:
    return cast(HistoricalCatalog, _SentinelCatalog())


def _patch_catalog_load(monkeypatch: Any) -> list[int]:
    calls: list[int] = []

    def _load(_config: object) -> HistoricalCatalog:
        calls.append(1)
        return _sentinel_catalog()

    monkeypatch.setattr(HistoricalCatalog, "load", staticmethod(_load))
    return calls


def test_catalog_is_loaded_once_and_cached(monkeypatch: Any) -> None:
    calls = _patch_catalog_load(monkeypatch)
    provider = BacktestReplayInputProvider(_config())

    assert provider.cached_catalog() is None
    first = provider.catalog()
    second = provider.catalog()

    assert first is second
    assert provider.cached_catalog() is first
    assert len(calls) == 1


def test_seeded_catalog_is_not_reloaded(monkeypatch: Any) -> None:
    calls = _patch_catalog_load(monkeypatch)
    seed = _sentinel_catalog()
    provider = BacktestReplayInputProvider(_config(), catalog=seed)

    assert provider.cached_catalog() is seed
    assert provider.catalog() is seed
    assert calls == []  # never loaded — the shared catalog was reused


def test_build_inputs_applies_materialized_cache_only_when_dir_set(monkeypatch: Any) -> None:
    _patch_catalog_load(monkeypatch)
    base_bundle = object()
    materialized_bundle = object()
    materialized_calls: list[Path] = []

    class _FakeReplaySource:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def build(self) -> object:
            return base_bundle

    def _materialize(*, config: object, catalog: object, inputs: object, cache_dir: Path) -> object:
        materialized_calls.append(cache_dir)
        return materialized_bundle

    monkeypatch.setattr(replay_input_module, "ReplayMarketDataSource", _FakeReplaySource)
    monkeypatch.setattr(replay_input_module, "materialized_replay_inputs", _materialize)

    without_cache = BacktestReplayInputProvider(_config()).build_inputs()
    assert without_cache is base_bundle
    assert materialized_calls == []

    cache_dir = Path("/tmp/qts-mat-cache")
    with_cache = BacktestReplayInputProvider(
        _config(), materialized_replay_cache_dir=cache_dir
    ).build_inputs()
    assert with_cache is materialized_bundle
    assert materialized_calls == [cache_dir]
