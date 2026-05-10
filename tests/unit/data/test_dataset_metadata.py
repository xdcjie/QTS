from __future__ import annotations

from datetime import UTC, datetime

import pytest
from qts.core.ids import InstrumentId
from qts.data.provenance import DatasetMetadata


def test_dataset_metadata_requires_provenance_fields_and_stable_reference() -> None:
    metadata = DatasetMetadata(
        dataset_id="aapl-1m-2026-01-02",
        source="vendor-x",
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        timeframe="1m",
        timezone_policy="exchange",
        adjustment_policy="split-adjusted",
        normalization_version="bars-v1",
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        content_hash="sha256:abc123",
    )

    assert metadata.reference == "vendor-x:aapl-1m-2026-01-02:sha256:abc123"


def test_dataset_metadata_rejects_missing_required_provenance() -> None:
    with pytest.raises(ValueError, match="dataset_id"):
        DatasetMetadata(
            dataset_id=" ",
            source="vendor-x",
            instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
            timeframe="1m",
            timezone_policy="exchange",
            adjustment_policy="raw",
            normalization_version="bars-v1",
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
