"""Honest research metrics derived from validation artifacts.

Reads validation artifacts produced by experiment runs and derives
research metrics from real evidence.  Fields that lack artifact backing
are emitted as ``None`` rather than hardcoded pass/1.0 defaults.

This module owns the boundary between "validation artifacts on disk" and
"research metrics payloads".  It does not own validation execution.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidationArtifactRead:
    """One validation artifact read from disk."""

    artifact_name: str
    payload: Mapping[str, Any]
    path: Path


class ValidationArtifactReader:
    """Load required validation artifacts by name from a run artifact directory.

    Each artifact is a JSON wrapper with a ``payload`` key containing the
    validation result.  If the file is missing or malformed the read returns
    ``None`` rather than raising, allowing callers to distinguish "not
    validated" from "validated and failed".
    """

    def __init__(self, artifact_dir: Path) -> None:
        self._artifact_dir = Path(artifact_dir)

    def read(self, artifact_name: str) -> ValidationArtifactRead | None:
        """Read a validation artifact by name.

        Returns ``None`` when the artifact file is absent or cannot be parsed.
        """
        path = self._artifact_dir / "validation" / f"{artifact_name}.json"
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(raw, Mapping):
            return None
        payload = raw.get("payload")
        if not isinstance(payload, Mapping):
            return None
        return ValidationArtifactRead(
            artifact_name=artifact_name,
            payload=payload,
            path=path,
        )

    def read_all(
        self, artifact_names: tuple[str, ...]
    ) -> dict[str, ValidationArtifactRead | None]:
        """Read multiple artifacts by name.

        Missing artifacts map to ``None`` values.
        """
        return {name: self.read(name) for name in artifact_names}


# Artifact names that map to research metrics fields.
_REQUIRED_ARTIFACT_NAMES: tuple[str, ...] = (
    "deterministic_replay",
    "no_lookahead",
    "walk_forward_validation",
    "cost_stress",
)


@dataclass(frozen=True, slots=True)
class SharpeSources:
    """train_sharpe and oos_sharpe with provenance from separate manifests."""

    train_sharpe: float | None
    oos_sharpe: float | None
    train_manifest_hash: str | None
    oos_manifest_hash: str | None

    @property
    def same_source(self) -> bool:
        """True when both sharpes come from the same manifest hash."""
        if self.train_manifest_hash is None or self.oos_manifest_hash is None:
            return False
        return self.train_manifest_hash == self.oos_manifest_hash


@dataclass(frozen=True, slots=True)
class ResearchMetricsDerivation:
    """Honest research metrics derived from validation artifacts.

    Fields are ``None`` when the backing artifact is missing, rather than
    defaulting to passing/high values.
    """

    deterministic_replay_passed: bool | None
    no_lookahead_passed: bool | None
    walk_forward_consistency: float | None
    parameter_sensitivity: float | None
    oos_months: float | None
    sharpe_sources: SharpeSources
    promotion_eligible: bool

    @property
    def has_hollow_verdict(self) -> bool:
        """True when any required validation field is missing."""
        return any(
            value is None
            for value in (
                self.deterministic_replay_passed,
                self.no_lookahead_passed,
                self.walk_forward_consistency,
                self.parameter_sensitivity,
                self.oos_months,
            )
        )

    @property
    def is_overfit_candidate(self) -> bool:
        """True when train_sharpe == oos_sharpe from the same source manifest."""
        sources = self.sharpe_sources
        if sources.train_sharpe is None or sources.oos_sharpe is None:
            return False
        return sources.same_source and sources.train_sharpe == sources.oos_sharpe


def _compute_oos_months(
    workflow_summary: Mapping[str, Any],
    train_manifest: Mapping[str, Any] | None,
    test_manifest: Mapping[str, Any] | None,
) -> float | None:
    """Compute OOS months from declared windows in manifests or workflow summary."""
    # Try workflow summary periods first
    periods = workflow_summary.get("periods")
    if isinstance(periods, list):
        oos_periods = [
            period
            for period in periods
            if isinstance(period, Mapping)
            and period.get("role") in ("oos", "test", "out_of_sample")
        ]
        if oos_periods:
            return _total_months_from_periods(oos_periods)

    # Try test manifest window
    if test_manifest is not None:
        oos_months = _months_from_manifest_window(test_manifest)
        if oos_months is not None:
            return oos_months

    # Try train manifest (derive from train end to total end)
    if train_manifest is not None:
        oos_months = _months_from_manifest_window(train_manifest)
        if oos_months is not None:
            return oos_months

    return None


def _total_months_from_periods(periods: list[Mapping[str, Any]]) -> float:
    """Sum months across a list of OOS period declarations."""
    total = 0.0
    for period in periods:
        start = _parse_iso(period.get("start"))
        end = _parse_iso(period.get("end"))
        if start is not None and end is not None:
            total += _month_delta(start, end)
    return total


def _months_from_manifest_window(manifest: Mapping[str, Any]) -> float | None:
    """Extract OOS months from a backtest manifest window declaration."""
    window = manifest.get("window")
    if isinstance(window, Mapping):
        start = _parse_iso(window.get("start"))
        end = _parse_iso(window.get("end"))
        if start is not None and end is not None:
            return _month_delta(start, end)
    # Fallback: top-level start/end
    start = _parse_iso(manifest.get("start"))
    end = _parse_iso(manifest.get("end"))
    if start is not None and end is not None:
        return _month_delta(start, end)
    return None


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO 8601 datetime string, returning None on failure."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _month_delta(start: datetime, end: datetime) -> float:
    """Compute fractional months between two datetimes."""
    start = start.astimezone(UTC)
    end = end.astimezone(UTC)
    if end <= start:
        return 0.0
    delta_days = (end - start).days
    return round(delta_days / 30.4375, 2)


class ResearchMetricsFromValidationArtifacts:
    """Derive honest research metrics from validation artifacts.

    This class owns the derivation logic: it reads artifacts produced by the
    experiment runner and produces metrics where every field is backed by real
    evidence or explicitly ``None``.
    """

    def derive(
        self,
        artifact_reader: ValidationArtifactReader,
        workflow_summary: Mapping[str, Any],
        *,
        train_manifest: Mapping[str, Any] | None = None,
        test_manifest: Mapping[str, Any] | None = None,
    ) -> ResearchMetricsDerivation:
        """Derive research metrics from validation artifacts.

        Parameters
        ----------
        artifact_reader:
            Reader configured to the trial's artifact directory.
        workflow_summary:
            The workflow summary payload for this trial.
        train_manifest:
            The train window backtest manifest (separate from test).
        test_manifest:
            The test/OOS window backtest manifest (separate from train).
        """
        artifacts = artifact_reader.read_all(_REQUIRED_ARTIFACT_NAMES)

        deterministic_replay_passed = self._derive_deterministic_replay(
            artifacts.get("deterministic_replay"),
        )
        no_lookahead_passed = self._derive_no_lookahead(
            artifacts.get("no_lookahead"),
        )
        walk_forward_consistency = self._derive_walk_forward_consistency(
            artifacts.get("walk_forward_validation"),
        )
        parameter_sensitivity = self._derive_parameter_sensitivity(
            artifacts.get("cost_stress"),
        )
        oos_months = _compute_oos_months(
            workflow_summary,
            train_manifest,
            test_manifest,
        )
        sharpe_sources = self._derive_sharpe_sources(
            artifacts.get("walk_forward_validation"),
            train_manifest=train_manifest,
            test_manifest=test_manifest,
        )

        promotion_eligible = self._derive_promotion_eligible(
            deterministic_replay_passed=deterministic_replay_passed,
            no_lookahead_passed=no_lookahead_passed,
            walk_forward_consistency=walk_forward_consistency,
            parameter_sensitivity=parameter_sensitivity,
            oos_months=oos_months,
            sharpe_sources=sharpe_sources,
        )

        return ResearchMetricsDerivation(
            deterministic_replay_passed=deterministic_replay_passed,
            no_lookahead_passed=no_lookahead_passed,
            walk_forward_consistency=walk_forward_consistency,
            parameter_sensitivity=parameter_sensitivity,
            oos_months=oos_months,
            sharpe_sources=sharpe_sources,
            promotion_eligible=promotion_eligible,
        )

    @staticmethod
    def _derive_deterministic_replay(
        artifact: ValidationArtifactRead | None,
    ) -> bool | None:
        if artifact is None:
            return None
        return bool(artifact.payload.get("passed"))

    @staticmethod
    def _derive_no_lookahead(
        artifact: ValidationArtifactRead | None,
    ) -> bool | None:
        if artifact is None:
            return None
        return bool(artifact.payload.get("passed"))

    @staticmethod
    def _derive_walk_forward_consistency(
        artifact: ValidationArtifactRead | None,
    ) -> float | None:
        if artifact is None:
            return None
        # The walk_forward_validation artifact has a "consistent" bool and
        # test_windows with scores. Derive consistency as a float metric.
        consistent = artifact.payload.get("consistent")
        if consistent is not True:
            return 0.0
        test_windows = artifact.payload.get("test_windows")
        if not isinstance(test_windows, list) or not test_windows:
            return None
        # Use the first test window's accepted status and train/test gap
        first_window = test_windows[0]
        if not isinstance(first_window, Mapping):
            return None
        train_score = first_window.get("train_score")
        test_score = first_window.get("score")
        if not isinstance(train_score, (int, float)) or not isinstance(
            test_score, (int, float)
        ):
            return None
        if train_score == 0:
            return 0.0
        return float(test_score / train_score)

    @staticmethod
    def _derive_parameter_sensitivity(
        artifact: ValidationArtifactRead | None,
    ) -> float | None:
        if artifact is None:
            return None
        degradation = artifact.payload.get("degradation")
        if not isinstance(degradation, (int, float)):
            return None
        # Lower degradation = less sensitivity to parameter/cost changes
        # Normalize: 0 degradation -> 1.0 (insensitive), high degradation -> 0.0
        return max(0.0, 1.0 - float(abs(degradation)))

    @staticmethod
    def _derive_sharpe_sources(
        artifact: ValidationArtifactRead | None,
        *,
        train_manifest: Mapping[str, Any] | None,
        test_manifest: Mapping[str, Any] | None,
    ) -> SharpeSources:
        train_sharpe: float | None = None
        oos_sharpe: float | None = None
        train_manifest_hash: str | None = None
        oos_manifest_hash: str | None = None

        # Derive from walk_forward_validation artifact which has train/test split
        if artifact is not None:
            test_windows = artifact.payload.get("test_windows")
            if isinstance(test_windows, list) and test_windows:
                first_window = test_windows[0]
                if isinstance(first_window, Mapping):
                    train_score = first_window.get("train_score")
                    test_score = first_window.get("score")
                    if isinstance(train_score, (int, float)):
                        train_sharpe = float(train_score)
                    if isinstance(test_score, (int, float)):
                        oos_sharpe = float(test_score)
                    train_manifest_hash = str(
                        first_window.get("train_manifest_hash", "")
                    ) or None
                    oos_manifest_hash = str(
                        first_window.get("manifest_hash", "")
                    ) or None

        # Override from explicit manifests if available
        if train_manifest is not None:
            train_stats = train_manifest.get("statistics")
            if isinstance(train_stats, Mapping):
                sharpe = train_stats.get("sharpe_ratio")
                if isinstance(sharpe, (int, float)):
                    train_sharpe = float(sharpe)
            train_hash = train_manifest.get("manifest_hash")
            if isinstance(train_hash, str) and train_hash.strip():
                train_manifest_hash = train_hash.strip()

        if test_manifest is not None:
            test_stats = test_manifest.get("statistics")
            if isinstance(test_stats, Mapping):
                sharpe = test_stats.get("sharpe_ratio")
                if isinstance(sharpe, (int, float)):
                    oos_sharpe = float(sharpe)
            test_hash = test_manifest.get("manifest_hash")
            if isinstance(test_hash, str) and test_hash.strip():
                oos_manifest_hash = test_hash.strip()

        return SharpeSources(
            train_sharpe=train_sharpe,
            oos_sharpe=oos_sharpe,
            train_manifest_hash=train_manifest_hash,
            oos_manifest_hash=oos_manifest_hash,
        )

    @staticmethod
    def _derive_promotion_eligible(
        *,
        deterministic_replay_passed: bool | None,
        no_lookahead_passed: bool | None,
        walk_forward_consistency: float | None,
        parameter_sensitivity: float | None,
        oos_months: float | None,
        sharpe_sources: SharpeSources,
    ) -> bool:
        """Promotion eligibility is derived from validation status, not a default."""
        if deterministic_replay_passed is not True:
            return False
        if no_lookahead_passed is not True:
            return False
        if walk_forward_consistency is None or walk_forward_consistency < 0.5:
            return False
        if parameter_sensitivity is None or parameter_sensitivity < 0.5:
            return False
        if oos_months is None or oos_months < 6.0:
            return False
        if sharpe_sources.same_source and sharpe_sources.train_sharpe == sharpe_sources.oos_sharpe:
            return False
        if sharpe_sources.train_sharpe is not None and sharpe_sources.oos_sharpe is not None:
            if sharpe_sources.oos_sharpe <= 0:
                return False
        return True


__all__ = [
    "ResearchMetricsDerivation",
    "ResearchMetricsFromValidationArtifacts",
    "SharpeSources",
    "ValidationArtifactRead",
    "ValidationArtifactReader",
]
