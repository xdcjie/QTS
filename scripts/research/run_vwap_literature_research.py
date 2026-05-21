"""Literature-inspired VWAP factor research.

This research-only script extends the previous VWAP signal labels with three
families of ideas:

* time-series momentum style continuation filters,
* technical-rule confirmation and oscillator consensus,
* dynamic intraday volume-curve/VWAP distance filters.

It does not change production strategy logic. Candidate exits are selected on
IS only and evaluated on OOS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.research.run_vwap_20_round_proxy_research import (
    COST_ATR,
    STOPS,
    TARGETS,
    dedup,
    exit_values,
    load_feature_bars,
    load_signals,
    metric_float,
    metrics,
    time_mask,
)
from scripts.research.run_vwap_20_round_proxy_research import (
    OUT_JSON as PRIOR_PROXY_JSON,
)
from scripts.research.run_vwap_20_round_research import ARTIFACT_ROOT, REPO_ROOT

OUT_CSV = ARTIFACT_ROOT / "vwap_literature_research_summary.csv"
OUT_JSON = ARTIFACT_ROOT / "vwap_literature_research_summary.json"
OUT_MD = ARTIFACT_ROOT / "vwap_literature_research_summary.md"
OUT_RAW_CSV = ARTIFACT_ROOT / "vwap_literature_research_raw.csv"
OUT_SEGMENTS_CSV = ARTIFACT_ROOT / "vwap_literature_research_segments.csv"

GC_MULTIPLIER = 100.0


@dataclass(frozen=True, slots=True)
class LiteratureCandidate:
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
    raw_rows, summary_rows, segment_rows = run_candidates(signals)
    write_outputs(raw_rows, summary_rows, segment_rows)
    return 0


def add_literature_features(bars: pd.DataFrame) -> pd.DataFrame:
    frame = bars.sort_values("signal_time_utc").copy()
    et = frame["signal_time_utc"].dt.tz_convert("US/Eastern")
    frame["et_minute"] = et.dt.hour * 60 + et.dt.minute
    close = frame["close"].astype(float)
    high = frame["high"].astype(float)
    low = frame["low"].astype(float)
    volume = frame["volume"].astype(float)
    atr = frame["atr_14"].astype(float).replace(0, np.nan)

    for window in (60, 120, 240):
        frame[f"mom_{window}_atr"] = (close - close.shift(window)) / atr

    frame["sma_20"] = close.rolling(20, min_periods=20).mean()
    frame["sma_80"] = close.rolling(80, min_periods=80).mean()
    frame["sma_50"] = close.rolling(50, min_periods=50).mean()
    frame["sma_200"] = close.rolling(200, min_periods=200).mean()
    frame["ma_20_80_atr"] = (frame["sma_20"] - frame["sma_80"]) / atr
    frame["ma_50_200_atr"] = (frame["sma_50"] - frame["sma_200"]) / atr

    don_high_60 = high.rolling(60, min_periods=60).max()
    don_low_60 = low.rolling(60, min_periods=60).min()
    frame["donchian_pos_60"] = (close - ((don_high_60 + don_low_60) / 2.0)) / (
        don_high_60 - don_low_60
    ).replace(0, np.nan)

    curve_mean = frame.groupby("et_minute")["volume"].transform(
        lambda values: values.shift(1).rolling(20, min_periods=5).mean()
    )
    frame["volume_curve_ratio"] = volume / curve_mean.replace(0, np.nan)
    return frame


def load_literature_signals(bars: pd.DataFrame) -> pd.DataFrame:
    signals = load_signals(bars)
    feature_cols = [
        "signal_time_utc",
        "symbol",
        "mom_60_atr",
        "mom_120_atr",
        "mom_240_atr",
        "ma_20_80_atr",
        "ma_50_200_atr",
        "donchian_pos_60",
        "volume_curve_ratio",
    ]
    merged = signals.merge(
        bars[feature_cols],
        on=["signal_time_utc", "symbol"],
        how="left",
    )
    direction = merged["dir_sign"]
    merged["technical_score"] = (
        (direction * merged["macd_hist"] > 0).astype(int)
        + ((merged["adx_14"] >= 18) & (direction * merged["di_delta"] > 0)).astype(int)
        + (direction * merged["roc_15"] > 0).astype(int)
        + (direction * merged["mom_60_atr"] > 0).astype(int)
        + (direction * merged["ma_20_80_atr"] > 0).astype(int)
        + (direction * merged["donchian_pos_60"] > 0).astype(int)
        + merged["rsi_14"].between(40, 65).astype(int)
        + merged["mfi_14"].between(35, 70).astype(int)
    )
    merged["oscillator_mid_score"] = (
        merged["rsi_14"].between(40, 65).astype(int)
        + merged["mfi_14"].between(35, 70).astype(int)
        + merged["stochastic_k"].between(20, 80).astype(int)
        + merged["williams_r"].between(-80, -20).astype(int)
    )
    return merged


def candidate_matrix() -> list[LiteratureCandidate]:
    def c(
        round_id: int,
        name: str,
        family: str,
        thesis: str,
        time_window: str,
        *rules: str,
        **params: float,
    ) -> LiteratureCandidate:
        return LiteratureCandidate(
            round_id=round_id,
            name=name,
            family=family,
            thesis=thesis,
            time_window=time_window,
            rules=tuple(rules),
            params=params,
        )

    return [
        c(
            1,
            "control_evening_mfi",
            "control",
            "Prior best OOS proxy control.",
            "evening_18_24",
            "mfi_mid",
        ),
        c(
            2,
            "control_evening_rsi",
            "control",
            "Prior drawdown-score control.",
            "evening_18_24",
            "rsi_mid",
        ),
        c(
            3,
            "tsmom_60_evening",
            "momentum",
            "One-hour continuation aligned with VWAP rejection.",
            "evening_18_24",
            "mom60_aligned",
        ),
        c(
            4,
            "tsmom_120_evening",
            "momentum",
            "Two-hour continuation aligned with VWAP rejection.",
            "evening_18_24",
            "mom120_aligned",
        ),
        c(
            5,
            "tsmom_240_evening",
            "momentum",
            "Four-hour continuation aligned with VWAP rejection.",
            "evening_18_24",
            "mom240_aligned",
        ),
        c(
            6,
            "tsmom_60_120_agree",
            "momentum",
            "One- and two-hour continuation agree.",
            "evening_18_24",
            "mom60_aligned",
            "mom120_aligned",
        ),
        c(
            7,
            "tsmom_120_strong",
            "momentum",
            "Two-hour continuation must exceed 0.5 ATR.",
            "evening_18_24",
            "mom120_min",
            mom_min=0.5,
        ),
        c(
            8,
            "ma_20_80_evening",
            "technical_rules",
            "MA 20/80 trend rule confirmation.",
            "evening_18_24",
            "ma20_80_aligned",
        ),
        c(
            9,
            "ma_50_200_evening",
            "technical_rules",
            "MA 50/200 trend rule confirmation.",
            "evening_18_24",
            "ma50_200_aligned",
        ),
        c(
            10,
            "tech_score_4_evening",
            "technical_rules",
            "At least four technical confirmations.",
            "evening_18_24",
            "technical_score_min",
            score_min=4,
        ),
        c(
            11,
            "tech_score_5_evening",
            "technical_rules",
            "At least five technical confirmations.",
            "evening_18_24",
            "technical_score_min",
            score_min=5,
        ),
        c(
            12,
            "oscillator_consensus",
            "technical_rules",
            "RSI/MFI/Stochastic/Williams middle regime.",
            "evening_18_24",
            "oscillator_score_min",
            score_min=4,
        ),
        c(
            13,
            "volume_curve_normal",
            "dynamic_volume",
            "Same-minute volume near expected curve.",
            "evening_18_24",
            "volume_curve_range",
            volume_min=0.6,
            volume_max=1.8,
        ),
        c(
            14,
            "volume_curve_high",
            "dynamic_volume",
            "Same-minute volume above expected curve.",
            "evening_18_24",
            "volume_curve_range",
            volume_min=1.5,
            volume_max=5.0,
        ),
        c(
            15,
            "volume_curve_distance",
            "dynamic_volume",
            "Normal curve volume with moderate VWAP distance.",
            "evening_18_24",
            "volume_curve_range",
            "distance_mid",
            volume_min=0.6,
            volume_max=1.8,
            distance_min=0.3,
            distance_max=2.5,
        ),
        c(
            16,
            "mfi_volume_curve",
            "hybrid",
            "MFI middle regime plus normal volume curve.",
            "evening_18_24",
            "mfi_mid",
            "volume_curve_range",
            volume_min=0.6,
            volume_max=1.8,
        ),
        c(
            17,
            "mfi_tsmom_120",
            "hybrid",
            "MFI middle regime plus two-hour momentum.",
            "evening_18_24",
            "mfi_mid",
            "mom120_aligned",
        ),
        c(
            18,
            "rsi_volume_curve",
            "hybrid",
            "RSI middle regime plus normal volume curve.",
            "evening_18_24",
            "rsi_mid",
            "volume_curve_range",
            volume_min=0.6,
            volume_max=1.8,
        ),
        c(
            19,
            "tech_volume_curve",
            "hybrid",
            "Technical score plus normal volume curve.",
            "evening_18_24",
            "technical_score_min",
            "volume_curve_range",
            score_min=4,
            volume_min=0.6,
            volume_max=1.8,
        ),
        c(
            20,
            "mom_volume_distance",
            "hybrid",
            "Momentum, normal curve volume, and VWAP distance.",
            "evening_18_24",
            "mom120_aligned",
            "volume_curve_range",
            "distance_mid",
            volume_min=0.6,
            volume_max=1.8,
            distance_min=0.3,
            distance_max=2.5,
        ),
        c(
            21,
            "avoid_bad_mom120",
            "momentum",
            "Drop weak buckets then require two-hour momentum.",
            "avoid_06_08_14_17",
            "mom120_aligned",
        ),
        c(
            22,
            "avoid_bad_tech4",
            "technical_rules",
            "Drop weak buckets then require technical score.",
            "avoid_06_08_14_17",
            "technical_score_min",
            score_min=4,
        ),
        c(
            23,
            "current_ma_20_80",
            "technical_rules",
            "Current window MA 20/80 confirmation.",
            "current_08_16",
            "ma20_80_aligned",
        ),
        c(
            24,
            "current_tech4",
            "technical_rules",
            "Current window technical score confirmation.",
            "current_08_16",
            "technical_score_min",
            score_min=4,
        ),
        c(
            25,
            "current_volume_curve",
            "dynamic_volume",
            "Current window normal volume curve.",
            "current_08_16",
            "volume_curve_range",
            volume_min=0.6,
            volume_max=1.8,
        ),
    ]


def run_candidates(
    signals: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    for candidate in candidate_matrix():
        frame = candidate_frame(signals, candidate)
        best = select_is_exit(frame)
        sample_rows: dict[str, dict[str, Any]] = {}
        for sample in ("IS", "OOS"):
            sample_frame = dedup(frame[frame["sample"] == sample])
            values = exit_values(sample_frame, best["stop_atr"], best["target_atr"], COST_ATR)
            metric = metrics(values)
            dollar_metric = dollar_metrics(sample_frame, values)
            row = {
                "round": candidate.round_id,
                "candidate": candidate.name,
                "family": candidate.family,
                "sample": sample,
                "thesis": candidate.thesis,
                "rules": ",".join(candidate.rules),
                "selected_stop_atr": best["stop_atr"],
                "selected_target_atr": best["target_atr"],
                "selected_is_score": best["score"],
                **metric,
                **dollar_metric,
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
                "thesis": candidate.thesis,
                "rules": ",".join(candidate.rules),
                "is_n": is_row["n"],
                "is_mean_atr": is_row["mean"],
                "is_sharpe": is_row["proxy_sharpe"],
                "is_cum_atr": is_row["cum_atr"],
                "is_pnl_usd": is_row["pnl_usd"],
                "is_max_dd_usd": is_row["max_dd_usd"],
                "oos_n": oos_row["n"],
                "oos_mean_atr": oos_row["mean"],
                "oos_sharpe": oos_row["proxy_sharpe"],
                "oos_cum_atr": oos_row["cum_atr"],
                "oos_pnl_usd": oos_row["pnl_usd"],
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


def candidate_frame(signals: pd.DataFrame, candidate: LiteratureCandidate) -> pd.DataFrame:
    mode = "current_08_16" if candidate.time_window == "current_08_16" else "full_session_18_17"
    frame = signals[signals["mode"] == mode].copy()
    mask = time_mask(frame, candidate.time_window)
    for rule in candidate.rules:
        mask &= rule_mask(frame, rule, candidate.params)
    return frame[mask].sort_values("signal_time_utc").copy()


def rule_mask(frame: pd.DataFrame, rule: str, params: dict[str, float]) -> pd.Series:
    direction = frame["dir_sign"]
    if rule == "mfi_mid":
        return frame["mfi_14"].between(35, 70)
    if rule == "rsi_mid":
        return frame["rsi_14"].between(40, 65)
    if rule == "distance_mid":
        return frame["close_distance_vwap_atr"].between(
            params.get("distance_min", 0.3),
            params.get("distance_max", 2.5),
        )
    if rule == "mom60_aligned":
        return direction * frame["mom_60_atr"] > 0
    if rule == "mom120_aligned":
        return direction * frame["mom_120_atr"] > 0
    if rule == "mom240_aligned":
        return direction * frame["mom_240_atr"] > 0
    if rule == "mom120_min":
        return direction * frame["mom_120_atr"] >= params.get("mom_min", 0.0)
    if rule == "ma20_80_aligned":
        return direction * frame["ma_20_80_atr"] > 0
    if rule == "ma50_200_aligned":
        return direction * frame["ma_50_200_atr"] > 0
    if rule == "technical_score_min":
        return frame["technical_score"] >= params.get("score_min", 4)
    if rule == "oscillator_score_min":
        return frame["oscillator_mid_score"] >= params.get("score_min", 4)
    if rule == "volume_curve_range":
        return frame["volume_curve_ratio"].between(
            params.get("volume_min", 0.6),
            params.get("volume_max", 1.8),
        )
    raise ValueError(f"unknown literature rule: {rule}")


def select_is_exit(frame: pd.DataFrame) -> dict[str, float]:
    is_frame = dedup(frame[frame["sample"] == "IS"])
    best = {"stop_atr": 2.0, "target_atr": 5.0, "score": -999.0}
    if len(is_frame) < 10:
        return best
    for stop in STOPS:
        for target in TARGETS:
            values = exit_values(is_frame, stop, target, COST_ATR)
            metric = metrics(values)
            dollars = dollar_metrics(is_frame, values)
            score = (
                metric_float(metric, "proxy_sharpe")
                + metric_float(metric, "mean")
                - abs(float(dollars["max_dd_usd"])) / 10000.0
            )
            if score > best["score"]:
                best = {"stop_atr": stop, "target_atr": target, "score": score}
    return best


def dollar_metrics(frame: pd.DataFrame, values: pd.Series) -> dict[str, float]:
    if frame.empty or values.empty:
        return {
            "pnl_usd": 0.0,
            "mean_usd": 0.0,
            "max_dd_usd": 0.0,
            "max_equity_usd": 0.0,
            "min_equity_usd": 0.0,
        }
    atr = frame.loc[values.index, "atr"].astype(float)
    dollars = values.astype(float) * atr * GC_MULTIPLIER
    curve = dollars.cumsum()
    drawdown = curve - curve.cummax()
    return {
        "pnl_usd": float(dollars.sum()),
        "mean_usd": float(dollars.mean()),
        "max_dd_usd": float(drawdown.min()),
        "max_equity_usd": float(curve.max()),
        "min_equity_usd": float(curve.min()),
    }


def segment_metrics(
    candidate: LiteratureCandidate,
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
                "segment": segment,
                "n": metric["n"],
                "mean_atr": metric["mean"],
                "proxy_sharpe": metric["proxy_sharpe"],
                "cum_atr": metric["cum_atr"],
                "pnl_usd": dollars["pnl_usd"],
                "max_dd_usd": dollars["max_dd_usd"],
            }
        )
    return rows


def score_summary(is_row: dict[str, Any], oos_row: dict[str, Any]) -> float:
    oos_n = int(oos_row["n"])
    oos_sharpe = float(oos_row["proxy_sharpe"])
    oos_mean = float(oos_row["mean"])
    oos_dd = abs(float(oos_row["max_dd_usd"])) / 10000.0
    is_penalty = 0.25 if float(is_row["pnl_usd"]) < 0 else 0.0
    sparse_penalty = 0.5 if oos_n < 50 else 0.0
    return oos_sharpe + oos_mean - oos_dd - is_penalty - sparse_penalty


def write_outputs(
    raw_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    segment_rows: list[dict[str, Any]],
) -> None:
    pd.DataFrame(raw_rows).to_csv(OUT_RAW_CSV, index=False)
    pd.DataFrame(summary_rows).to_csv(OUT_CSV, index=False)
    pd.DataFrame(segment_rows).to_csv(OUT_SEGMENTS_CSV, index=False)
    OUT_JSON.write_text(
        json.dumps(
            {
                "method": {
                    "date": "2026-05-20",
                    "source_prior_proxy": str(PRIOR_PROXY_JSON.relative_to(REPO_ROOT)),
                    "families": ["momentum", "technical_rules", "dynamic_volume", "hybrid"],
                    "gc_multiplier": GC_MULTIPLIER,
                    "exit_model": (
                        "60m dedup, IS-selected stop/target, conservative stop-first, 0.05 ATR cost"
                    ),
                    "volume_curve": (
                        "current volume divided by prior rolling mean for the same ET minute"
                    ),
                },
                "ranked": summary_rows,
                "raw": raw_rows,
                "segments": segment_rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    OUT_MD.write_text(markdown(summary_rows), encoding="utf-8")


def markdown(summary_rows: list[dict[str, Any]]) -> str:
    lines = [
        "# VWAP Literature-Inspired Factor Research",
        "",
        "Date: 2026-05-20",
        "",
        "## Method",
        "",
        "- Time-series momentum: 60/120/240 minute ATR-normalized continuation.",
        "- Technical rules: MA cross, MACD/ADX/ROC/Donchian confirmation, oscillator consensus.",
        "- Dynamic volume/VWAP: same ET-minute rolling volume curve plus VWAP distance filters.",
        "- Exit proxy: 60-minute cooldown, IS-selected stop/target, stop-first, 0.05 ATR cost.",
        "",
        "## Ranked Results",
        "",
        "| Rank | Round | Candidate | Family | OOS n | OOS PnL | OOS Sharpe | "
        "OOS MaxDD | Stop | Target |",
        "|---:|---:|:---|:---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(summary_rows, start=1):
        lines.append(
            f"| {rank} | {row['round']} | {row['candidate']} | {row['family']} | "
            f"{row['oos_n']} | {row['oos_pnl_usd']:.2f} | {row['oos_sharpe']:.3f} | "
            f"{row['oos_max_dd_usd']:.2f} | {row['stop_atr']:.1f} | "
            f"{row['target_atr']:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Summary CSV: `{OUT_CSV.relative_to(REPO_ROOT)}`",
            f"- Summary JSON: `{OUT_JSON.relative_to(REPO_ROOT)}`",
            f"- Raw CSV: `{OUT_RAW_CSV.relative_to(REPO_ROOT)}`",
            f"- Segment CSV: `{OUT_SEGMENTS_CSV.relative_to(REPO_ROOT)}`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
