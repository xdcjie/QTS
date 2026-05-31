"""Promotion-metrics integrity checks.

Owns the packet-independent metrics-payload integrity rules extracted from
:class:`PromotionPacketValidator` (QTS-FINAL-011): research-safety flag gating,
optimistic fill-timing rejection, hollow-verdict sentinel detection, and
train/oos Sharpe source-provenance checks. These are pure functions over a
metrics payload with no packet state, so the validator stays the orchestrator
while these remain reusable, individually testable rules.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _append_execution_timing_reasons(
    research: Mapping[str, Any],
    reasons: list[str],
) -> None:
    """Gate promotion on the evidence backtest's fill-timing honesty.

    ``research.fill_timing_promotion_grade`` is the manifest-derived fact
    recording whether the evidence backtest's fills may back promotion
    evidence. It is ``True`` only for next-obtainable (``next_bar_open``)
    fills; the optimistic ``same_bar_close`` policy is never promotion-grade,
    even with a research waiver, so a ``False`` value means the evidence used
    optimistic same-bar look-ahead fills and is rejected. ``None`` (no
    manifest recorded the flag, e.g. synthetic fixtures) is not gated here --
    the upstream ``promotion_eligible`` derivation already rejects unverified
    evidence.
    """
    if research.get("fill_timing_promotion_grade") is False:
        reasons.append(
            "research.fill_timing_promotion_grade is False: evidence backtest "
            "used optimistic same_bar_close look-ahead fills, which are never "
            "promotion-grade"
        )


def _check_hollow_verdict_sentinel(
    metrics_payload: Mapping[str, Any],
    reasons: list[str],
) -> None:
    """Reject metrics that use the old hardcoded sentinel defaults.

    The old pattern was:
    - deterministic_replay_passed=True, no_lookahead_passed=True,
      promotion_eligible=True (all True with no None)
    - parameter_sensitivity=1.0, walk_forward_consistency=1.0 (perfect)
    - oos_months=12.0 (hardcoded)
    This combination is the signature of a hollow verdict that was not
    derived from actual validation artifacts.
    """
    research = metrics_payload.get("research")
    if not isinstance(research, Mapping):
        return

    research_booleans = {
        "deterministic_replay_passed",
        "no_lookahead_passed",
        "promotion_eligible",
    }
    all_research_true = all(research.get(field) is True for field in research_booleans)

    stability = metrics_payload.get("stability")
    stability_all_perfect = False
    if isinstance(stability, Mapping):
        ps = stability.get("parameter_sensitivity")
        wf = stability.get("walk_forward_consistency")
        if ps == 1.0 and wf == 1.0:
            stability_all_perfect = True

    trading = metrics_payload.get("trading")
    oos_months_hardcoded = False
    if isinstance(trading, Mapping) and trading.get("oos_months") == 12.0:
        oos_months_hardcoded = True

    if all_research_true and stability_all_perfect and oos_months_hardcoded:
        reasons.append(
            "metrics contain hollow verdict sentinel: "
            "all research booleans True with parameter_sensitivity=1.0, "
            "walk_forward_consistency=1.0, oos_months=12.0"
        )


def _check_sharpe_source_provenance(
    metrics_payload: Mapping[str, Any],
    reasons: list[str],
) -> None:
    """Reject train_sharpe == oos_sharpe when they share the same source.

    If both train_sharpe and oos_sharpe are identical and come from the
    same source manifest, this indicates they were not computed from
    separate train/test splits, which is a known overfit indicator.
    """
    performance = metrics_payload.get("performance")
    if not isinstance(performance, Mapping):
        return

    train_sharpe = performance.get("train_sharpe")
    oos_sharpe = performance.get("oos_sharpe")

    # If either is None, validation artifacts were not produced
    if train_sharpe is None:
        reasons.append("performance.train_sharpe is missing: validation artifact not produced")
    if oos_sharpe is None:
        reasons.append("performance.oos_sharpe is missing: validation artifact not produced")

    if train_sharpe is None or oos_sharpe is None:
        return

    # Same value from the same source is a known overfit indicator
    if train_sharpe == oos_sharpe:
        # Check if they have the same source manifest hash
        train_manifest_hash = performance.get("train_manifest_hash")
        oos_manifest_hash = performance.get("oos_manifest_hash")
        if train_manifest_hash is not None and oos_manifest_hash is not None:
            if train_manifest_hash == oos_manifest_hash:
                reasons.append(
                    "performance.train_sharpe == oos_sharpe from the same "
                    "source manifest: known overfit candidate"
                )
        else:
            # Without explicit provenance, identical values are suspicious
            reasons.append(
                "performance.train_sharpe == oos_sharpe without separate source manifest provenance"
            )


def append_research_safety_metric_reasons(
    metrics_payload: Mapping[str, Any],
    reasons: list[str],
) -> None:
    research = metrics_payload.get("research")
    if not isinstance(research, Mapping):
        return

    # Validation-gated fields must be True (not None, not False)
    for field_name in ("deterministic_replay_passed", "no_lookahead_passed"):
        value = research.get(field_name)
        if value is None:
            reasons.append(f"research.{field_name} is missing: validation artifact not produced")
        elif value is not True:
            reasons.append(f"research.{field_name} must be true")

    # promotion_eligible must be explicitly True from derived validation status
    promotion_eligible = research.get("promotion_eligible")
    if promotion_eligible is None:
        reasons.append("research.promotion_eligible is missing: not derived from validation")
    elif promotion_eligible is not True:
        reasons.append("research.promotion_eligible must be true")

    # Optimistic same-bar-close fills are look-ahead and cannot back
    # promotion evidence unless an explicit optimistic waiver is recorded.
    _append_execution_timing_reasons(research, reasons)

    # Detect hollow verdict: all-True research booleans with
    # stability all-1.0 is a sentinel pattern from the old hardcoded
    # defaults.
    _check_hollow_verdict_sentinel(metrics_payload, reasons)

    # train_sharpe and oos_sharpe must come from different source manifests
    _check_sharpe_source_provenance(metrics_payload, reasons)


__all__ = ["append_research_safety_metric_reasons"]
