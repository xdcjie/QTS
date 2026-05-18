from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.research import HistoryRequest, ResearchBook, ResearchBookConfig


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


def test_research_book_aggregates_source_timeframe_before_returning_requested_timeframe() -> None:
    book = ResearchBook.from_config(
        ResearchBookConfig(
            data_config_path=Path("configs/data/historical.local.yaml"),
            catalog_name="research_futures",
            roots=("GC",),
            timeframe="5m",
        )
    )

    frame = book.history(
        HistoryRequest(
            root="GC",
            start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
            end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
            timeframe="5m",
        )
    )

    assert len(frame) > 0
    assert {bar.start_time for bar in frame} == {datetime(2010, 6, 6, 22, 0, tzinfo=UTC)}
    assert {bar.end_time for bar in frame} == {datetime(2010, 6, 6, 22, 5, tzinfo=UTC)}
    assert all(bar.timeframe == "5m" for bar in frame)
    assert all(bar.is_complete for bar in frame)
    assert all(not bar.is_partial for bar in frame)
    assert len({bar.instrument_id for bar in frame}) == len(frame)


def test_research_book_config_can_be_assembled_from_backtest_market_data_reference() -> None:
    config = ResearchBookConfig(
        data_config_path=Path("configs/data/historical.local.yaml"),
        catalog_name="research_futures",
        roots=("GC",),
        timeframe="1m",
    )

    book = ResearchBook.from_config(config)

    frame = book.history(
        HistoryRequest(
            root="GC",
            start=datetime(2010, 6, 6, 22, 0, tzinfo=UTC),
            end=datetime(2010, 6, 6, 22, 5, tzinfo=UTC),
            timeframe="1m",
        )
    )

    assert len(frame) > 0
