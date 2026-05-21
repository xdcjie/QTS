"""Run 20 framework backtest rounds for VWAP factor research.

The script creates a research-only compact GC dataset for the requested
2024-2026 window, generates one config per candidate and sample split, runs
``scripts/run_backtest.py`` for every round, and writes summary artifacts.
"""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qts.data.historical.catalog import HistoricalCatalog, HistoricalCatalogLoadConfig
from qts.data.historical.csv_dataset import iter_historical_bars
from qts.registry.future_roll import (
    FirstNoticeDateFutureContractSelector,
    FutureContractRollSpec,
)
from qts.registry.providers.exchange_calendar_provider import ExchangeCalendarProvider

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = REPO_ROOT / "artifacts/analysis/vwap_20_round_2026-05-19"
DATA_CONFIG = ARTIFACT_ROOT / "historical.research.yaml"
COMPACT_HISTORY = ARTIFACT_ROOT / "historical/data/gc.csv"
COMPACT_CHAIN = ARTIFACT_ROOT / "historical/chains/GC.json"
CONFIG_DIR = ARTIFACT_ROOT / "configs"
RUNS_DIR = ARTIFACT_ROOT / "runs"
SUMMARY_CSV = ARTIFACT_ROOT / "vwap_20_round_backtest_summary.csv"
SUMMARY_JSON = ARTIFACT_ROOT / "vwap_20_round_backtest_summary.json"
SUMMARY_MD = ARTIFACT_ROOT / "vwap_20_round_backtest_summary.md"

START = datetime(2024, 5, 1, tzinfo=UTC)
SPLIT = datetime(2025, 5, 1, tzinfo=UTC)
END = datetime(2026, 4, 10, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class Candidate:
    round_id: int
    name: str
    thesis: str
    params: dict[str, object]


def main() -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    build_compact_history()
    write_data_config()
    candidates = candidate_matrix()
    rows: list[dict[str, object]] = []
    for candidate in candidates:
        for sample, start, end in (("IS", START, SPLIT), ("OOS", SPLIT, END)):
            config_path = write_backtest_config(candidate, sample=sample, start=start, end=end)
            rows.append(run_candidate(candidate, sample=sample, config_path=config_path))
            print(
                f"ROUND {candidate.round_id:02d} {sample} {candidate.name}: "
                f"{rows[-1].get('status')}"
            )
    write_summary(candidates, rows)
    return 0


def build_compact_history() -> None:
    if COMPACT_HISTORY.exists() and COMPACT_CHAIN.exists():
        return
    COMPACT_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    COMPACT_CHAIN.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO_ROOT / "historical/chains/GC.json", COMPACT_CHAIN)

    catalog = HistoricalCatalog.load(
        HistoricalCatalogLoadConfig.from_historical_market_data_config(
            REPO_ROOT / "configs/data/historical.local.yaml",
            catalog="research_futures",
            roots=("GC",),
            requested_timeframe="1m",
        )
    )
    dataset = catalog.datasets["GC"]
    if dataset.chain is None:
        raise RuntimeError("GC chain metadata is required")
    selector = FirstNoticeDateFutureContractSelector(
        contracts=tuple(
            FutureContractRollSpec(
                symbol=contract.symbol,
                instrument_id=dataset.chain.instrument_id_for_symbol(contract.symbol),
                first_notice_day=contract.first_notice_day,
                expiry=contract.expiry,
            )
            for contract in dataset.chain.contracts
        ),
        session_offset=ExchangeCalendarProvider(dataset.chain.trading_calendar).session_offset,
        active_months=dataset.chain.active_months,
        roll_sessions_before_first_notice=3,
    )
    stream = iter_historical_bars(
        dataset.csv_path,
        dataset.symbol_resolver,
        timeframe=dataset.source_timeframe or "1m",
        start=START,
        end=END,
        contract_selector=selector,
        session_window=dataset.chain.session_window(),
        schema=dataset.csv_schema,
    )
    with COMPACT_HISTORY.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "ts_event",
                "rtype",
                "publisher_id",
                "instrument_id",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "symbol",
            ),
        )
        writer.writeheader()
        for bar in stream:
            symbol = stream.roll_selections[-1].source_symbol if stream.roll_selections else "GC"
            writer.writerow(
                {
                    "ts_event": bar.start_time.isoformat().replace("+00:00", "Z"),
                    "rtype": "33",
                    "publisher_id": "1",
                    "instrument_id": bar.instrument_id.value,
                    "open": str(bar.open),
                    "high": str(bar.high),
                    "low": str(bar.low),
                    "close": str(bar.close),
                    "volume": str(bar.volume),
                    "symbol": symbol,
                }
            )


def write_data_config() -> None:
    payload = f"""historical_data:
  stores:
    vwap20_csv:
      type: local_csv
      root_dir: {ARTIFACT_ROOT.relative_to(REPO_ROOT)}/historical
      bars_dir: data
      chains_dir: chains
      defaults:
        schema: databento_ohlcv
        exchange_timezone: US/Eastern
        timezone_policy: source_utc_exchange_sessions
        normalization: raw-research-compact
  schemas:
    databento_ohlcv:
      timestamp: ts_event
      symbol: symbol
      instrument_id: instrument_id
      open: open
      high: high
      low: low
      close: close
      volume: volume
  catalogs:
    vwap20_research:
      store: vwap20_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
"""
    DATA_CONFIG.write_text(payload, encoding="utf-8")


def candidate_matrix() -> list[Candidate]:
    base: dict[str, object] = {
        "symbol": "GC",
        "target_quantity": "1",
        "vwap_slope_lookback": 5,
        "max_bars_in_wait_state": 5,
        "pullback_touch_atr_below": "0.2",
        "min_volume_ratio": "1.2",
    }

    def c(round_id: int, name: str, thesis: str, **params: object) -> Candidate:
        merged = dict(base)
        merged.update(params)
        return Candidate(round_id=round_id, name=name, thesis=thesis, params=merged)

    return [
        c(
            1,
            "baseline_current_08_16",
            "Current RTH-like VWAP v2 control.",
            time_window="current_08_16",
        ),
        c(2, "full_session", "Full GC session control.", time_window="full_session"),
        c(
            3,
            "avoid_bad_buckets",
            "Drop prior weak 06-08 and 14-17 ET buckets.",
            time_window="avoid_06_08_14_17",
        ),
        c(
            4,
            "evening_distance_mid_wide",
            "Evening trades with moderate VWAP distance.",
            time_window="evening_18_24",
            factor_filters=["distance_mid"],
            distance_min_atr="0.3",
            distance_max_atr="2.5",
        ),
        c(
            5,
            "evening_distance_mid_tight",
            "Evening trades with tighter VWAP distance.",
            time_window="evening_18_24",
            factor_filters=["distance_mid"],
            distance_min_atr="0.5",
            distance_max_atr="2.0",
        ),
        c(
            6,
            "evening_pressure_positive",
            "Evening positive Chaikin money-flow pressure.",
            time_window="evening_18_22",
            factor_filters=["cmf_positive"],
            cmf_min="0",
        ),
        c(
            7,
            "evening_pressure_aligned",
            "Evening direction-aligned money-flow pressure.",
            time_window="evening_18_22",
            factor_filters=["cmf_aligned"],
            cmf_min="0",
        ),
        c(
            8,
            "current_volume_le_180",
            "Current window without extreme volume spikes.",
            time_window="current_08_16",
            factor_filters=["volume_le"],
            volume_ratio_max="1.8",
        ),
        c(
            9,
            "current_volume_mid",
            "Current window medium participation only.",
            time_window="current_08_16",
            factor_filters=["volume_range"],
            volume_ratio_min="1.0",
            volume_ratio_max="1.8",
        ),
        c(
            10,
            "rth_open_drive_contra",
            "RTH open window contra/non-positive opening drive.",
            time_window="rth_08_12",
            factor_filters=["rth_drive_non_positive"],
        ),
        c(
            11,
            "rth_adx_aligned_18",
            "RTH trend-strength confirmation.",
            time_window="rth_08_12",
            factor_filters=["adx_aligned"],
            adx_min="18",
        ),
        c(
            12,
            "avoid_adx_aligned_20",
            "Full-session bad-bucket filter plus ADX alignment.",
            time_window="avoid_06_08_14_17",
            factor_filters=["adx_aligned"],
            adx_min="20",
        ),
        c(
            13,
            "evening_rsi_mid",
            "Evening VWAP pullback only when RSI is not extreme.",
            time_window="evening_18_24",
            factor_filters=["rsi_mid"],
            rsi_min="40",
            rsi_max="65",
        ),
        c(
            14,
            "evening_macd_aligned",
            "Evening VWAP pullback with MACD histogram alignment.",
            time_window="evening_18_24",
            factor_filters=["macd_aligned"],
        ),
        c(
            15,
            "evening_mfi_mid",
            "Evening money-flow index middle regime.",
            time_window="evening_18_24",
            factor_filters=["mfi_mid"],
            mfi_min="35",
            mfi_max="70",
        ),
        c(
            16,
            "avoid_bollinger_inside",
            "Avoid weak buckets and reject overextended Bollinger z-score.",
            time_window="avoid_06_08_14_17",
            factor_filters=["bollinger_inside"],
            max_bollinger_z_abs="1.25",
        ),
        c(
            17,
            "current_stochastic_mid",
            "Current window stochastic middle regime.",
            time_window="current_08_16",
            factor_filters=["stochastic_mid"],
            stochastic_min="25",
            stochastic_max="80",
        ),
        c(
            18,
            "current_cci_reversal",
            "Current window CCI pullback reversal.",
            time_window="current_08_16",
            factor_filters=["cci_reversal"],
            cci_abs_min="50",
        ),
        c(
            19,
            "evening_roc_aligned",
            "Evening rate-of-change aligned with VWAP direction.",
            time_window="evening_18_24",
            factor_filters=["roc_aligned"],
            roc_min_abs="0",
        ),
        c(
            20,
            "avoid_keltner_cmf",
            "Broad session filter plus Keltner containment and CMF alignment.",
            time_window="avoid_06_08_14_17",
            factor_filters=["keltner_inside", "cmf_aligned"],
            cmf_min="0",
        ),
    ]


def write_backtest_config(
    candidate: Candidate,
    *,
    sample: str,
    start: datetime,
    end: datetime,
) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CONFIG_DIR / f"{candidate.round_id:02d}_{candidate.name}_{sample.lower()}.yaml"
    params = yaml_mapping(candidate.params, indent=2)
    payload = f"""market_data:
  source: local_historical
  config: {DATA_CONFIG.relative_to(REPO_ROOT)}
  catalog: vwap20_research
roots:
  - GC
symbols:
  - GC
start: "{start.isoformat().replace("+00:00", "Z")}"
end: "{end.isoformat().replace("+00:00", "Z")}"
timeframe: 1m
initial_cash: "1000000"
strategy_class: examples.strategies.vwap_factor_research:VwapFactorResearchStrategy
strategy_params:
{params}
cost_model:
  fixed_commission_per_contract: "0"
  slippage_bps: "0"
risk_config:
  max_notional: "100000000"
roll_policy:
  enabled: true
  method: first_notice_date
  roll_sessions_before_first_notice: 3
warmup_bars: 80
"""
    config_path.write_text(payload, encoding="utf-8")
    return config_path


def yaml_mapping(payload: dict[str, object], *, indent: int) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in payload.items():
        if isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f'{prefix}  - "{item}"')
        elif isinstance(value, str):
            lines.append(f'{prefix}{key}: "{value}"')
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def run_candidate(candidate: Candidate, *, sample: str, config_path: Path) -> dict[str, object]:
    output_dir = RUNS_DIR / f"{candidate.round_id:02d}_{candidate.name}" / sample.lower()
    output_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    python_paths = [str(REPO_ROOT / "backend/src"), str(REPO_ROOT)]
    if env.get("PYTHONPATH"):
        python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_paths)
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/run_backtest.py"),
        "--config",
        str(config_path),
        "--output-dir",
        str(output_dir),
    ]
    row: dict[str, object] = {
        "round": candidate.round_id,
        "candidate": candidate.name,
        "sample": sample,
        "thesis": candidate.thesis,
        "config_path": str(config_path.relative_to(REPO_ROOT)),
        "status": "failed",
    }
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=240,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        row["status"] = "timeout"
        row["error"] = str(exc)
        return row
    row["stdout"] = completed.stdout.strip()
    row["stderr"] = completed.stderr.strip()
    row["returncode"] = completed.returncode
    if completed.returncode != 0:
        row["error"] = completed.stderr.strip()[-1000:]
        return row
    manifest_path = first_manifest_path(completed.stdout)
    if manifest_path is None:
        row["error"] = "manifest path missing from run_backtest output"
        return row
    row.update(metrics_from_manifest(manifest_path))
    row["manifest_path"] = str(manifest_path.relative_to(REPO_ROOT))
    row["status"] = "ok"
    return row


def first_manifest_path(stdout: str) -> Path | None:
    for line in stdout.splitlines():
        path = REPO_ROOT / line.strip()
        if path.name.endswith(".manifest.json") and path.exists():
            return path
    return None


def metrics_from_manifest(manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = manifest.get("metrics") or {}
    artifacts = manifest.get("artifacts") or {}
    equity_path = artifact_path(artifacts.get("equity_curve"))
    computed = compute_equity_metrics(equity_path) if equity_path else {}
    total_return = as_float(metrics.get("total_return")) or computed.get("total_return")
    max_drawdown = as_float(metrics.get("max_drawdown")) or computed.get("max_drawdown")
    sharpe = as_float(metrics.get("sharpe_ratio")) or computed.get("sharpe_ratio")
    return {
        "run_id": manifest.get("run_id"),
        "processed_bars": manifest.get("processed_bars"),
        "trading_bars": manifest.get("trading_bars"),
        "warmup_bars": manifest.get("warmup_bars"),
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe,
        "profit_factor": as_float(metrics.get("profit_factor")),
        "total_trades": as_int(metrics.get("total_trades"))
        or artifact_rows(artifacts.get("trade_ledger")),
        "total_orders": as_int(metrics.get("total_orders"))
        or artifact_rows(artifacts.get("orders")),
        "fills": artifact_rows(artifacts.get("fills")),
        "equity_points": artifact_rows(artifacts.get("equity_curve")),
    }


def artifact_path(payload: object) -> Path | None:
    if not isinstance(payload, dict):
        return None
    path = payload.get("path")
    if not isinstance(path, str):
        return None
    resolved = REPO_ROOT / path
    return resolved if resolved.exists() else None


def artifact_rows(payload: object) -> int | None:
    if not isinstance(payload, dict):
        return None
    rows = payload.get("rows")
    return as_int(rows)


def compute_equity_metrics(path: Path) -> dict[str, float | None]:
    values: list[float] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            equity = payload.get("equity")
            if equity is not None:
                values.append(float(equity))
    if len(values) < 2:
        return {"total_return": None, "max_drawdown": None, "sharpe_ratio": None}
    start = values[0]
    returns = [(values[index] / values[index - 1]) - 1 for index in range(1, len(values))]
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / max(len(returns) - 1, 1)
    std = math.sqrt(variance)
    peak = values[0]
    max_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        if peak:
            max_drawdown = min(max_drawdown, value / peak - 1)
    return {
        "total_return": values[-1] / start - 1 if start else None,
        "max_drawdown": abs(max_drawdown),
        "sharpe_ratio": (mean / std * math.sqrt(2520)) if std else None,
    }


def write_summary(candidates: list[Candidate], rows: list[dict[str, object]]) -> None:
    rows_by_key = {(row["round"], row["sample"]): row for row in rows}
    paired: list[dict[str, object]] = []
    for candidate in candidates:
        is_row = rows_by_key.get((candidate.round_id, "IS"), {})
        oos_row = rows_by_key.get((candidate.round_id, "OOS"), {})
        paired.append(
            {
                "round": candidate.round_id,
                "candidate": candidate.name,
                "thesis": candidate.thesis,
                "is_status": is_row.get("status"),
                "oos_status": oos_row.get("status"),
                "is_total_return": is_row.get("total_return"),
                "oos_total_return": oos_row.get("total_return"),
                "is_sharpe_ratio": is_row.get("sharpe_ratio"),
                "oos_sharpe_ratio": oos_row.get("sharpe_ratio"),
                "is_max_drawdown": is_row.get("max_drawdown"),
                "oos_max_drawdown": oos_row.get("max_drawdown"),
                "is_total_trades": is_row.get("total_trades"),
                "oos_total_trades": oos_row.get("total_trades"),
                "score": score(oos_row),
                "is_manifest_path": is_row.get("manifest_path"),
                "oos_manifest_path": oos_row.get("manifest_path"),
            }
        )
    paired.sort(
        key=lambda item: item["score"] if isinstance(item["score"], float) else -999, reverse=True
    )
    with SUMMARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(paired[0].keys()))
        writer.writeheader()
        writer.writerows(paired)
    SUMMARY_JSON.write_text(
        json.dumps(
            {
                "method": {
                    "rounds": len(candidates),
                    "is_window": [START.isoformat(), SPLIT.isoformat()],
                    "oos_window": [SPLIT.isoformat(), END.isoformat()],
                    "backtest_script": "scripts/run_backtest.py",
                    "strategy_class": (
                        "examples.strategies.vwap_factor_research:VwapFactorResearchStrategy"
                    ),
                    "compact_history": str(COMPACT_HISTORY.relative_to(REPO_ROOT)),
                    "selection_note": (
                        "Candidates are ranked by OOS for research reporting only; "
                        "production promotion still requires separate approval and "
                        "broader validation."
                    ),
                },
                "paired_results": paired,
                "raw_runs": rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    SUMMARY_MD.write_text(markdown_summary(paired), encoding="utf-8")


def score(row: dict[str, object]) -> float:
    if row.get("status") != "ok":
        return -999.0
    total_return = as_float(row.get("total_return")) or 0.0
    sharpe = as_float(row.get("sharpe_ratio")) or 0.0
    max_drawdown = as_float(row.get("max_drawdown")) or 0.0
    trades = as_float(row.get("total_trades")) or 0.0
    trade_penalty = 0.5 if trades < 5 else 0.0
    return total_return * 1000 + sharpe - max_drawdown * 100 - trade_penalty


def markdown_summary(paired: list[dict[str, object]]) -> str:
    lines = [
        "# VWAP 20-Round Framework Backtest Research",
        "",
        "Date: 2026-05-19",
        "",
        "## Scope",
        "",
        "- Framework path: generated configs are run through `scripts/run_backtest.py`.",
        "- Strategy path: `examples.strategies.vwap_factor_research:"
        "VwapFactorResearchStrategy` uses Strategy SDK indicators and target APIs.",
        "- Data path: research-only compact GC historical CSV preserves the configured "
        "chain/session/roll boundary for the 2024-05-01 to 2026-04-10 window.",
        "- No production runtime, risk, order, broker, or existing VWAP v2 trading logic "
        "is changed.",
        "",
        "## Ranked OOS Results",
        "",
        "| Rank | Round | Candidate | OOS Return | OOS Sharpe | OOS MaxDD | "
        "OOS Trades | IS Return | IS Sharpe |",
        "|---:|---:|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, item in enumerate(paired, start=1):
        lines.append(
            (
                "| {rank} | {round} | {candidate} | {oos_ret} | {oos_sharpe} | "
                "{oos_dd} | {oos_trades} | {is_ret} | {is_sharpe} |"
            ).format(
                rank=rank,
                round=item["round"],
                candidate=item["candidate"],
                oos_ret=fmt(item.get("oos_total_return")),
                oos_sharpe=fmt(item.get("oos_sharpe_ratio")),
                oos_dd=fmt(item.get("oos_max_drawdown")),
                oos_trades=item.get("oos_total_trades") or "",
                is_ret=fmt(item.get("is_total_return")),
                is_sharpe=fmt(item.get("is_sharpe_ratio")),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation Gate",
            "",
            "- A candidate is only a research winner if it improves OOS return/Sharpe "
            "without a worse drawdown profile and has enough trades to avoid one-off "
            "artifacts.",
            "- Any OOS-ranked result is still a hypothesis. Promotion into production "
            "strategy defaults requires a separate code review and broader validation.",
            "",
            "## Artifacts",
            "",
            f"- CSV summary: `{SUMMARY_CSV.relative_to(REPO_ROOT)}`",
            f"- JSON summary: `{SUMMARY_JSON.relative_to(REPO_ROOT)}`",
            f"- Generated configs: `{CONFIG_DIR.relative_to(REPO_ROOT)}`",
            f"- Backtest runs: `{RUNS_DIR.relative_to(REPO_ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def fmt(value: object) -> str:
    if value is None or value == "":
        return ""
    numeric = as_float(value)
    return "" if numeric is None else f"{numeric:.6f}"


def as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(Decimal(str(value)))
    except Exception:
        return None


def as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
