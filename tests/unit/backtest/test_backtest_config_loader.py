from __future__ import annotations

from pathlib import Path

from qts.runtime.config_loader import BacktestConfigLoader


def test_config_loader_parses_market_data_payload() -> None:
    cfg = BacktestConfigLoader.from_payload(
        {
            "roots": ["GC"],
            "symbols": ["GC"],
            "start": "2026-01-02T14:30:00Z",
            "end": "2026-01-02T14:31:00Z",
            "timeframe": "1m",
            "initial_cash": "100000",
            "strategy_class": "tests.integration.test_backtest_gc_si:RollingGcStrategy",
            "market_data": {
                "source": "local_historical",
                "config": "configs/data/historical.local.yaml",
                "catalog": "research_futures",
            },
        }
    )

    assert cfg.market_data.source == "local_historical"
    assert cfg.market_data.config_path == Path("configs/data/historical.local.yaml")
    assert cfg.market_data.catalog == "research_futures"
