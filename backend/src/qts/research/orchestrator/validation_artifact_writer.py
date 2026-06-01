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

import itertools
import json
from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.orchestrator.no_lookahead_artifact import NoLookaheadValidationArtifact


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
            "no_lookahead": NoLookaheadValidationArtifact().payload(
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
        allowed_gap = max(abs(train), abs(test), Decimal("1")) * Decimal("0.25")
        accepted = test >= Decimal("0") and gap <= allowed_gap
        return {
            "consistent": accepted,
            "manifest_statistics_hash": str(test_manifest.get("statistics_hash", "")),
            "max_allowed_train_test_gap": float(allowed_gap),
            "max_train_test_gap": float(gap),
            "test_windows": [
                {
                    "accepted": accepted,
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
        for (_previous_time, previous_equity), (timestamp, equity) in itertools.pairwise(points):
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
