from __future__ import annotations

import csv
import shutil
from pathlib import Path

from qts.data.historical.csv_dataset import EXPECTED_HISTORICAL_COLUMNS


def _write_fixture(root: Path) -> Path:
    (root / "historical" / "chains").mkdir(parents=True)
    (root / "historical" / "data").mkdir(parents=True)
    shutil.copyfile(Path("historical/chains/GC.json"), root / "historical" / "chains" / "GC.json")
    shutil.copyfile(Path("historical/chains/SI.json"), root / "historical" / "chains" / "SI.json")
    _write_csv(root / "historical" / "data" / "gc.csv", "GCQ0", ["2000.0", "2001.0"])
    _write_csv(root / "historical" / "data" / "si.csv", "SIN0", ["20.0", "19.0"])
    config_path = root / "backtest.yaml"
    config_path.write_text(
        f"""
dataset_root: {root / "historical"}
roots: [GC, SI]
symbols: [GCQ0, SIN0]
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:02:00Z"
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for index, close in enumerate(closes):
            writer.writerow(
                {
                    "ts_event": f"2010-06-06T22:0{index}:00.000000000Z",
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
    from qts.backtest.research_runner import run_research_backtest

    config_path = _write_fixture(tmp_path)

    left = run_research_backtest(config_path, output_dir=tmp_path / "left")
    right = run_research_backtest(config_path, output_dir=tmp_path / "right")

    assert left.result.report_hash == right.result.report_hash
