"""Anchor: optimizer CLI accepts a backtest YAML config and sweeps strategy_params.

Domain fact: optimizer and single-run backtest must share the
``configs/backtest.yaml -> HistoricalCatalog -> ReplayMarketDataSource
-> BacktestEngine.from_config`` path. The optimizer is a thin wrapper
that varies ``strategy_params`` across a parameter grid; everything
else (instrument registry, cost model, risk engine, dataset metadata)
comes from the same code path ``scripts/run_backtest.py`` uses.

Owner: ``qts.research.optimizer.pipeline.BacktestPipelineRunner`` +
``scripts/run_optimizer.py`` (pipeline branch).

Forbidden shortcut: hand-rolling a bars factory; bypassing
``qts.backtest.runner`` helpers; loading the strategy through any
loader other than the one ``run_backtest`` uses.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from qts.backtest.pipeline import BacktestPipeline
from qts.data.historical.csv_format import EXPECTED_HISTORICAL_COLUMNS
from qts.strategy_sdk import Strategy

# Re-exported as a top-level module attribute so the optimizer's
# ``load_strategy_from_config`` loader can find it via
# ``"tests.integration.test_optimizer_consumes_backtest_config:ParametrizedBuyStrategy"``.


class ParametrizedBuyStrategy(Strategy):
    """Buy ``quantity`` shares on bar index ``entry_bar`` (1-based)."""

    def __init__(self, *, quantity: str = "1", entry_bar: int = 1) -> None:
        from decimal import Decimal

        self._quantity = Decimal(str(quantity))
        self._entry_bar = int(entry_bar)
        self._index = 0
        self._opened = False
        self._asset: Any = None

    def initialize(self, ctx: Any) -> None:
        self._asset = ctx.symbol("AAPL")

    def on_bar(self, ctx: Any, bar: object) -> None:
        self._index += 1
        if self._opened or self._index < self._entry_bar:
            return
        ctx.target_quantity(self._asset, self._quantity)
        self._opened = True


def _write_fixture_csv(path: Path, *, closes: list[str], symbol: str = "AAPL") -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EXPECTED_HISTORICAL_COLUMNS)
        writer.writeheader()
        for minute, close in enumerate(closes):
            writer.writerow(
                {
                    "ts_event": f"2010-06-06T22:0{minute}:00.000000000Z",
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": str(minute + 1),
                    "open": close,
                    "high": close,
                    "low": close,
                    "close": close,
                    "volume": "100",
                    "symbol": symbol,
                }
            )


def _write_fixtures(tmp_path: Path) -> tuple[Path, Path]:
    historical_root = tmp_path / "historical"
    (historical_root / "data").mkdir(parents=True)
    _write_fixture_csv(
        historical_root / "data" / "equity.csv",
        closes=["100.0", "101.0", "102.0", "103.0", "104.0"],
    )
    data_config_path = tmp_path / "historical.local.yaml"
    data_config_path.write_text(
        f"""
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: {historical_root}
      bars_dir: data
      chains_dir: chains
  catalogs:
    research:
      store: local_csv
      datasets:
        EQUITY:
          asset_class: equity
          bars:
            - file: equity.csv
              timeframe: 1m
""",
        encoding="utf-8",
    )
    backtest_config_path = tmp_path / "backtest.yaml"
    backtest_config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research
roots: [EQUITY]
symbols: [AAPL]
instrument_ids:
  AAPL: EQUITY.US.NASDAQ.AAPL
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:05:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_class: "tests.integration.test_optimizer_consumes_backtest_config:ParametrizedBuyStrategy"
strategy_params:
  quantity: "1"
  entry_bar: 1
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )
    return backtest_config_path, data_config_path


def test_optimizer_cli_consumes_backtest_config_and_sweeps_strategy_params(
    tmp_path: Path,
) -> None:
    backtest_config, _ = _write_fixtures(tmp_path)
    optimizer_config = tmp_path / "optimizer.yaml"
    optimizer_config.write_text(
        f"""
backtest_config: {backtest_config}
objective_metric: total_return
capital_metrics:
  margin_proxy: "1000"
parameters:
  - name: entry_bar
    values: [1, 2]
  - name: quantity
    values: ["1", "2"]
validation:
  constraints:
    - metric: pnl_usd
      operator: ">"
      threshold: "0"
""",
        encoding="utf-8",
    )
    validation_output = tmp_path / "validation-summary.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_optimizer.py",
            str(optimizer_config),
            "--output-root",
            str(tmp_path / "optimizer-runs"),
            "--validation-output",
            str(validation_output),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            "PYTHONPATH": f"backend/src{os.pathsep}.",
            "QTS_API_DEV_TOKENS": "1",
            "PATH": os.environ.get("PATH", ""),
        },
    )

    assert result.returncode == 0, (
        f"optimizer CLI failed (returncode={result.returncode}):\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    output = result.stdout
    assert "rank" in output.lower(), f"missing rank header in output:\n{output}"
    rank_lines = [
        line for line in output.splitlines() if line.strip().startswith(("1", "2", "3", "4"))
    ]
    assert len(rank_lines) >= 4, f"expected at least 4 ranked rows, got:\n{output}"
    manifest_hash_column_present = "manifest_hash" in output
    assert manifest_hash_column_present, f"manifest_hash column missing in output:\n{output}"
    validation_payload = json.loads(validation_output.read_text(encoding="utf-8"))
    assert validation_payload["accepted_count"] >= 1
    assert (
        validation_payload["accepted_runs"][0]["capital_metrics"]["return_on_margin_proxy"] != "0"
    )


def test_pipeline_sweeps_params_loaded_from_strategy_config(tmp_path: Path) -> None:
    """Regression: optimizer overrides must survive strategy_config normalization."""

    data_config_path = tmp_path / "historical.local.yaml"
    data_config_path.write_text(
        """
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: /tmp
      bars_dir: data
  catalogs:
    research:
      store: local_csv
      datasets: {}
""",
        encoding="utf-8",
    )
    strategy_config_path = tmp_path / "strategy.yaml"
    strategy_config_path.write_text(
        """
strategy_id: parameterized-buy
class_path: tests.integration.test_optimizer_consumes_backtest_config:ParametrizedBuyStrategy
params:
  quantity: "1"
  entry_bar: 1
""",
        encoding="utf-8",
    )
    backtest_config_path = tmp_path / "backtest.yaml"
    backtest_config_path.write_text(
        f"""
market_data:
  source: local_historical
  config: {data_config_path}
  catalog: research
roots: [EQUITY]
symbols: [AAPL]
instrument_ids:
  AAPL: EQUITY.US.NASDAQ.AAPL
start: "2010-06-06T22:00:00Z"
end: "2010-06-06T22:05:00Z"
timeframe: 1m
initial_cash: "100000"
strategy_config: {strategy_config_path}
risk_config:
  max_notional: "100000000"
""",
        encoding="utf-8",
    )

    pipeline = BacktestPipeline.from_yaml(backtest_config_path)
    swept_pipeline = pipeline.with_strategy_params({"quantity": "3", "entry_bar": 2})

    assert swept_pipeline.config.strategy_params["quantity"] == "3"
    assert swept_pipeline.config.strategy_params["entry_bar"] == 2
    assert swept_pipeline.config.strategy is not None
    assert swept_pipeline.config.strategy.params["quantity"] == "3"
    assert swept_pipeline.config.strategy.params["entry_bar"] == 2


def test_materialized_replay_cache_preserves_backtest_metrics(tmp_path: Path) -> None:
    backtest_config, _ = _write_fixtures(tmp_path)

    baseline_engine, _ = BacktestPipeline.from_yaml(backtest_config).build_engine()
    baseline = baseline_engine.run_streaming(tmp_path / "baseline", compact_events=True)
    cached_engine, _ = (
        BacktestPipeline.from_yaml(backtest_config)
        .with_materialized_replay_cache(tmp_path / "replay-cache")
        .build_engine()
    )
    cached = cached_engine.run_streaming(tmp_path / "cached", compact_events=True)

    baseline_manifest = json.loads(Path(baseline.manifest_path).read_text(encoding="utf-8"))
    cached_manifest = json.loads(Path(cached.manifest_path).read_text(encoding="utf-8"))

    assert cached.processed_bars == baseline.processed_bars
    assert cached.trading_bars == baseline.trading_bars
    assert cached_manifest["metrics"] == baseline_manifest["metrics"]
    assert list((tmp_path / "replay-cache").glob("*.jsonl"))


def test_pipeline_optimizer_config_accepts_materialized_replay_cache(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    from scripts import run_optimizer

    backtest_config, _ = _write_fixtures(tmp_path)
    calls: list[dict[str, Any]] = []

    class FakeRunner:
        def run(self, job: Any) -> tuple[Any, ...]:
            calls.append(
                {
                    "base_config_path": job.base_config_path,
                    "materialized_replay_cache_dir": job.materialized_replay_cache_dir,
                    "objective_metric": job.objective_metric,
                    "output_root": job.output_root,
                }
            )
            return ()

    monkeypatch.setattr(run_optimizer, "BacktestPipelineRunner", FakeRunner)

    results, objective_metric = run_optimizer._run_pipeline_path(
        {
            "backtest_config": str(backtest_config),
            "objective_metric": "total_return",
            "materialized_replay_cache": {
                "enabled": True,
                "cache_dir": "replay-cache",
            },
            "parameters": [{"name": "quantity", "values": ["1"]}],
        },
        output_root=tmp_path / "optimizer-runs",
        config_dir=tmp_path,
    )

    assert results == ()
    assert objective_metric == "total_return"
    assert calls == [
        {
            "base_config_path": backtest_config,
            "materialized_replay_cache_dir": (tmp_path / "replay-cache").resolve(),
            "objective_metric": "total_return",
            "output_root": tmp_path / "optimizer-runs",
        }
    ]
