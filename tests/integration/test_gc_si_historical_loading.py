from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from qts.core.ids import InstrumentId
from qts.data.historical.catalog import load_historical_catalog
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS
from qts.registry.symbol_resolution import StaticSymbolResolver


def _load_validation_script() -> ModuleType:
    module_path = Path("scripts/validate_historical.py")
    spec = importlib.util.spec_from_file_location("validate_historical", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_load_historical_catalog_uses_requested_roots_without_counting_rows() -> None:
    catalog = load_historical_catalog(Path("historical"), roots=("GC", "SI"))

    assert catalog.roots == ("GC", "SI")
    assert catalog.datasets["GC"].chain_path == Path("historical/chains/GC.json")
    assert catalog.datasets["GC"].csv_path == Path("historical/data/gc.csv")
    assert catalog.datasets["GC"].dataset.row_count is None
    assert catalog.datasets["GC"].dataset.root == "GC"
    assert catalog.datasets["SI"].chain is not None
    assert catalog.datasets["SI"].chain.root == "SI"
    assert catalog.datasets["SI"].dataset.row_count is None


def test_load_historical_catalog_fails_clearly_when_required_file_is_missing(
    tmp_path: Path,
) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "chains").mkdir()
    shutil.copyfile(Path("historical/chains/GC.json"), tmp_path / "chains" / "GC.json")
    shutil.copyfile(Path("historical/chains/SI.json"), tmp_path / "chains" / "SI.json")

    with pytest.raises(FileNotFoundError, match="historical/data/gc.csv"):
        load_historical_catalog(tmp_path, roots=("GC", "SI"))


def test_load_historical_catalog_accepts_explicit_resolver_without_chain(
    tmp_path: Path,
) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "chains").mkdir()
    (tmp_path / "data" / "equity.csv").write_text(
        ",".join(EXPECTED_HISTORICAL_COLUMNS) + "\n",
        encoding="utf-8",
    )
    resolver = StaticSymbolResolver({"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    catalog = load_historical_catalog(
        tmp_path,
        roots=("EQUITY",),
        symbol_resolvers={"EQUITY": resolver},
    )

    dataset = catalog.datasets["EQUITY"]
    assert dataset.chain is None
    assert dataset.chain_path is None
    assert dataset.symbol_resolver is resolver
    assert dataset.csv_path == tmp_path / "data" / "equity.csv"


def test_validate_historical_cli_writes_sample_evidence_for_requested_roots(
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
            "--roots",
            "GC",
            "SI",
            "--sample-rows",
            "5",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    evidence_files = sorted(output_dir.glob("historical_validation_*.json"))
    assert len(evidence_files) == 1
    payload = json.loads(evidence_files[0].read_text(encoding="utf-8"))
    assert payload["root"] == "historical"
    assert payload["sample_rows"] == 5
    assert payload["datasets"]["GC"]["stats"]["rows_seen"] == 5
    assert payload["datasets"]["SI"]["stats"]["rows_seen"] == 5
