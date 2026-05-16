from __future__ import annotations

import importlib
from dataclasses import is_dataclass
from pathlib import Path

import pytest

AUDITED_CLASSES = {
    "RuntimeOrderResult": {
        "module": "qts.runtime.order_result",
        "decision": "keep",
        "role": "runtime result",
    },
    "OrderManagerResult": {
        "module": "qts.domain.orders.value_objects",
        "decision": "keep",
        "role": "domain model",
    },
    "ExecutionReport": {
        "module": "qts.domain.orders.value_objects",
        "decision": "keep",
        "role": "domain model",
    },
    "IbkrExecutionReport": {
        "module": "qts.execution.adapters.ibkr_order_execution",
        "decision": "keep",
        "role": "broker adapter payload",
    },
    "RuntimeEventWriteResult": {
        "module": "qts.runtime.sinks.base",
        "decision": "keep",
        "role": "runtime result",
    },
    "WrittenRuntimeEvent": {
        "module": "qts.runtime.sinks.broker_runtime",
        "decision": "remove",
        "role": "mirror",
    },
    "RuntimeManifest": {
        "module": "qts.reporting.base",
        "decision": "keep",
        "role": "reporting artifact",
    },
    "LiveReportManifest": {
        "module": "qts.reporting.live",
        "decision": "remove",
        "role": "reporting artifact",
    },
    "BacktestArtifacts": {
        "module": "qts.reporting.backtest",
        "decision": "keep",
        "role": "reporting artifact",
    },
}

DOC_PATH = Path("docs/architecture/runtime_value_model_boundaries.md")
ALLOWED_ROLES = {
    "api dto",
    "broker adapter payload",
    "domain model",
    "mirror",
    "reporting artifact",
    "runtime result",
}
ALLOWED_DIRECTIONS = {
    "adapter -> domain",
    "domain -> runtime",
    "runtime -> reporting",
    "runtime internal",
    "removed",
}


def _concept_map_rows() -> dict[str, dict[str, str]]:
    text = DOC_PATH.read_text(encoding="utf-8")
    rows: dict[str, dict[str, str]] = {}
    header: list[str] | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        compact = line.replace("|", "").replace(" ", "").strip()
        if not line.startswith("|") or set(compact) <= {"-", ":"}:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and cells[0] == "Class":
            header = cells
            continue
        if header is None or len(cells) != len(header):
            continue
        row = dict(zip(header, cells, strict=True))
        row["Class"] = row["Class"].strip("`")
        rows[row["Class"]] = row
    return rows


def test_runtime_value_model_concept_map_covers_audited_classes() -> None:
    rows = _concept_map_rows()

    assert set(rows) == set(AUDITED_CLASSES)
    for class_name, expected in AUDITED_CLASSES.items():
        row = rows[class_name]
        assert row["Package"] == expected["module"]
        assert row["Boundary role"] == expected["role"]
        assert row["Boundary role"] in ALLOWED_ROLES
        assert row["Direction"] in ALLOWED_DIRECTIONS
        assert row["Decision"] == expected["decision"]
        assert row["Conversion owner"]
        assert row["Mirror decision"]


def test_retained_runtime_value_models_have_distinct_boundary_classes() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("qts.runtime.live")
    for class_name, expected in AUDITED_CLASSES.items():
        if expected["decision"] == "remove":
            try:
                module = importlib.import_module(expected["module"])
            except ModuleNotFoundError:
                continue
            assert not hasattr(module, class_name)
            continue
        module = importlib.import_module(expected["module"])
        model_type = getattr(module, class_name)
        assert is_dataclass(model_type), class_name
