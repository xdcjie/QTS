from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.research import HistoryRequest, ResearchBook, ResearchBookConfig
from qts.runtime.config import BacktestMarketDataReference, BacktestRuntimeConfig


def test_research_book_history_uses_configured_historical_catalog() -> None:
    book = ResearchBook.from_config(
        ResearchBookConfig(
            data_config_path=Path("configs/data/historical.local.yaml"),
            catalog_name="research_futures",
            roots=("GC",),
            timeframe="1m",
        )
    )
    frame = book.history(
        HistoryRequest(
            root="GC",
            start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
            end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
            timeframe="1m",
        )
    )

    assert len(frame) > 0
    assert all(bar.start_time >= datetime(2010, 6, 6, 22, 0, tzinfo=UTC) for bar in frame)
    assert all(bar.start_time < datetime(2010, 6, 6, 22, 5, tzinfo=UTC) for bar in frame)
    assert all(str(bar.instrument_id).startswith("FUTURE.CME.GC.") for bar in frame)
    assert book.dataset_ids == ("GC:1m:historical/data/gc.csv",)


def test_research_book_can_use_backtest_market_data_reference() -> None:
    config = BacktestRuntimeConfig(
        market_data=BacktestMarketDataReference(
            config_path=Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
        ),
        roots=("GC",),
        symbols=("GCQ0",),
        start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
        end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
        timeframe="1m",
        initial_cash=Decimal("1000000"),
        strategy_class="tests.integration.test_backtest_gc_si:BuyOneGcStrategy",
    )

    book = ResearchBook.from_backtest_config(config)
    frame = book.history(
        HistoryRequest(
            root="GC",
            start=config.start,
            end=config.end,
            timeframe=config.timeframe,
        )
    )

    assert len(frame) > 0
    assert all(config.start <= bar.start_time < config.end for bar in frame)
