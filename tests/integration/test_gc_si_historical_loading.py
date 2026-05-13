from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from qts.core.ids import InstrumentId
from qts.data.historical.catalog import (
    HistoricalCatalog,
    HistoricalCatalogLoadConfig,
)
from qts.data.historical.config import HistoricalMarketDataConfig
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


def test_historical_catalog_load_uses_requested_roots_without_counting_rows() -> None:
    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            Path("configs/data/historical.local.yaml"),
            catalog="research_futures",
            roots=("GC", "SI"),
        )
    )

    assert catalog.roots == ("GC", "SI")
    assert catalog.datasets["GC"].chain_path == Path("historical/chains/GC.json")
    assert catalog.datasets["GC"].csv_path == Path("historical/data/gc.csv")
    assert catalog.datasets["GC"].dataset.row_count is None
    assert catalog.datasets["GC"].dataset.root == "GC"
    assert catalog.datasets["SI"].chain is not None
    assert catalog.datasets["SI"].chain.root == "SI"
    assert catalog.datasets["SI"].dataset.row_count is None


def test_historical_catalog_load_fails_clearly_when_required_file_is_missing(
    tmp_path: Path,
) -> None:
    config_path = _write_historical_config(tmp_path, roots=("GC", "SI"))

    with pytest.raises(FileNotFoundError, match="historical/data/gc.csv"):
        HistoricalCatalog.load(
            HistoricalCatalogLoadConfig.from_historical_market_data_config(
                config_path,
                catalog="research_futures",
                roots=("GC", "SI"),
            )
        )


def test_historical_catalog_accepts_explicit_resolver_without_chain(
    tmp_path: Path,
) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "equity.csv").write_text(
        ",".join(EXPECTED_HISTORICAL_COLUMNS) + "\n",
        encoding="utf-8",
    )
    config_path = _write_historical_config(tmp_path, roots=("EQUITY",))
    resolver = StaticSymbolResolver({"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")})

    catalog = HistoricalCatalog.from_historical_market_data_config(
        HistoricalMarketDataConfig.from_yaml(config_path),
        catalog="research_futures",
        roots=("EQUITY",),
        symbol_resolvers={"EQUITY": resolver},
    )

    dataset = catalog.datasets["EQUITY"]
    assert dataset.chain is None
    assert dataset.chain_path is None
    assert dataset.symbol_resolver is resolver
    assert dataset.csv_path == tmp_path / "data" / "equity.csv"


def test_historical_catalog_load_uses_static_ids_when_chain_is_absent(
    tmp_path: Path,
) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "equity.csv").write_text(
        ",".join(EXPECTED_HISTORICAL_COLUMNS) + "\n",
        encoding="utf-8",
    )
    config_path = _write_historical_config(tmp_path, roots=("EQUITY",))

    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            config_path,
            catalog="research_futures",
            roots=("EQUITY",),
            instrument_ids={"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")},
        )
    )

    dataset = catalog.datasets["EQUITY"]
    assert dataset.chain is None
    assert dataset.symbol_resolver.instrument_id_for_symbol("AAPL") == InstrumentId(
        "EQUITY.US.NASDAQ.AAPL"
    )


def _write_historical_config(root: Path, *, roots: tuple[str, ...]) -> Path:
    config_path = root / "historical.local.yaml"
    datasets = "\n".join(
        f"""        {symbol}:
          asset_class: {"future" if symbol in {"GC", "SI"} else "equity"}
          {"chain_file: " + symbol + ".json" if symbol in {"GC", "SI"} else ""}
          bars:
            - file: {symbol.lower()}.csv
              timeframe: 1m"""
        for symbol in roots
    )
    config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {root}
      bars_dir: data
      chains_dir: chains
  catalogs:
    research_futures:
      store: local_csv
      datasets:
{datasets}
""",
        encoding="utf-8",
    )
    return config_path


def test_validate_historical_cli_writes_sample_evidence_for_requested_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_validation_script()
    main = cast(Any, module).main

    output_dir = tmp_path / "evidence"
    exit_code = main(
        [
            "--config",
            "configs/data/historical.local.yaml",
            "--catalog",
            "research_futures",
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
    assert payload["config"] == "configs/data/historical.local.yaml"
    assert payload["catalog"] == "research_futures"
    assert payload["sample_rows"] == 5
    assert payload["datasets"]["GC"]["stats"]["rows_seen"] == 5
    assert payload["datasets"]["SI"]["stats"]["rows_seen"] == 5


def test_validate_historical_cli_uses_configured_schema_and_timeframe(
    tmp_path: Path,
) -> None:
    module = _load_validation_script()
    main = cast(Any, module).main
    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    (historical_root / "chains").mkdir(parents=True)
    _write_minimal_chain(historical_root / "chains" / "GC.json")
    _write_custom_schema_csv(historical_root / "data" / "gc_5s.csv")
    config_path = tmp_path / "historical.local.yaml"
    config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
  schemas:
    custom_ohlcv:
      timestamp: time
      symbol: ticker
      instrument_id: source_id
      open: o
      high: h
      low: l
      close: c
      volume: v
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          chain_file: GC.json
          bars:
            - file: gc_5s.csv
              timeframe: 5s
              schema: custom_ohlcv
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / "evidence"

    exit_code = main(
        [
            "--config",
            str(config_path),
            "--catalog",
            "research_futures",
            "--roots",
            "GC",
            "--sample-rows",
            "1",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 0
    evidence_files = sorted(output_dir.glob("historical_validation_*.json"))
    payload = json.loads(evidence_files[0].read_text(encoding="utf-8"))
    dataset = payload["datasets"]["GC"]
    assert dataset["source_timeframe"] == "5s"
    assert dataset["schema_name"] == "custom_ohlcv"
    assert dataset["stats"]["bars_emitted"] == 1


def _write_minimal_chain(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "root": "GC",
                "market": "CME_FUT",
                "currency": "USD",
                "timezone_id": "US/Eastern",
                "tick_size": "0.1",
                "multiplier": "100",
                "trading_calendar": "CMES",
                "contracts": [
                    {
                        "local_symbol": "GCQ0",
                        "expiry": "2026-08-28T22:00:00+00:00",
                        "first_notice_day": "2026-07-31",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_custom_schema_csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("time", "source_id", "o", "h", "l", "c", "v", "ticker"),
        )
        writer.writeheader()
        writer.writerow(
            {
                "time": "2026-01-02T14:30:00.000000000Z",
                "source_id": "GCQ0",
                "o": "2000",
                "h": "2000",
                "l": "2000",
                "c": "2000",
                "v": "1",
                "ticker": "GCQ0",
            }
        )
