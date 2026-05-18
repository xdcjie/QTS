from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from qts.research import HistoryRequest, ResearchBookConfig


def test_research_book_config_rejects_missing_catalog_reference() -> None:
    with pytest.raises(ValueError, match="catalog_name is required"):
        ResearchBookConfig(
            data_config_path=Path("configs/data/historical.local.yaml"),
            catalog_name="",
            roots=("GC",),
            timeframe="1m",
        )


def test_history_request_uses_half_open_interval() -> None:
    request = HistoryRequest(
        root="GC",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
        timeframe="1m",
    )

    assert request.includes(datetime(2026, 1, 1, tzinfo=UTC))
    assert not request.includes(datetime(2026, 1, 2, tzinfo=UTC))
