from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS


def test_build_historical_csv_index_cli_writes_sidecar_index(tmp_path: Path) -> None:
    csv_path = tmp_path / "gc.csv"
    _write_rows(csv_path)
    module = _load_script()

    exit_code = module.main([str(csv_path)])

    index_path = csv_path.with_suffix(csv_path.suffix + ".index.json")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["granularity"] == "day"
    assert payload["row_count"] == 2


def _load_script() -> ModuleType:
    module_path = Path("scripts/build_historical_csv_index.py")
    spec = importlib.util.spec_from_file_location("build_historical_csv_index", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_rows(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        writer.writerow(_row("2026-01-02T14:30:00.000000000Z"))
        writer.writerow(_row("2026-01-03T14:30:00.000000000Z"))


def _row(timestamp: str) -> dict[str, str]:
    return {
        "ts_event": timestamp,
        "rtype": "33",
        "publisher_id": "1",
        "instrument_id": "123",
        "open": "2000.0",
        "high": "2000.0",
        "low": "2000.0",
        "close": "2000.0",
        "volume": "2",
        "symbol": "GCQ0",
    }
