from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from qts.data.historical.gc_si import load_gc_si_catalog


def _load_validation_script() -> ModuleType:
    module_path = Path("scripts/validate_historical_gc_si.py")
    spec = importlib.util.spec_from_file_location("validate_historical_gc_si", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_gc_si_catalog_uses_explicit_paths_without_counting_rows() -> None:
    catalog = load_gc_si_catalog(Path("historical"))

    assert catalog.roots == ("GC", "SI")
    assert catalog.datasets["GC"].chain_path == Path("historical/chains/GC.json")
    assert catalog.datasets["GC"].csv_path == Path("historical/data/gc.csv")
    assert catalog.datasets["GC"].dataset.row_count is None
    assert catalog.datasets["GC"].dataset.root == "GC"
    assert catalog.datasets["SI"].chain.root == "SI"
    assert catalog.datasets["SI"].dataset.row_count is None


def test_load_gc_si_catalog_fails_clearly_when_required_file_is_missing(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), tmp_path / "chains" / "GC.json")
    shutil.copyfile(Path("historical/chains/SI.json"), tmp_path / "chains" / "SI.json")

    with pytest.raises(FileNotFoundError, match="historical/data/gc.csv"):
        load_gc_si_catalog(tmp_path)


def test_validate_historical_gc_si_cli_writes_sample_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_validation_script()
    main = cast(Any, module).main

    output_dir = tmp_path / "evidence"
    exit_code = main(
        [
            "--root",
            "historical",
            "--sample-rows",
            "5",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    evidence_files = sorted(output_dir.glob("gc_si_validation_*.json"))
    assert len(evidence_files) == 1
    payload = json.loads(evidence_files[0].read_text(encoding="utf-8"))
    assert payload["root"] == "historical"
    assert payload["sample_rows"] == 5
    assert payload["datasets"]["GC"]["stats"]["rows_seen"] == 5
    assert payload["datasets"]["SI"]["stats"]["rows_seen"] == 5
