from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path

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


def test_dataset_metadata_keeps_required_text_validation_inside_the_model() -> None:
    tree = ast.parse(Path("backend/src/qts/data/provenance.py").read_text(encoding="utf-8"))

    private_functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("_")
    }

    assert "_require_text" not in private_functions
