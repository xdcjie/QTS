"""Historical VWAP factor research with relaxed trading-hour windows.

This research-only runner takes the strongest literature-inspired filters and
tests them across broader ET windows, including overnight half-open intervals.
It keeps production VWAP v2 untouched and uses short framework smoke checks for
the top proxy-ranked candidates.

New VWAP research should use ``scripts/run_research.py workflow`` with a
checked-in config under ``configs/research/workflows``. Keep this script only
for reproducing the historical relaxed-hours artifact set.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from scripts.research.run_vwap_20_round_proxy_research import (
    COST_ATR,
    dedup,
    exit_values,
    load_feature_bars,
    metrics,
)
from scripts.research.run_vwap_20_round_research import ARTIFACT_ROOT, DATA_CONFIG, REPO_ROOT
from scripts.research.run_vwap_literature_research import (
    add_literature_features,
    dollar_metrics,
    load_literature_signals,
    rule_mask,
    score_summary,
    select_is_exit,
)

OUT_CSV = ARTIFACT_ROOT / "vwap_relaxed_hours_research_summary.csv"
OUT_JSON = ARTIFACT_ROOT / "vwap_relaxed_hours_research_summary.json"
OUT_MD = ARTIFACT_ROOT / "vwap_relaxed_hours_research_summary.md"
OUT_RAW_CSV = ARTIFACT_ROOT / "vwap_relaxed_hours_research_raw.csv"
OUT_SEGMENTS_CSV = ARTIFACT_ROOT / "vwap_relaxed_hours_research_segments.csv"
SMOKE_CSV = ARTIFACT_ROOT / "vwap_relaxed_hours_framework_smoke.csv"
CONFIG_DIR = ARTIFACT_ROOT / "relaxed_hours_configs"
SMOKE_DIR = ARTIFACT_ROOT / "relaxed_hours_framework_smoke"

SMOKE_START = datetime(2025, 5, 5, tzinfo=UTC)
SMOKE_END = datetime(2025, 5, 8, tzinfo=UTC)
SMOKE_TOP_N = 20


@dataclass(frozen=True, slots=True)
class RelaxedCandidate:
    round_id: int
    name: str
    family: str
    thesis: str
    time_window: str
    rules: tuple[str, ...]
    params: dict[str, float]


def main() -> int:
    bars = add_literature_features(load_feature_bars())
    signals = load_literature_signals(bars)
    candidates = candidate_matrix()
    raw_rows, summary_rows, segment_rows = run_candidates(signals, candidates)
    smoke_rows = run_framework_smokes(summary_rows[:SMOKE_TOP_N], candidates)
    write_outputs(raw_rows, summary_rows, segment_rows, smoke_rows)
    return 0


def candidate_matrix() -> list[RelaxedCandidate]:
    windows = [
        ("full_session", "GC full session except 17:00-18:00 ET break."),
        ("overnight_18_06", "Overnight liquidity window 18:00-06:00 ET."),
        ("night_18_08", "Extended night window 18:00-08:00 ET."),
        ("asia_20_02", "Asia-heavy 20:00-02:00 ET window."),
        ("early_00_08", "Post-midnight to pre-RTH 00:00-08:00 ET window."),
        ("pre_rth_06_08", "Pre-RTH 06:00-08:00 ET window."),
        ("rth_08_17", "RTH-like broad 08:00-17:00 ET window."),
        ("day_08_14", "Morning/day 08:00-14:00 ET window."),
        ("late_12_17", "Late day 12:00-17:00 ET window."),
        ("avoid_06_08_14_17", "Full session excluding prior weak buckets."),
    ]
    factor_sets = [
        (
            "volume_high",
            "dynamic_volume",
            "Volume above same-minute expected curve.",
            ("volume_curve_range",),
            {"volume_min": 1.5, "volume_max": 5.0},
        ),
        ("ma50_200", "technical_rules", "MA 50/200 trend confirmation.", ("ma50_200_aligned",), {}),
        (
            "tsmom_60_120",
            "momentum",
            "60m and 120m time-series momentum agreement.",
            ("mom60_aligned", "mom120_aligned"),
            {},
        ),
        (
            "tsmom_120",
            "momentum",
            "120m time-series momentum confirmation.",
            ("mom120_aligned",),
            {},
        ),
        (
            "technical_score5",
            "technical_rules",
            "At least five technical confirmations.",
            ("technical_score_min",),
            {"score_min": 5.0},
        ),
        (
            "oscillator4",
            "technical_rules",
            "Four oscillator middle-regime confirmations.",
            ("oscillator_score_min",),
            {"score_min": 4.0},
        ),
        ("mfi_mid", "control", "Prior MFI middle-regime control.", ("mfi_mid",), {}),
        (
            "ma50_200_volume_high",
            "hybrid",
            "MA 50/200 plus high volume curve.",
            ("ma50_200_aligned", "volume_curve_range"),
            {"volume_min": 1.5, "volume_max": 5.0},
        ),
        (
            "tsmom_volume_high",
            "hybrid",
            "120m momentum plus high volume curve.",
            ("mom120_aligned", "volume_curve_range"),
            {"volume_min": 1.5, "volume_max": 5.0},
        ),
    ]

    candidates: list[RelaxedCandidate] = []
    round_id = 1
    for window, window_thesis in windows:
        for factor_name, family, factor_thesis, rules, params in factor_sets:
            candidates.append(
                RelaxedCandidate(
                    round_id=round_id,
                    name=f"{factor_name}_{window}",
                    family=family,
                    thesis=f"{factor_thesis} {window_thesis}",
                    time_window=window,
                    rules=rules,
                    params=params,
                )
            )
            round_id += 1
    return candidates


def run_candidates(
    signals: pd.DataFrame,
    candidates: list[RelaxedCandidate],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        frame = candidate_frame(signals, candidate)
        best = select_is_exit(frame)
        sample_rows: dict[str, dict[str, Any]] = {}
        for sample in ("IS", "OOS"):
            sample_frame = dedup(frame[frame["sample"] == sample])
            values = exit_values(sample_frame, best["stop_atr"], best["target_atr"], COST_ATR)
            metric = metrics(values)
            dollars = dollar_metrics(sample_frame, values)
            row = {
                "round": candidate.round_id,
                "candidate": candidate.name,
                "family": candidate.family,
                "sample": sample,
                "time_window": candidate.time_window,
                "thesis": candidate.thesis,
                "rules": ",".join(candidate.rules),
                "selected_stop_atr": best["stop_atr"],
                "selected_target_atr": best["target_atr"],
                "selected_is_score": best["score"],
                **metric,
                **dollars,
            }
            raw_rows.append(row)
            sample_rows[sample] = row
            segment_rows.extend(segment_metrics(candidate, sample_frame, best, sample=sample))
        is_row = sample_rows["IS"]
        oos_row = sample_rows["OOS"]
        summary_rows.append(
            {
                "round": candidate.round_id,
                "candidate": candidate.name,
                "family": candidate.family,
                "time_window": candidate.time_window,
                "thesis": candidate.thesis,
                "rules": ",".join(candidate.rules),
                "is_n": is_row["n"],
                "is_pnl_usd": is_row["pnl_usd"],
                "is_sharpe": is_row["proxy_sharpe"],
                "is_max_dd_usd": is_row["max_dd_usd"],
                "oos_n": oos_row["n"],
                "oos_pnl_usd": oos_row["pnl_usd"],
                "oos_sharpe": oos_row["proxy_sharpe"],
                "oos_max_dd_usd": oos_row["max_dd_usd"],
                "oos_profit_factor": oos_row["profit_factor"],
                "stop_atr": oos_row["selected_stop_atr"],
                "target_atr": oos_row["selected_target_atr"],
                "score": score_summary(is_row, oos_row),
            }
        )
    return (
        raw_rows,
        sorted(summary_rows, key=lambda item: float(item["score"]), reverse=True),
        segment_rows,
    )


def candidate_frame(signals: pd.DataFrame, candidate: RelaxedCandidate) -> pd.DataFrame:
    mode = "current_08_16" if candidate.time_window == "current_08_16" else "full_session_18_17"
    frame = signals[signals["mode"] == mode].copy()
    mask = time_window_mask(frame, candidate.time_window)
    for rule in candidate.rules:
        mask &= rule_mask(frame, rule, candidate.params)
    return frame[mask].sort_values("signal_time_utc").copy()


def time_window_mask(frame: pd.DataFrame, window: str) -> pd.Series:
    hour = frame["et_hour"].astype(int)
    bucket = frame["session_bucket"]
    if window == "full_session":
        return pd.Series(True, index=frame.index)
    if window == "avoid_06_08_14_17":
        return ~bucket.isin(["06-08", "14-16", "16-17"])
    intervals = {
        "overnight_18_06": (18, 6),
        "night_18_08": (18, 8),
        "asia_20_02": (20, 2),
        "early_00_08": (0, 8),
        "pre_rth_06_08": (6, 8),
        "rth_08_17": (8, 17),
        "day_08_14": (8, 14),
        "late_12_17": (12, 17),
    }
    if window not in intervals:
        raise ValueError(f"unknown relaxed time window: {window}")
    start, end = intervals[window]
    if start < end:
        return (hour >= start) & (hour < end)
    return (hour >= start) | (hour < end)


def segment_metrics(
    candidate: RelaxedCandidate,
    frame: pd.DataFrame,
    best: dict[str, float],
    *,
    sample: str,
) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    segmented = frame.copy()
    segmented["segment"] = segmented["signal_time_utc"].dt.strftime("%Y-%m")
    rows: list[dict[str, Any]] = []
    for segment, segment_frame in segmented.groupby("segment", sort=True):
        values = exit_values(segment_frame, best["stop_atr"], best["target_atr"], COST_ATR)
        metric = metrics(values)
        dollars = dollar_metrics(segment_frame, values)
        rows.append(
            {
                "round": candidate.round_id,
                "candidate": candidate.name,
                "family": candidate.family,
                "sample": sample,
                "time_window": candidate.time_window,
                "segment": segment,
                "n": metric["n"],
                "proxy_sharpe": metric["proxy_sharpe"],
                "pnl_usd": dollars["pnl_usd"],
                "max_dd_usd": dollars["max_dd_usd"],
            }
        )
    return rows


def run_framework_smokes(
    ranked_rows: list[dict[str, Any]],
    candidates: list[RelaxedCandidate],
) -> list[dict[str, Any]]:
    by_name = {candidate.name: candidate for candidate in candidates}
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT / "backend/src"), str(REPO_ROOT)])
    rows: list[dict[str, Any]] = []
    for ranked in ranked_rows:
        candidate = by_name[str(ranked["candidate"])]
        config_path = write_config(candidate)
        output_dir = SMOKE_DIR / f"{candidate.round_id:02d}_{candidate.name}"
        row = run_smoke(candidate, config_path, output_dir, env)
        rows.append(row)
        print(f"SMOKE {candidate.round_id:02d} {candidate.name}: {row['status']}")
    return rows


def write_config(candidate: RelaxedCandidate) -> Path:
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


def mapped_params(candidate: RelaxedCandidate) -> dict[str, object]:
    mapped: dict[str, object] = {}
    params = candidate.params
    if "volume_min" in params:
        mapped["volume_curve_ratio_min"] = str(params["volume_min"])
    if "volume_max" in params:
        mapped["volume_curve_ratio_max"] = str(params["volume_max"])
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
    candidate: RelaxedCandidate,
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
        "time_window": candidate.time_window,
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


def write_outputs(
    raw_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    segment_rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
) -> None:
    pd.DataFrame(raw_rows).to_csv(OUT_RAW_CSV, index=False)
    pd.DataFrame(summary_rows).to_csv(OUT_CSV, index=False)
    pd.DataFrame(segment_rows).to_csv(OUT_SEGMENTS_CSV, index=False)
    pd.DataFrame(smoke_rows).to_csv(SMOKE_CSV, index=False)
    OUT_JSON.write_text(
        json.dumps(
            {
                "method": {
                    "date": "2026-05-20",
                    "candidate_count": len(summary_rows),
                    "framework_smoke_top_n": SMOKE_TOP_N,
                    "exit_model": (
                        "60m dedup, IS-selected stop/target, conservative stop-first, 0.05 ATR cost"
                    ),
                },
                "ranked": summary_rows,
                "raw": raw_rows,
                "segments": segment_rows,
                "smoke": smoke_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    OUT_MD.write_text(markdown(summary_rows, smoke_rows), encoding="utf-8")


def markdown(summary_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> str:
    smoke_statuses = sorted({str(row["status"]) for row in smoke_rows})
    lines = [
        "# VWAP Relaxed-Hours Research",
        "",
        "Date: 2026-05-20",
        "",
        "## Method",
        "",
        "- Re-tested strongest VWAP factor families across broader ET windows.",
        "- Windows include full session, overnight 18-06, night 18-08, Asia 20-02, "
        "00-08, 06-08, 08-17, 08-14, 12-17, and prior weak-bucket exclusion.",
        "- Top proxy-ranked candidates receive short `scripts/run_backtest.py` smoke checks.",
        f"- Framework smoke statuses: {', '.join(smoke_statuses)}.",
        "",
        "## Ranked Results",
        "",
        "| Rank | Candidate | Window | OOS n | OOS PnL | OOS Sharpe | "
        "OOS MaxDD | IS PnL | Stop | Target |",
        "|---:|:---|:---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(summary_rows[:30], start=1):
        lines.append(
            f"| {rank} | {row['candidate']} | {row['time_window']} | {row['oos_n']} | "
            f"{row['oos_pnl_usd']:.2f} | {row['oos_sharpe']:.3f} | "
            f"{row['oos_max_dd_usd']:.2f} | {row['is_pnl_usd']:.2f} | "
            f"{row['stop_atr']:.1f} | {row['target_atr']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Summary CSV: `{OUT_CSV.relative_to(REPO_ROOT)}`",
            f"- Summary JSON: `{OUT_JSON.relative_to(REPO_ROOT)}`",
            f"- Raw CSV: `{OUT_RAW_CSV.relative_to(REPO_ROOT)}`",
            f"- Segments CSV: `{OUT_SEGMENTS_CSV.relative_to(REPO_ROOT)}`",
            f"- Framework smoke CSV: `{SMOKE_CSV.relative_to(REPO_ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
