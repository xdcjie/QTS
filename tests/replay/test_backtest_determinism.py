from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_hash
from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS


def _write_fixture(root: Path) -> Path:
    (root / "historical" / "chains").mkdir(parents=True)
    (root / "historical" / "data").mkdir(parents=True)
    shutil.copyfile(Path("historical/chains/GC.json"), root / "historical" / "chains" / "GC.json")
    shutil.copyfile(Path("historical/chains/SI.json"), root / "historical" / "chains" / "SI.json")
    _write_csv(
        root / "historical" / "data" / "gc.csv",
        "GCQ0",
        ["2000.0", "2001.0", "2002.0", "2003.0"],
    )
    _write_csv(
        root / "historical" / "data" / "si.csv",
        "SIN0",
        ["20.0", "19.0", "18.0", "17.0"],
    )
    data_config_path = root / "historical.local.yaml"
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {root / "historical"}
      bars_dir: data
      chains_dir: chains
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
        SI:
          asset_class: future
          exchange: CME
          chain_file: SI.json
          bars:
            - file: si.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )
    config_path = root / "backtest.yaml"
    config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research_futures
roots: [GC, SI]
symbols: [GCQ0, SIN0]
start: "2010-06-06T22:00:00Z"
end: "2010-06-07T22:02:00Z"
timeframe: 1m
initial_cash: "1000000"
strategy_class: "examples.strategies.gc_si_momentum:GcSiMomentumStrategy"
strategy_params:
  symbols: [GCQ0, SIN0]
  short_window: 1
  long_window: 2
cost_model:
  fixed_commission_per_contract: "0"
  slippage_bps: "0"
risk_config:
  max_notional: "100000000"
warmup_bars: 0
""",
        encoding="utf-8",
    )
    return config_path


def _write_csv(path: Path, symbol: str, closes: list[str]) -> None:
    timestamps = [
        "2010-06-06T22:00:00.000000000Z",
        "2010-06-06T22:01:00.000000000Z",
        "2010-06-07T22:00:00.000000000Z",
        "2010-06-07T22:01:00.000000000Z",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index, close in enumerate(closes):
            writer.writerow(
                {
                    "ts_event": timestamps[index],
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": str(index + 1),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "1",
                    "symbol": symbol,
                }
            )


def test_same_research_config_data_and_strategy_produce_same_report_hash(tmp_path: Path) -> None:
    from qts.backtest.runner import run_backtest

    config_path = _write_fixture(tmp_path)

    left = run_backtest(config_path, output_dir=tmp_path / "left")
    right = run_backtest(config_path, output_dir=tmp_path / "right")

    assert left.result.report_hash == right.result.report_hash


def test_same_research_config_data_and_strategy_produce_same_normalized_artifacts(
    tmp_path: Path,
) -> None:
    from qts.backtest.runner import run_backtest

    config_path = _write_fixture(tmp_path)

    left = run_backtest(config_path, output_dir=tmp_path / "left")
    right = run_backtest(config_path, output_dir=tmp_path / "right")

    assert _normalized_manifest_hash(left.manifest_path) == _normalized_manifest_hash(
        right.manifest_path
    )
    for kind in ("events", "orders", "fills", "trade_ledger", "equity_curve"):
        assert _normalized_ndjson_hash(left.artifact_paths[kind]) == _normalized_ndjson_hash(
            right.artifact_paths[kind]
        )
    left_sequences = _sequence_numbers(left.artifact_paths["events"])
    right_sequences = _sequence_numbers(right.artifact_paths["events"])
    assert left_sequences == right_sequences
    assert left_sequences == sorted(left_sequences)
    assert len(left_sequences) == len(set(left_sequences))


def _normalized_manifest_hash(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("manifest_hash", None)
    payload.pop("created_at", None)
    payload.pop("finalized_at", None)
    for artifact in payload["artifacts"].values():
        artifact["path"] = Path(artifact["path"]).name
    return stable_json_hash(payload)


def _normalized_ndjson_hash(path: Path) -> str:
    return stable_json_hash(_read_ndjson(path))


def _sequence_numbers(path: Path) -> list[int]:
    return [int(row["sequence_no"]) for row in _read_ndjson(path)]


def _read_ndjson(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
