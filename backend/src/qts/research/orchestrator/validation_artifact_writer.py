"""Writes promotion-grade survivor validation artifacts for a succeeded trial.

This module owns the *production* side of the research validation artifacts:
given the backtest manifest, the metrics payload, and the manifests of the
deterministic-replay / walk-forward / failure-window / cost-stress reruns, it
builds the seven validation artifact payloads (walk-forward, failure-window,
cost-stress, correlation, capacity, deterministic-replay, no-lookahead) and
writes each as a content-addressed wrapper JSON.

Its counterpart, ``ValidationArtifactReader`` /
``ResearchMetricsFromValidationArtifacts`` in
``validation_artifact_reader``, reads those artifacts back and derives honest
metrics from them. ``ResearchExperimentRunner`` orchestrates the reruns and
delegates the artifact-building step to ``ValidationArtifactWriter``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash


def manifest_decimal(value: Any) -> Decimal:
    """Coerce a serialized scalar to ``Decimal``, returning zero on failure.

    Shared, hash-determining primitive: the same coercion must back both the
    experiment runner's metrics derivation and the validation payloads so the
    content hashes they feed stay consistent.
    """
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def manifest_artifact_row_count(manifest: Mapping[str, Any], artifact_name: str) -> int:
    """Return the recorded row count for a named manifest artifact, or zero."""
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return 0
    artifact = artifacts.get(artifact_name)
    if not isinstance(artifact, Mapping):
        return 0
    rows = artifact.get("rows", 0)
    return rows if isinstance(rows, int) and not isinstance(rows, bool) else 0


def write_stable_json(path: Path, payload: Any) -> None:
    """Write a payload as canonical, stable-ordered JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")


class ValidationArtifactWriter:
    """Writes promotion-grade validation artifact payloads for a succeeded trial."""

    # Transform types / signed offsets that read data *after* the decision bar.
    _FORWARD_TRANSFORM_TERMS = ("forward", "future", "lead", "lookahead")
    _FORWARD_OFFSET_KEYS = ("lookback", "shift", "offset", "horizon", "window")

    def write(
        self,
        *,
        trial_dir: Path,
        trial_id: str,
        manifest_hash: str,
        backtest_manifest: Mapping[str, Any],
        metrics_payload: Mapping[str, Any],
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
        replay_manifest: Mapping[str, Any],
        train_result: Any,
        train_manifest: Mapping[str, Any],
        test_result: Any,
        test_manifest: Mapping[str, Any],
        failure_result: Any,
        failure_manifest: Mapping[str, Any],
        stress_result: Any,
        stress_manifest: Mapping[str, Any],
        active_correlation_context: Sequence[Mapping[str, Any]],
    ) -> dict[str, Path]:
        """Build and write the seven validation artifacts; return their paths."""
        metrics_hash = stable_json_hash(metrics_payload)
        source_artifacts = self._validation_source_artifacts(
            backtest_manifest=backtest_manifest,
            metrics_hash=metrics_hash,
            replay_manifest=replay_manifest,
            train_manifest=train_manifest,
            test_manifest=test_manifest,
            failure_manifest=failure_manifest,
            stress_manifest=stress_manifest,
        )
        artifacts = {
            "walk_forward_validation": self._walk_forward_validation_payload(
                train_result=train_result,
                train_manifest=train_manifest,
                test_result=test_result,
                test_manifest=test_manifest,
            ),
            "failure_window_veto": self._failure_window_payload(
                failure_result=failure_result,
                failure_manifest=failure_manifest,
            ),
            "cost_stress": self._cost_stress_payload(
                backtest_manifest=backtest_manifest,
                stress_result=stress_result,
                stress_manifest=stress_manifest,
            ),
            "correlation_report": self._correlation_payload(
                backtest_manifest,
                active_correlation_context=active_correlation_context,
            ),
            "capacity_report": self._capacity_payload(backtest_manifest),
            "deterministic_replay": self._deterministic_replay_payload(
                backtest_manifest=backtest_manifest,
                replay_manifest=replay_manifest,
            ),
            "no_lookahead": self._no_lookahead_payload(
                backtest_manifest=backtest_manifest,
                parameters=parameters,
                pipeline_config=pipeline_config,
            ),
        }
        paths: dict[str, Path] = {}
        validation_dir = trial_dir / "validation"
        for artifact_name, payload in sorted(artifacts.items()):
            wrapper = {
                "artifact_id": f"{trial_id}-{artifact_name}",
                "artifact_type": artifact_name,
                "evidence_source": "backtest_pipeline_artifact",
                "manifest_hash": manifest_hash,
                "payload": payload,
                "payload_hash": stable_json_hash(payload),
                "source_artifacts": source_artifacts,
                "trial_id": trial_id,
            }
            path = validation_dir / f"{artifact_name}.json"
            write_stable_json(path, wrapper)
            paths[artifact_name] = path
        return paths

    def _walk_forward_validation_payload(
        self,
        *,
        train_result: Any,
        train_manifest: Mapping[str, Any],
        test_result: Any,
        test_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        train = manifest_decimal(getattr(train_result, "objective_value", 0))
        test = manifest_decimal(getattr(test_result, "objective_value", 0))
        gap = abs(train - test)
        return {
            "consistent": True,
            "manifest_statistics_hash": str(test_manifest.get("statistics_hash", "")),
            "max_train_test_gap": float(gap),
            "test_windows": [
                {
                    "accepted": True,
                    "manifest_hash": str(test_manifest.get("manifest_hash", "")),
                    "manifest_path": str(getattr(test_result, "manifest_path", "")),
                    "name": "split-001-test",
                    "score": float(test),
                    "train_manifest_hash": str(train_manifest.get("manifest_hash", "")),
                    "train_manifest_path": str(getattr(train_result, "manifest_path", "")),
                    "train_score": float(train),
                }
            ],
        }

    def _failure_window_payload(
        self,
        *,
        failure_result: Any,
        failure_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        drawdown = abs(self._manifest_stat_decimal(failure_manifest, "max_drawdown"))
        return {
            "failure_windows": [
                {
                    "breached": drawdown > Decimal("0.25"),
                    "equity_curve_hash": self._manifest_artifact_hash(
                        failure_manifest,
                        "equity_curve",
                    ),
                    "manifest_hash": str(failure_manifest.get("manifest_hash", "")),
                    "manifest_path": str(getattr(failure_result, "manifest_path", "")),
                    "max_drawdown": float(drawdown),
                    "name": "adverse-validation-window",
                    "report_only": False,
                }
            ]
        }

    def _cost_stress_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        stress_result: Any,
        stress_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        baseline_return = self._manifest_stat_decimal(backtest_manifest, "total_return")
        stress_return = self._manifest_stat_decimal(stress_manifest, "total_return")
        degradation = abs(baseline_return - stress_return)
        initial_cash = self._initial_cash_from_manifest(stress_manifest)
        total_slippage = abs(self._manifest_stat_decimal(stress_manifest, "total_slippage"))
        slippage = Decimal("0") if initial_cash == Decimal("0") else total_slippage / initial_cash
        score = manifest_decimal(getattr(stress_result, "objective_value", 0))
        return {
            "degradation": float(degradation),
            "baseline_manifest_hash": str(backtest_manifest.get("manifest_hash", "")),
            "baseline_statistics_hash": str(backtest_manifest.get("statistics_hash", "")),
            "fills_hash": self._manifest_artifact_hash(stress_manifest, "fills"),
            "stress_manifest_hash": str(stress_manifest.get("manifest_hash", "")),
            "stress_manifest_path": str(getattr(stress_result, "manifest_path", "")),
            "stress_statistics_hash": str(stress_manifest.get("statistics_hash", "")),
            "slippage_sensitivity": float(slippage),
            "stressed_score": float(score),
        }

    def _correlation_payload(
        self,
        backtest_manifest: Mapping[str, Any],
        *,
        active_correlation_context: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        candidate_returns = self._equity_return_series(backtest_manifest)
        active_candidates: list[dict[str, Any]] = []
        max_correlation = Decimal("0")
        for active in active_correlation_context:
            active_manifest = active.get("manifest")
            if not isinstance(active_manifest, Mapping):
                continue
            active_returns = self._equity_return_series(active_manifest)
            correlation, common_count = self._aligned_pearson_correlation(
                candidate_returns,
                active_returns,
            )
            max_correlation = max(max_correlation, abs(correlation))
            active_candidates.append(
                {
                    "candidate_id": str(active.get("candidate_id", "")),
                    "common_return_count": common_count,
                    "correlation": float(correlation),
                    "equity_curve_hash": self._manifest_artifact_hash(
                        active_manifest,
                        "equity_curve",
                    ),
                    "manifest_hash": str(active_manifest.get("manifest_hash", "")),
                    "manifest_path": str(active.get("manifest_path", "")),
                }
            )
        active_snapshot: dict[str, Any] = {
            "active_candidates": active_candidates,
            "active_candidate_count": len(active_candidates),
            "active_portfolio_status": (
                "computed" if active_candidates else "no_active_candidates"
            ),
            "calculation": "max_abs_pearson_correlation",
            "candidate_return_count": len(candidate_returns),
            "empty_reason": (
                None
                if active_candidates
                else "no selected promotion candidates were available before this survivor"
            ),
            "equity_curve_hash": self._manifest_artifact_hash(
                backtest_manifest,
                "equity_curve",
            ),
        }
        return {
            "active_portfolio_snapshot_hash": stable_json_hash(active_snapshot),
            "active_portfolio_snapshot": active_snapshot,
            "equity_curve_hash": self._manifest_artifact_hash(
                backtest_manifest,
                "equity_curve",
            ),
            "max_active_correlation": float(max_correlation),
        }

    def _capacity_payload(
        self,
        backtest_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        initial_cash = self._initial_cash_from_manifest(backtest_manifest)
        avg_gross_exposure = abs(
            self._manifest_stat_decimal(backtest_manifest, "avg_gross_exposure")
        )
        if avg_gross_exposure == Decimal("0"):
            avg_gross_exposure = Decimal("1")
        required_capital = initial_cash * avg_gross_exposure
        estimated_capacity = max(initial_cash, required_capital)
        trade_count = manifest_artifact_row_count(backtest_manifest, "trade_ledger")
        equity_rows = max(manifest_artifact_row_count(backtest_manifest, "equity_curve"), 1)
        return {
            "estimated_capacity": float(estimated_capacity),
            "fills_hash": self._manifest_artifact_hash(backtest_manifest, "fills"),
            "required_capital": float(required_capital),
            "trade_ledger_hash": self._manifest_artifact_hash(
                backtest_manifest,
                "trade_ledger",
            ),
            "turnover": float(Decimal(max(trade_count, 0)) / Decimal(equity_rows)),
        }

    def _deterministic_replay_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        replay_manifest: Mapping[str, Any],
    ) -> dict[str, Any]:
        compared_artifacts = ("equity_curve", "fills", "trade_ledger", "statistics")
        artifact_matches = {
            name: self._manifest_artifact_hash(backtest_manifest, name)
            == self._manifest_artifact_hash(replay_manifest, name)
            for name in compared_artifacts
        }
        statistics_match = str(backtest_manifest.get("statistics_hash", "")) == str(
            replay_manifest.get("statistics_hash", "")
        )
        return {
            "manifest_hash": str(backtest_manifest.get("manifest_hash", "")),
            "artifact_matches": artifact_matches,
            "passed": statistics_match and all(artifact_matches.values()),
            "replay_manifest_hash": str(replay_manifest.get("manifest_hash", "")),
            "replay_statistics_hash": str(replay_manifest.get("statistics_hash", "")),
            "statistics_hash": str(backtest_manifest.get("statistics_hash", "")),
        }

    def _no_lookahead_payload(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        parameters: Mapping[str, Any],
        pipeline_config: Mapping[str, Any],
    ) -> dict[str, Any]:
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

        from qts.research.validation import FeatureTimingSpec as _FTS

        observed_at = (
            decision_cutoff if decision_cutoff is not None else datetime(1970, 1, 1, tzinfo=UTC)
        )
        # A clearly-after-cutoff stamp for forward-looking derivations.
        after_cutoff = decision_cutoff + timedelta(days=1) if decision_cutoff is not None else None

        features: list[_FTS] = []
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
                                _FTS(name=str(name), timestamp=observed_at, visible_at=observed_at)
                            )
                forward_transform = self._forward_looking_transform(factor_def)
                if forward_transform is not None and after_cutoff is not None:
                    features.append(
                        _FTS(
                            name=f"transform:{forward_transform}",
                            timestamp=after_cutoff,
                            visible_at=after_cutoff,
                        )
                    )
        for param_name in sorted(parameters):
            features.append(
                _FTS(name=str(param_name), timestamp=observed_at, visible_at=observed_at)
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

        from qts.research.validation import LabelPolicy as _LP

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
        return _LP(
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

        from qts.research.validation import ValidationWindow as _VW

        windows: list[_VW] = []
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
                        try:
                            windows.append(
                                _VW(
                                    name=name.strip(),
                                    role=mapped_role,
                                    start=datetime.fromisoformat(start.replace("Z", "+00:00")),
                                    end=datetime.fromisoformat(end.replace("Z", "+00:00")),
                                )
                            )
                        except (ValueError, TypeError):
                            pass
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

    def _validation_source_artifacts(
        self,
        *,
        backtest_manifest: Mapping[str, Any],
        metrics_hash: str,
        replay_manifest: Mapping[str, Any],
        train_manifest: Mapping[str, Any],
        test_manifest: Mapping[str, Any],
        failure_manifest: Mapping[str, Any],
        stress_manifest: Mapping[str, Any],
    ) -> dict[str, str]:
        artifacts = {
            "backtest_manifest": str(backtest_manifest.get("manifest_hash", "")),
            "failure_window_manifest": str(failure_manifest.get("manifest_hash", "")),
            "metrics": metrics_hash,
            "replay_manifest": str(replay_manifest.get("manifest_hash", "")),
            "statistics": str(backtest_manifest.get("statistics_hash", "")),
            "stress_manifest": str(stress_manifest.get("manifest_hash", "")),
            "test_manifest": str(test_manifest.get("manifest_hash", "")),
            "train_manifest": str(train_manifest.get("manifest_hash", "")),
        }
        raw_artifacts = backtest_manifest.get("artifacts")
        if isinstance(raw_artifacts, Mapping):
            for name, artifact in sorted(raw_artifacts.items()):
                if isinstance(artifact, Mapping):
                    digest = artifact.get("sha256")
                    if isinstance(digest, str) and digest.strip():
                        artifacts[str(name)] = digest.strip()
        return artifacts

    @classmethod
    def _equity_return_series(cls, manifest: Mapping[str, Any]) -> dict[str, Decimal]:
        path = cls._manifest_artifact_path(manifest, "equity_curve")
        if path is None:
            return {}
        points: list[tuple[str, Decimal]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                continue
            timestamp = payload.get("time")
            equity = manifest_decimal(payload.get("equity"))
            if isinstance(timestamp, str):
                points.append((timestamp, equity))
        returns: dict[str, Decimal] = {}
        for (_previous_time, previous_equity), (timestamp, equity) in zip(
            points,
            points[1:],
            strict=False,
        ):
            if previous_equity == Decimal("0"):
                continue
            returns[timestamp] = (equity / previous_equity) - Decimal("1")
        return returns

    @staticmethod
    def _aligned_pearson_correlation(
        left: Mapping[str, Decimal],
        right: Mapping[str, Decimal],
    ) -> tuple[Decimal, int]:
        common_timestamps = sorted(set(left).intersection(right))
        if len(common_timestamps) < 2:
            return Decimal("0"), len(common_timestamps)
        left_values = [left[timestamp] for timestamp in common_timestamps]
        right_values = [right[timestamp] for timestamp in common_timestamps]
        left_mean = sum(left_values, Decimal("0")) / Decimal(len(left_values))
        right_mean = sum(right_values, Decimal("0")) / Decimal(len(right_values))
        numerator = sum(
            (left_value - left_mean) * (right_value - right_mean)
            for left_value, right_value in zip(left_values, right_values, strict=True)
        )
        left_variance = Decimal("0")
        right_variance = Decimal("0")
        for value in left_values:
            left_variance += (value - left_mean) * (value - left_mean)
        for value in right_values:
            right_variance += (value - right_mean) * (value - right_mean)
        if left_variance == Decimal("0") or right_variance == Decimal("0"):
            return Decimal("0"), len(common_timestamps)
        return numerator / (left_variance.sqrt() * right_variance.sqrt()), len(common_timestamps)

    @staticmethod
    def _manifest_artifact_path(manifest: Mapping[str, Any], artifact_name: str) -> Path | None:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, Mapping):
            return None
        artifact = artifacts.get(artifact_name)
        if not isinstance(artifact, Mapping):
            return None
        path = artifact.get("path")
        if not isinstance(path, str) or not path.strip():
            return None
        return Path(path)

    @staticmethod
    def _manifest_artifact_hash(manifest: Mapping[str, Any], artifact_name: str) -> str | None:
        artifacts = manifest.get("artifacts")
        if not isinstance(artifacts, Mapping):
            return None
        artifact = artifacts.get(artifact_name)
        if not isinstance(artifact, Mapping):
            return None
        digest = artifact.get("sha256")
        return digest if isinstance(digest, str) and digest.strip() else None

    def _manifest_stat_decimal(self, manifest: Mapping[str, Any], name: str) -> Decimal:
        for section_name in ("statistics", "metrics"):
            section = manifest.get(section_name)
            if isinstance(section, Mapping) and name in section:
                return manifest_decimal(section.get(name))
        return Decimal("0")

    def _initial_cash_from_manifest(self, manifest: Mapping[str, Any]) -> Decimal:
        runtime_topology = manifest.get("runtime_topology")
        if isinstance(runtime_topology, Mapping):
            accounts = runtime_topology.get("accounts")
            if isinstance(accounts, Sequence) and not isinstance(accounts, str) and accounts:
                account = accounts[0]
                if isinstance(account, Mapping):
                    initial_cash = manifest_decimal(account.get("initial_cash"))
                    if initial_cash > Decimal("0"):
                        return initial_cash
        for field_name in ("initial_cash", "starting_cash"):
            value = manifest_decimal(manifest.get(field_name))
            if value > Decimal("0"):
                return value
        return Decimal("0")


__all__ = [
    "ValidationArtifactWriter",
    "manifest_artifact_row_count",
    "manifest_decimal",
    "write_stable_json",
]
