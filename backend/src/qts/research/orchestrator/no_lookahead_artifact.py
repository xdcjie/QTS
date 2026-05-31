"""No-lookahead validation artifact builder.

Owns the promotion-grade no-lookahead (timing-protocol) validation payload that
``ValidationArtifactWriter`` previously built inline: deriving feature timing
specs, label policy, and validation windows from the backtest manifest +
pipeline config, running them through ``NoLookaheadValidationRunner``, and
emitting the artifact payload (with a legacy forbidden-term string scan retained
for backward compatibility only). Extracted per QTS-FINAL-011 so each validation
artifact family is owned by a focused builder.
"""

from __future__ import annotations

import contextlib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash


class NoLookaheadValidationArtifact:
    """Builds the no-lookahead (timing-protocol) validation artifact payload."""

    # Transform types / signed offsets that read data *after* the decision bar.
    _FORWARD_TRANSFORM_TERMS = ("forward", "future", "lead", "lookahead")
    _FORWARD_OFFSET_KEYS = ("lookback", "shift", "offset", "horizon", "window")

    def payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build the no-lookahead validation payload for a succeeded trial."""
        from qts.research.validation import NoLookaheadValidationRunner

        # Timing-protocol validation: feature timestamps, label policy, windows.
        windows = self._no_lookahead_windows(backtest_manifest, pipeline_config)
        # Anchor feature timing to the real out-of-sample cutoff (the earliest
        # test/OOS window start) instead of a 1970 epoch placeholder, so the
        # feature-timestamp and visible_at checks run against real, in-window
        # times. A factor input declared with a forward-looking transform is
        # observable only after the decision and therefore exceeds the cutoff.
        decision_cutoff = self._no_lookahead_decision_cutoff(windows, backtest_manifest)
        features = self._no_lookahead_features(parameters, pipeline_config, decision_cutoff)
        label_policy = self._no_lookahead_label_policy(parameters, pipeline_config)
        protocol = self._no_lookahead_factor_snapshot_protocol(backtest_manifest, parameters)
        runner = NoLookaheadValidationRunner(
            features=features,
            label_policy=label_policy,
            windows=windows,
            factor_snapshot_protocol=protocol,
            decision_time=decision_cutoff,
        )
        result = runner.validate()
        timing_payload = result.to_payload()

        # Legacy string scan retained for backward compatibility only.
        # It is NOT sufficient for promotion-grade validation.
        forbidden_terms = ("future_return", "forward_return", "future_shift", "lookahead", "lead")
        scanned_payload = {
            "parameters": dict(parameters),
            "pipeline_config": dict(pipeline_config),
        }
        serialized = stable_json_dumps(scanned_payload).lower()
        string_violations = tuple(term for term in forbidden_terms if term in serialized)

        return {
            "dataset_metadata_hash": stable_json_hash(
                backtest_manifest.get("dataset_metadata", ())
            ),
            "forbidden_terms": list(forbidden_terms),
            "manifest_hash": str(backtest_manifest.get("manifest_hash", "")),
            "passed": result.passed and not string_violations,
            "string_scan_only": False,
            "string_scan_violations": list(string_violations),
            "timing_validation": timing_payload,
            "violations": [
                v.to_payload() if hasattr(v, "to_payload") else v for v in result.violations
            ],
            "window_overlaps": list(result.window_overlaps),
            **{
                k: timing_payload[k]
                for k in (
                    "checked_features",
                    "label_horizon",
                    "max_feature_timestamp",
                    "min_label_cutoff",
                )
                if k in timing_payload
            },
        }

    def _no_lookahead_decision_cutoff(
        self,
        windows: Sequence[Any],
        backtest_manifest: Mapping[str, Any],
    ) -> datetime | None:
        """Return the no-lookahead decision cutoff: the earliest OOS window start.

        Features must be observable at or before the out-of-sample boundary.
        Falls back to the backtest window end, then None when neither is present
        (older artifacts), in which case feature timing degrades to the 1970
        epoch sentinel rather than failing construction.
        """
        oos_starts: list[datetime] = [
            window.start for window in windows if getattr(window, "role", "") != "train"
        ]
        if oos_starts:
            return min(oos_starts)
        window = backtest_manifest.get("window")
        if isinstance(window, Mapping):
            end = window.get("end")
            if isinstance(end, str):
                try:
                    return datetime.fromisoformat(end.replace("Z", "+00:00"))
                except ValueError:
                    return None
        return None

    def _no_lookahead_features(
        self,
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
        decision_cutoff: datetime | None,
    ) -> tuple[Any, ...]:
        """Derive feature timing specs from pipeline parameters and config.

        Backward-looking inputs are observable at the decision (``decision_cutoff``);
        a forward-looking transform is observable only after it, so its feature
        timestamp is placed past the cutoff and the runner flags the leak.
        """

        from qts.research.validation import FeatureTimingSpec as _FeatureTimingSpec

        observed_at = (
            decision_cutoff if decision_cutoff is not None else datetime(1970, 1, 1, tzinfo=UTC)
        )
        # A clearly-after-cutoff stamp for forward-looking derivations.
        after_cutoff = decision_cutoff + timedelta(days=1) if decision_cutoff is not None else None

        features: list[_FeatureTimingSpec] = []
        research_factory = pipeline_config.get("research_factory")
        if isinstance(research_factory, Mapping):
            factor_def = research_factory.get("factor_definition")
            if isinstance(factor_def, Mapping):
                inputs = factor_def.get("inputs")
                if isinstance(inputs, Sequence) and not isinstance(inputs, str):
                    for inp in inputs:
                        if isinstance(inp, Mapping):
                            name = inp.get("field", inp.get("root", "unknown"))
                            features.append(
                                _FeatureTimingSpec(
                                    name=str(name),
                                    timestamp=observed_at,
                                    visible_at=observed_at,
                                )
                            )
                forward_transform = self._forward_looking_transform(factor_def)
                if forward_transform is not None and after_cutoff is not None:
                    features.append(
                        _FeatureTimingSpec(
                            name=f"transform:{forward_transform}",
                            timestamp=after_cutoff,
                            visible_at=after_cutoff,
                        )
                    )
        for param_name in sorted(parameters):
            features.append(
                _FeatureTimingSpec(
                    name=str(param_name), timestamp=observed_at, visible_at=observed_at
                )
            )
        return tuple(features)

    @classmethod
    def _forward_looking_transform(cls, factor_def: Mapping[str, Any]) -> str | None:
        """Return a forward-looking transform's label, if the factor declares one.

        A transform is forward-looking when its ``type`` names a forward/future
        operation or it carries a negative offset (e.g. ``lookback: -3``), meaning
        it reads bars after the decision -- a look-ahead leak.
        """
        transforms = factor_def.get("transforms")
        if not isinstance(transforms, Sequence) or isinstance(transforms, str):
            return None
        for transform in transforms:
            if not isinstance(transform, Mapping):
                continue
            transform_type = str(transform.get("type", "")).lower()
            if any(term in transform_type for term in cls._FORWARD_TRANSFORM_TERMS):
                return transform_type or "forward"
            for key in cls._FORWARD_OFFSET_KEYS:
                value = transform.get(key)
                if isinstance(value, int) and not isinstance(value, bool) and value < 0:
                    return f"{transform_type or 'transform'}:{key}"
        return None

    def _no_lookahead_label_policy(
        self,
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> Any | None:
        """Derive label policy from pipeline config."""

        from qts.research.validation import LabelPolicy as _LabelPolicy

        research_factory = pipeline_config.get("research_factory")
        if not isinstance(research_factory, Mapping):
            return None
        factor_def = research_factory.get("factor_definition")
        if not isinstance(factor_def, Mapping):
            return None
        label_policy_raw = factor_def.get("label_policy")
        if not isinstance(label_policy_raw, Mapping):
            return None
        horizon = label_policy_raw.get("horizon_bars")
        visible_after = label_policy_raw.get("visible_after")
        no_lookahead = label_policy_raw.get("no_lookahead", True)
        if not isinstance(horizon, int) or isinstance(horizon, bool):
            return None
        if not isinstance(visible_after, str) or not visible_after.strip():
            return None
        return _LabelPolicy(
            horizon_bars=horizon,
            visible_after=visible_after.strip(),
            no_lookahead=bool(no_lookahead),
        )

    def _no_lookahead_windows(
        self,
        backtest_manifest: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> tuple[Any, ...]:
        """Derive validation windows from backtest manifest and pipeline config."""

        from qts.research.validation import ValidationWindow as _ValidationWindow

        windows: list[_ValidationWindow] = []
        for source in (pipeline_config, backtest_manifest):
            splits = source.get("splits")
            if not isinstance(splits, Mapping):
                continue
            raw_windows = splits.get("windows")
            if not isinstance(raw_windows, Sequence) or isinstance(raw_windows, str):
                continue
            for raw_window in raw_windows:
                if not isinstance(raw_window, Mapping):
                    continue
                name = raw_window.get("name")
                role = raw_window.get("role")
                start = raw_window.get("start")
                end = raw_window.get("end")
                if (
                    isinstance(name, str)
                    and isinstance(role, str)
                    and isinstance(start, str)
                    and isinstance(end, str)
                ):
                    role_map = {
                        "in_sample": "train",
                        "validation": "test",
                        "out_of_sample": "out_of_sample",
                    }
                    mapped_role = role_map.get(role, role)
                    if mapped_role in {"train", "test", "out_of_sample"}:
                        with contextlib.suppress(ValueError, TypeError):
                            windows.append(
                                _ValidationWindow(
                                    name=name.strip(),
                                    role=mapped_role,
                                    start=datetime.fromisoformat(start.replace("Z", "+00:00")),
                                    end=datetime.fromisoformat(end.replace("Z", "+00:00")),
                                )
                            )
        return tuple(windows)

    def _no_lookahead_factor_snapshot_protocol(
        self,
        backtest_manifest: Mapping[str, Any],
        parameters: Mapping[str, Any],
    ) -> Mapping[str, Any] | None:
        """Extract FactorSnapshotProtocol payload from manifest if present."""

        for key in ("factor_snapshot_protocol", "forward_return_protocol"):
            protocol = backtest_manifest.get(key)
            if isinstance(protocol, Mapping):
                return protocol
        return None


__all__ = ["NoLookaheadValidationArtifact"]
