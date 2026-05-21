"""Fast 20-round VWAP factor research using compact bars and signal labels."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.research.run_vwap_20_round_research import (
    ARTIFACT_ROOT,
    REPO_ROOT,
    candidate_matrix,
    write_backtest_config,
    write_data_config,
)

SIGNALS = REPO_ROOT / "artifacts/analysis/vwap_full_session_audit_2026-05-19_signals.csv"
COMPACT_HISTORY = ARTIFACT_ROOT / "historical/data/gc.csv"
OUT_CSV = ARTIFACT_ROOT / "vwap_20_round_proxy_summary.csv"
OUT_JSON = ARTIFACT_ROOT / "vwap_20_round_proxy_summary.json"
OUT_MD = ARTIFACT_ROOT / "vwap_20_round_proxy_summary.md"
SMOKE_CSV = ARTIFACT_ROOT / "vwap_20_round_framework_smoke.csv"
SMOKE_DIR = ARTIFACT_ROOT / "framework_smoke"

STOPS = (1.5, 2.0, 2.5, 3.0, 4.0)
TARGETS = (2.0, 2.5, 3.0, 4.0, 5.0)
COST_ATR = 0.05


def main() -> int:
    write_data_config()
    bars = load_feature_bars()
    signals = load_signals(bars)
    round_rows = run_proxy_rounds(signals)
    smoke_rows = run_framework_smokes()
    write_outputs(round_rows, smoke_rows)
    return 0


def load_feature_bars() -> pd.DataFrame:
    bars = pd.read_csv(COMPACT_HISTORY)
    bars["signal_time_utc"] = pd.to_datetime(bars["ts_event"], utc=True)
    bars["close"] = bars["close"].astype(float)
    bars["open"] = bars["open"].astype(float)
    bars["high"] = bars["high"].astype(float)
    bars["low"] = bars["low"].astype(float)
    bars["volume"] = bars["volume"].astype(float)
    close = bars["close"]
    high = bars["high"]
    low = bars["low"]
    volume = bars["volume"]
    typical = (high + low + close) / 3.0

    bars["ret_15"] = close.pct_change(15)
    bars["roc_15"] = close.pct_change(15) * 100.0
    bars["ema_12"] = close.ewm(span=12, adjust=False, min_periods=12).mean()
    bars["ema_26"] = close.ewm(span=26, adjust=False, min_periods=26).mean()
    macd = bars["ema_12"] - bars["ema_26"]
    bars["macd_hist"] = macd - macd.ewm(span=9, adjust=False, min_periods=9).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta.clip(upper=0)).fillna(0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    bars["rsi_14"] = 100 - (100 / (1 + rs))
    bars.loc[avg_loss == 0, "rsi_14"] = 100

    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean() / atr
    minus_di = (
        100 * pd.Series(minus_dm).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean() / atr
    )
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100
    bars["adx_14"] = dx.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    bars["di_delta"] = plus_di - minus_di
    bars["atr_14"] = atr

    raw_money = typical * volume
    pos_flow = raw_money.where(typical > typical.shift(1), 0.0)
    neg_flow = raw_money.where(typical < typical.shift(1), 0.0)
    pos_sum = pos_flow.rolling(14, min_periods=14).sum()
    neg_sum = neg_flow.rolling(14, min_periods=14).sum()
    money_ratio = pos_sum / neg_sum.replace(0, np.nan)
    bars["mfi_14"] = 100 - (100 / (1 + money_ratio))

    mf_multiplier = (((close - low) - (high - close)) / (high - low).replace(0, np.nan)).fillna(0)
    mf_volume = mf_multiplier * volume
    bars["cmf_20"] = (
        mf_volume.rolling(20, min_periods=20).sum() / volume.rolling(20, min_periods=20).sum()
    )

    middle = close.rolling(20, min_periods=20).mean()
    std = close.rolling(20, min_periods=20).std(ddof=0)
    bars["bollinger_z"] = (close - middle) / std.replace(0, np.nan)

    don_high = high.rolling(20, min_periods=20).max()
    don_low = low.rolling(20, min_periods=20).min()
    bars["donchian_pos"] = (close - ((don_high + don_low) / 2.0)) / (don_high - don_low).replace(
        0, np.nan
    )
    keltner_mid = close.ewm(span=20, adjust=False, min_periods=20).mean()
    keltner_atr = tr.ewm(alpha=1 / 20, adjust=False, min_periods=20).mean()
    bars["keltner_inside"] = (close >= keltner_mid - 2 * keltner_atr) & (
        close <= keltner_mid + 2 * keltner_atr
    )

    stoch_low = low.rolling(14, min_periods=14).min()
    stoch_high = high.rolling(14, min_periods=14).max()
    bars["stochastic_k"] = ((close - stoch_low) / (stoch_high - stoch_low).replace(0, np.nan)) * 100
    bars["williams_r"] = ((stoch_high - close) / (stoch_high - stoch_low).replace(0, np.nan)) * -100

    tp_mean = typical.rolling(20, min_periods=20).mean()
    mean_dev = typical.rolling(20, min_periods=20).apply(
        lambda values: float(np.mean(np.abs(values - np.mean(values)))),
        raw=True,
    )
    bars["cci_20"] = (typical - tp_mean) / (0.015 * mean_dev.replace(0, np.nan))
    abs_returns = close.diff().abs().rolling(20, min_periods=20).sum()
    bars["efficiency_20"] = (close - close.shift(20)).abs() / abs_returns.replace(0, np.nan)
    return bars


def load_signals(bars: pd.DataFrame) -> pd.DataFrame:
    signals = pd.read_csv(SIGNALS)
    signals["signal_time_utc"] = pd.to_datetime(signals["signal_time_utc"], utc=True)
    merged = signals.merge(
        bars[
            [
                "signal_time_utc",
                "symbol",
                "macd_hist",
                "rsi_14",
                "adx_14",
                "di_delta",
                "mfi_14",
                "cmf_20",
                "roc_15",
                "bollinger_z",
                "donchian_pos",
                "keltner_inside",
                "stochastic_k",
                "williams_r",
                "cci_20",
                "efficiency_20",
            ]
        ],
        on=["signal_time_utc", "symbol"],
        how="left",
    )
    merged["dir_sign"] = np.where(merged["direction"] == "long", 1.0, -1.0)
    return merged


def run_proxy_rounds(signals: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidate_matrix():
        candidate_signals = candidate_frame(signals, candidate)
        best = select_is_exit(candidate_signals)
        for sample in ("IS", "OOS"):
            frame = dedup(candidate_signals[candidate_signals["sample"] == sample])
            values = exit_values(frame, best["stop_atr"], best["target_atr"], COST_ATR)
            metric = metrics(values)
            rows.append(
                {
                    "round": candidate.round_id,
                    "candidate": candidate.name,
                    "sample": sample,
                    "thesis": candidate.thesis,
                    "selected_stop_atr": best["stop_atr"],
                    "selected_target_atr": best["target_atr"],
                    "selected_is_score": best["score"],
                    **metric,
                }
            )
    return rows


def candidate_frame(signals: pd.DataFrame, candidate: Any) -> pd.DataFrame:
    if candidate.name == "baseline_current_08_16":
        frame = signals[signals["mode"] == "current_08_16"].copy()
    else:
        frame = signals[signals["mode"] == "full_session_18_17"].copy()
    params = candidate.params
    mask = time_mask(frame, str(params.get("time_window", "full_session")))
    for filter_name in params.get("factor_filters", ()):
        mask &= factor_mask(frame, str(filter_name), params)
    return frame[mask].sort_values("signal_time_utc").copy()


def time_mask(frame: pd.DataFrame, window: str) -> pd.Series:
    bucket = frame["session_bucket"]
    if window == "full_session":
        return pd.Series(True, index=frame.index)
    if window == "current_08_16" or window == "bucket_08_16_full_anchor":
        return bucket.isin(["08-10", "10-12", "12-14", "14-16"])
    if window == "evening_18_24":
        return bucket.isin(["18-22", "22-24"])
    if window == "evening_18_22":
        return bucket.eq("18-22")
    if window == "rth_08_12":
        return bucket.isin(["08-10", "10-12"])
    if window == "avoid_06_08_14_17":
        return ~bucket.isin(["06-08", "14-16", "16-17"])
    raise ValueError(f"unknown time window: {window}")


def factor_mask(frame: pd.DataFrame, filter_name: str, params: dict[str, object]) -> pd.Series:
    direction = frame["dir_sign"]
    if filter_name == "distance_mid":
        return frame["close_distance_vwap_atr"].between(
            param_float(params, "distance_min_atr", 0.0),
            param_float(params, "distance_max_atr", 99.0),
        )
    if filter_name == "volume_range":
        return frame["volume_ratio"].between(
            param_float(params, "volume_ratio_min", 0.0),
            param_float(params, "volume_ratio_max", 99.0),
        )
    if filter_name == "volume_le":
        return frame["volume_ratio"] <= param_float(params, "volume_ratio_max", 99.0)
    if filter_name == "rth_drive_non_positive":
        return direction * frame["rth_first_hour_return_atr_aligned"] <= 0
    if filter_name == "adx_aligned":
        return (frame["adx_14"] >= param_float(params, "adx_min", 18.0)) & (
            direction * frame["di_delta"] > 0
        )
    if filter_name == "rsi_mid":
        return frame["rsi_14"].between(
            param_float(params, "rsi_min", 35.0), param_float(params, "rsi_max", 65.0)
        )
    if filter_name == "macd_aligned":
        return direction * frame["macd_hist"] > 0
    if filter_name == "cmf_positive":
        return frame["cmf_20"] > param_float(params, "cmf_min", 0.0)
    if filter_name == "cmf_aligned":
        return direction * frame["cmf_20"] > param_float(params, "cmf_min", 0.0)
    if filter_name == "mfi_mid":
        return frame["mfi_14"].between(
            param_float(params, "mfi_min", 35.0), param_float(params, "mfi_max", 70.0)
        )
    if filter_name == "bollinger_inside":
        return frame["bollinger_z"].abs() <= param_float(params, "max_bollinger_z_abs", 1.5)
    if filter_name == "stochastic_mid":
        return frame["stochastic_k"].between(
            param_float(params, "stochastic_min", 20.0),
            param_float(params, "stochastic_max", 80.0),
        )
    if filter_name == "cci_reversal":
        return direction * frame["cci_20"] <= -param_float(params, "cci_abs_min", 50.0)
    if filter_name == "roc_aligned":
        return direction * frame["roc_15"] >= param_float(params, "roc_min_abs", 0.0)
    if filter_name == "keltner_inside":
        return frame["keltner_inside"].fillna(False)
    raise ValueError(f"unknown filter: {filter_name}")


def select_is_exit(frame: pd.DataFrame) -> dict[str, float]:
    is_frame = dedup(frame[frame["sample"] == "IS"])
    best = {"stop_atr": 2.0, "target_atr": 5.0, "score": -999.0}
    if len(is_frame) < 10:
        return best
    for stop in STOPS:
        for target in TARGETS:
            values = exit_values(is_frame, stop, target, COST_ATR)
            metric = metrics(values)
            score = (
                metric_float(metric, "proxy_sharpe")
                + metric_float(metric, "mean")
                - abs(metric_float(metric, "max_dd")) * 0.03
            )
            if score > best["score"]:
                best = {"stop_atr": stop, "target_atr": target, "score": score}
    return best


def param_float(params: dict[str, object], key: str, default: float) -> float:
    value = params.get(key, default)
    return float(str(value))


def metric_float(metric: dict[str, float | int | None], key: str) -> float:
    value = metric.get(key)
    return float(value) if value is not None else 0.0


def dedup(frame: pd.DataFrame, minutes: int = 60) -> pd.DataFrame:
    kept: list[int] = []
    last = None
    for idx, row in frame.sort_values("signal_time_utc").iterrows():
        ts = row["signal_time_utc"]
        if last is None or ts >= last + pd.Timedelta(minutes=minutes):
            kept.append(idx)
            last = ts
    return frame.loc[kept].copy()


def exit_values(frame: pd.DataFrame, stop: float, target: float, cost: float) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=float)
    values = frame["fwd_60m_atr"].astype(float).copy()
    hit_stop = frame["mae_60m_atr"].astype(float) >= stop
    hit_target = frame["mfe_60m_atr"].astype(float) >= target
    values[hit_stop] = -stop
    values[(~hit_stop) & hit_target] = target
    return values - cost


def metrics(values: pd.Series) -> dict[str, float | int | None]:
    values = values.dropna().astype(float)
    n = int(len(values))
    if n == 0:
        return {
            "n": 0,
            "mean": 0.0,
            "median": 0.0,
            "win_rate": 0.0,
            "proxy_sharpe": 0.0,
            "cum_atr": 0.0,
            "max_dd": 0.0,
            "profit_factor": None,
        }
    std = values.std(ddof=1)
    gains = values[values > 0].sum()
    losses = -values[values < 0].sum()
    curve = values.cumsum()
    drawdown = curve - curve.cummax()
    return {
        "n": n,
        "mean": float(values.mean()),
        "median": float(values.median()),
        "win_rate": float((values > 0).mean()),
        "proxy_sharpe": float(values.mean() / std * math.sqrt(n)) if std else 0.0,
        "cum_atr": float(values.sum()),
        "max_dd": float(drawdown.min()),
        "profit_factor": float(gains / losses) if losses > 0 else None,
    }


def run_framework_smokes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(REPO_ROOT / "backend/src"), str(REPO_ROOT)])
    for candidate in candidate_matrix():
        config_path = write_backtest_config(
            candidate,
            sample="SMOKE",
            start=pd.Timestamp("2025-05-05T00:00:00Z").to_pydatetime(),
            end=pd.Timestamp("2025-05-08T00:00:00Z").to_pydatetime(),
        )
        output_dir = SMOKE_DIR / f"{candidate.round_id:02d}_{candidate.name}"
        cmd = [
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
            "status": "failed",
        }
        try:
            completed = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                env=env,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired:
            row["status"] = "timeout"
            rows.append(row)
            print(f"SMOKE {candidate.round_id:02d} {candidate.name}: timeout")
            continue
        row["returncode"] = completed.returncode
        row["status"] = "ok" if completed.returncode == 0 else "failed"
        row["stderr_tail"] = completed.stderr[-500:]
        rows.append(row)
        print(f"SMOKE {candidate.round_id:02d} {candidate.name}: {row['status']}")
    pd.DataFrame(rows).to_csv(SMOKE_CSV, index=False)
    return rows


def write_outputs(round_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]]) -> None:
    raw = pd.DataFrame(round_rows)
    pivot_rows = []
    for candidate in candidate_matrix():
        is_row = raw[(raw["round"] == candidate.round_id) & (raw["sample"] == "IS")].iloc[0]
        oos_row = raw[(raw["round"] == candidate.round_id) & (raw["sample"] == "OOS")].iloc[0]
        smoke = next(row for row in smoke_rows if row["round"] == candidate.round_id)
        score = (
            float(oos_row["proxy_sharpe"])
            + float(oos_row["mean"])
            - abs(float(oos_row["max_dd"])) * 0.03
            - (0.5 if float(oos_row["n"]) < 25 else 0)
        )
        pivot_rows.append(
            {
                "round": candidate.round_id,
                "candidate": candidate.name,
                "thesis": candidate.thesis,
                "is_n": int(is_row["n"]),
                "is_mean": float(is_row["mean"]),
                "is_sharpe": float(is_row["proxy_sharpe"]),
                "is_max_dd": float(is_row["max_dd"]),
                "oos_n": int(oos_row["n"]),
                "oos_mean": float(oos_row["mean"]),
                "oos_sharpe": float(oos_row["proxy_sharpe"]),
                "oos_max_dd": float(oos_row["max_dd"]),
                "oos_profit_factor": oos_row["profit_factor"],
                "stop_atr": float(oos_row["selected_stop_atr"]),
                "target_atr": float(oos_row["selected_target_atr"]),
                "framework_smoke_status": smoke["status"],
                "score": score,
            }
        )
    summary = pd.DataFrame(pivot_rows).sort_values("score", ascending=False)
    summary.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(
        json.dumps(
            {
                "method": {
                    "rounds": 20,
                    "source_signals": str(SIGNALS.relative_to(REPO_ROOT)),
                    "compact_history": str(COMPACT_HISTORY.relative_to(REPO_ROOT)),
                    "exit_model": (
                        "60m dedup, IS-selected stop/target, conservative stop-first, 0.05 ATR cost"
                    ),
                    "framework_smoke": str(SMOKE_CSV.relative_to(REPO_ROOT)),
                },
                "ranked": summary.to_dict("records"),
                "raw": round_rows,
                "smoke": smoke_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    OUT_MD.write_text(markdown(summary), encoding="utf-8")


def markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# VWAP 20-Round Factor Exploration",
        "",
        "Date: 2026-05-19",
        "",
        "## Method",
        "",
        "- 20 rounds completed with non-VWAP indicators combined with VWAP pullback signals.",
        "- Indicators are computed from compact GC 1m bars; signal selection uses "
        "existing VWAP full-session/current signal labels.",
        "- Exit proxy: 60-minute cooldown, IS-selected stop/target, conservative "
        "stop-first, 0.05 ATR cost.",
        "- Framework gate: each round also receives a short-window "
        "`scripts/run_backtest.py` smoke run using `VwapFactorResearchStrategy`.",
        "",
        "## Ranked Results",
        "",
        "| Rank | Round | Candidate | OOS n | OOS Mean | OOS Sharpe | "
        "OOS MaxDD | PF | Stop | Target | Framework Smoke |",
        "|---:|---:|:---|---:|---:|---:|---:|---:|---:|---:|:---|",
    ]
    for rank, row in enumerate(summary.to_dict("records"), start=1):
        lines.append(
            f"| {rank} | {row['round']} | {row['candidate']} | {row['oos_n']} | "
            f"{row['oos_mean']:.3f} | {row['oos_sharpe']:.3f} | {row['oos_max_dd']:.3f} | "
            f"{float(row['oos_profit_factor']):.3f} | {row['stop_atr']:.1f} | "
            f"{row['target_atr']:.1f} | {row['framework_smoke_status']} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Summary CSV: `{OUT_CSV.relative_to(REPO_ROOT)}`",
            f"- Summary JSON: `{OUT_JSON.relative_to(REPO_ROOT)}`",
            f"- Framework smoke CSV: `{SMOKE_CSV.relative_to(REPO_ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
