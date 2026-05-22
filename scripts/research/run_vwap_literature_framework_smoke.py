"""Historical smoke runner for literature-inspired VWAP candidates.

New VWAP research should use ``scripts/run_research.py workflow`` with a
checked-in config under ``configs/research/workflows``. Keep this script only
for reproducing the historical literature smoke artifacts.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.research.run_vwap_20_round_research import ARTIFACT_ROOT, DATA_CONFIG, REPO_ROOT
from scripts.research.run_vwap_literature_research import LiteratureCandidate, candidate_matrix

CONFIG_DIR = ARTIFACT_ROOT / "literature_configs"
SMOKE_DIR = ARTIFACT_ROOT / "literature_framework_smoke"
SMOKE_CSV = ARTIFACT_ROOT / "vwap_literature_framework_smoke.csv"

SMOKE_START = datetime(2025, 5, 5, tzinfo=UTC)
SMOKE_END = datetime(2025, 5, 8, tzinfo=UTC)


def main() -> int:
    rows: list[dict[str, Any]] = []
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT / "backend/src"), str(REPO_ROOT)])
    for candidate in candidate_matrix():
        config_path = write_config(candidate)
        output_dir = SMOKE_DIR / f"{candidate.round_id:02d}_{candidate.name}"
        row = run_smoke(candidate, config_path, output_dir, env)
        rows.append(row)
        print(f"SMOKE {candidate.round_id:02d} {candidate.name}: {row['status']}")
    SMOKE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with SMOKE_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return 0


def write_config(candidate: LiteratureCandidate) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_path = CONFIG_DIR / f"{candidate.round_id:02d}_{candidate.name}_smoke.yaml"
    params = {
        "symbol": "GC",
        "target_quantity": "1",
        "vwap_slope_lookback": 5,
        "max_bars_in_wait_state": 5,
        "pullback_touch_atr_below": "0.2",
        "min_volume_ratio": "1.2",
        "time_window": candidate.time_window,
        "factor_filters": list(candidate.rules),
    }
    params.update(mapped_params(candidate))
    payload = f"""market_data:
  source: local_historical
  config: {DATA_CONFIG.relative_to(REPO_ROOT)}
  catalog: vwap20_research
roots:
  - GC
symbols:
  - GC
start: "{SMOKE_START.isoformat().replace("+00:00", "Z")}"
end: "{SMOKE_END.isoformat().replace("+00:00", "Z")}"
timeframe: 1m
initial_cash: "1000000"
strategy_class: strategies.research.vwap_factor_research:VwapFactorResearchStrategy
strategy_params:
{yaml_mapping(params, indent=2)}
cost_model:
  fixed_commission_per_contract: "0"
  slippage_bps: "0"
risk_config:
  max_notional: "100000000"
roll_policy:
  enabled: true
  method: first_notice_date
  roll_sessions_before_first_notice: 3
warmup_bars: 240
"""
    config_path.write_text(payload, encoding="utf-8")
    return config_path


def mapped_params(candidate: LiteratureCandidate) -> dict[str, object]:
    mapped: dict[str, object] = {}
    params = candidate.params
    if "volume_min" in params:
        mapped["volume_curve_ratio_min"] = str(params["volume_min"])
    if "volume_max" in params:
        mapped["volume_curve_ratio_max"] = str(params["volume_max"])
    if "distance_min" in params:
        mapped["distance_min_atr"] = str(params["distance_min"])
    if "distance_max" in params:
        mapped["distance_max_atr"] = str(params["distance_max"])
    if "mom_min" in params:
        mapped["ts_momentum_min_abs"] = str(params["mom_min"])
    if "score_min" in params and "technical_score_min" in candidate.rules:
        mapped["technical_score_min"] = int(params["score_min"])
    if "score_min" in params and "oscillator_score_min" in candidate.rules:
        mapped["oscillator_score_min"] = int(params["score_min"])
    return mapped


def yaml_mapping(payload: dict[str, object], *, indent: int) -> str:
    prefix = " " * indent
    lines: list[str] = []
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


def run_smoke(
    candidate: LiteratureCandidate,
    config_path: Path,
    output_dir: Path,
    env: dict[str, str],
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(REPO_ROOT / "scripts/run_backtest.py"),
        "--config",
        str(config_path),
        "--output-dir",
        str(output_dir),
    ]
    row: dict[str, Any] = {
        "round": candidate.round_id,
        "candidate": candidate.name,
        "family": candidate.family,
        "status": "failed",
        "config_path": str(config_path.relative_to(REPO_ROOT)),
    }
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        row["status"] = "timeout"
        return row
    row["returncode"] = completed.returncode
    row["status"] = "ok" if completed.returncode == 0 else "failed"
    row["stderr_tail"] = completed.stderr[-500:]
    manifest_path = first_manifest_path(completed.stdout)
    if manifest_path is not None:
        row.update(metrics_from_manifest(manifest_path))
        row["manifest_path"] = str(manifest_path.relative_to(REPO_ROOT))
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
    return {
        "total_return": metrics.get("total_return"),
        "sharpe_ratio": metrics.get("sharpe_ratio"),
        "max_drawdown": metrics.get("max_drawdown"),
        "total_trades": metrics.get("total_trades"),
        "profit_factor": metrics.get("profit_factor"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
