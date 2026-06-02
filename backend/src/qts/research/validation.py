"""Timing-protocol-level no-lookahead validation for research artifacts.

Replaces string-grep scanning with real temporal validation of:
- Feature timestamp <= label cutoff
- Bar visible_at <= decision_time
- Forward label visibility declared and isolated
- Train/test/OOS windows non-overlapping
- FactorSnapshotProtocol timing proof
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from qts.core.hashing import stable_json_hash


@dataclass(frozen=True, slots=True)
class NoLookaheadViolation:
    """One detected lookahead violation with structured evidence."""

    code: str
    message: str
    feature_name: str | None = None
    feature_timestamp: str | None = None
    cutoff_timestamp: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("code is required")
        if not self.message.strip():
            raise ValueError("message is required")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready violation payload."""

        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.feature_name is not None:
            payload["feature_name"] = self.feature_name
        if self.feature_timestamp is not None:
            payload["feature_timestamp"] = self.feature_timestamp
        if self.cutoff_timestamp is not None:
            payload["cutoff_timestamp"] = self.cutoff_timestamp
        return payload


@dataclass(frozen=True, slots=True)
class FeatureTimingSpec:
    """Timing specification for one feature used in a research pipeline."""

    name: str
    timestamp: datetime
    visible_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name is required")
        if self.visible_at is not None and self.visible_at < self.timestamp:
            raise ValueError(f"visible_at must be >= timestamp for feature {self.name}")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready feature timing payload."""

        payload: dict[str, Any] = {
            "name": self.name,
            "timestamp": _format_timestamp(self.timestamp),
        }
        if self.visible_at is not None:
            payload["visible_at"] = _format_timestamp(self.visible_at)
        return payload


@dataclass(frozen=True, slots=True)
class LabelPolicy:
    """Forward label visibility and isolation declaration."""

    horizon_bars: int
    visible_after: str
    no_lookahead: bool = True

    def __post_init__(self) -> None:
        if self.horizon_bars < 1:
            raise ValueError("horizon_bars must be positive")
        if not self.visible_after.strip():
            raise ValueError("visible_after is required")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready label policy payload."""

        return {
            "horizon_bars": self.horizon_bars,
            "no_lookahead": self.no_lookahead,
            "visible_after": self.visible_after,
        }


@dataclass(frozen=True, slots=True)
class ValidationWindow:
    """One train/test/OOS validation window with role and temporal bounds."""

    name: str
    role: str
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name is required")
        if self.role not in {"train", "test", "out_of_sample"}:
            raise ValueError(f"unsupported window role: {self.role}")
        if self.start >= self.end:
            raise ValueError("window start must be before end")

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready window payload."""

        return {
            "end": _format_timestamp(self.end),
            "name": self.name,
            "role": self.role,
            "start": _format_timestamp(self.start),
        }


@dataclass(frozen=True, slots=True)
class NoLookaheadValidationResult:
    """Complete no-lookahead validation result with timing proof."""

    passed: bool
    checked_features: tuple[str, ...]
    label_horizon: int | None
    max_feature_timestamp: str | None
    min_label_cutoff: str | None
    violations: tuple[NoLookaheadViolation, ...]
    window_overlaps: tuple[str, ...]
    string_scan_only: bool
    payload_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "checked_features", tuple(self.checked_features))
        object.__setattr__(self, "violations", tuple(self.violations))
        object.__setattr__(self, "window_overlaps", tuple(self.window_overlaps))

    def to_payload(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready validation payload."""

        return {
            "checked_features": list(self.checked_features),
            "label_horizon": self.label_horizon,
            "max_feature_timestamp": self.max_feature_timestamp,
            "min_label_cutoff": self.min_label_cutoff,
            "passed": self.passed,
            "payload_hash": self.payload_hash,
            "string_scan_only": self.string_scan_only,
            "violations": [v.to_payload() for v in self.violations],
            "window_overlaps": list(self.window_overlaps),
        }


class NoLookaheadValidationRunner:
    """Owns timing-protocol-level no-lookahead validation.

    Consumes workflow summary, manifest windows, factor snapshot / label
    policy, and feature timing specs. Validates that:
    - Every feature timestamp <= label cutoff
    - Bar visible_at <= decision_time when provided
    - Forward label visibility is declared and isolated
    - Train/test/OOS windows are non-overlapping
    - FactorSnapshotProtocol timing constraints hold

    Writes no_lookahead.json with checked_features, label_horizon,
    max_feature_timestamp, min_label_cutoff, violations, and payload_hash.
    """

    def __init__(
        self,
        *,
        features: Sequence[FeatureTimingSpec] = (),
        label_policy: LabelPolicy | None = None,
        windows: Sequence[ValidationWindow] = (),
        factor_snapshot_protocol: Mapping[str, Any] | None = None,
        decision_time: datetime | None = None,
    ) -> None:
        self._features = tuple(features)
        self._label_policy = label_policy
        self._windows = tuple(windows)
        self._factor_snapshot_protocol = factor_snapshot_protocol
        self._decision_time = decision_time

    def validate(self) -> NoLookaheadValidationResult:
        """Run all timing-protocol no-lookahead checks."""

        violations: list[NoLookaheadViolation] = []
        window_overlaps: list[str] = []

        # 1. Feature timestamp <= label cutoff
        feature_violations = self._check_feature_timestamps()
        violations.extend(feature_violations)

        # 2. Bar visible_at <= decision_time
        visibility_violations = self._check_bar_visibility()
        violations.extend(visibility_violations)

        # 3. Forward label visibility declared and isolated
        label_violations = self._check_label_policy()
        violations.extend(label_violations)

        # 4. Train/test/OOS windows non-overlapping
        overlap_violations = self._check_window_overlaps()
        window_overlaps.extend(overlap_violations)

        # 5. FactorSnapshotProtocol timing proof
        protocol_violations = self._check_factor_snapshot_protocol()
        violations.extend(protocol_violations)

        checked_features = tuple(feature.name for feature in self._features)
        label_horizon = self._label_policy.horizon_bars if self._label_policy else None
        max_feature_ts = self._max_feature_timestamp()
        min_label_cutoff = self._min_label_cutoff()

        payload = self._build_payload(
            checked_features=checked_features,
            label_horizon=label_horizon,
            max_feature_timestamp=max_feature_ts,
            min_label_cutoff=min_label_cutoff,
            violations=violations,
            window_overlaps=window_overlaps,
        )
        payload_hash = stable_json_hash(payload)

        passed = not violations and not window_overlaps

        return NoLookaheadValidationResult(
            passed=passed,
            checked_features=checked_features,
            label_horizon=label_horizon,
            max_feature_timestamp=max_feature_ts,
            min_label_cutoff=min_label_cutoff,
            violations=tuple(violations),
            window_overlaps=tuple(window_overlaps),
            string_scan_only=False,
            payload_hash=payload_hash,
        )

    @classmethod
    def from_payloads(
        cls,
        *,
        features: Sequence[Mapping[str, Any]] = (),
        label_policy: Mapping[str, Any] | None = None,
        windows: Sequence[Mapping[str, Any]] = (),
        factor_snapshot_protocol: Mapping[str, Any] | None = None,
        decision_time: datetime | None = None,
    ) -> NoLookaheadValidationRunner:
        """Construct a runner from raw JSON-like payload mappings."""

        feature_specs = tuple(
            FeatureTimingSpec(
                name=cls._required_text(f, "name"),
                timestamp=cls._required_datetime(f, "timestamp"),
                visible_at=(_optional_datetime(f, "visible_at") if "visible_at" in f else None),
            )
            for f in features
        )
        policy = (
            LabelPolicy(
                horizon_bars=cls._required_int(label_policy, "horizon_bars"),
                visible_after=cls._required_text(label_policy, "visible_after"),
                no_lookahead=_bool_field(label_policy, "no_lookahead", default=True),
            )
            if label_policy is not None
            else None
        )
        window_specs = tuple(
            ValidationWindow(
                name=cls._required_text(w, "name"),
                role=cls._required_text(w, "role"),
                start=cls._required_datetime(w, "start"),
                end=cls._required_datetime(w, "end"),
            )
            for w in windows
        )
        return cls(
            features=feature_specs,
            label_policy=policy,
            windows=window_specs,
            factor_snapshot_protocol=factor_snapshot_protocol,
            decision_time=decision_time,
        )

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()

    @staticmethod
    def _required_int(payload: Mapping[str, Any], field_name: str) -> int:
        value = payload.get(field_name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{field_name} must be an integer")
        return value

    @staticmethod
    def _required_datetime(payload: Mapping[str, Any], field_name: str) -> datetime:
        value = payload.get(field_name)
        if value is None:
            raise ValueError(f"{field_name} is required")
        return NoLookaheadValidationRunner._parse_datetime(value)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        """Parse a value into a timezone-aware datetime."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=UTC)
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min, tzinfo=UTC)
        if isinstance(value, str):
            text = value
            if text.endswith("Z"):
                text = f"{text[:-1]}+00:00"
            if "T" not in text:
                return datetime.combine(date.fromisoformat(text), time.min, tzinfo=UTC)
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed
        raise ValueError(f"cannot parse datetime from {type(value).__name__}")

    def _check_feature_timestamps(self) -> list[NoLookaheadViolation]:
        """Check that every feature timestamp <= label cutoff / decision time."""

        violations: list[NoLookaheadViolation] = []
        cutoff = self._effective_label_cutoff()

        for feature in self._features:
            if cutoff is not None and feature.timestamp > cutoff:
                violations.append(
                    NoLookaheadViolation(
                        code="feature_exceeds_label_cutoff",
                        message=(
                            f"feature '{feature.name}' timestamp "
                            f"{_format_timestamp(feature.timestamp)} exceeds "
                            f"label cutoff {_format_timestamp(cutoff)}"
                        ),
                        feature_name=feature.name,
                        feature_timestamp=_format_timestamp(feature.timestamp),
                        cutoff_timestamp=_format_timestamp(cutoff),
                    )
                )

            # Detect forward-return-style features by name pattern
            name_lower = feature.name.lower()
            if any(
                term in name_lower
                for term in ("future_return", "forward_return", "future_shift", "lead")
            ):
                violations.append(
                    NoLookaheadViolation(
                        code="forward_return_feature_detected",
                        message=(
                            f"feature '{feature.name}' is a forward/lookahead "
                            f"feature by name convention"
                        ),
                        feature_name=feature.name,
                        feature_timestamp=_format_timestamp(feature.timestamp),
                        cutoff_timestamp=(
                            _format_timestamp(cutoff) if cutoff is not None else None
                        ),
                    )
                )

        return violations

    def _check_bar_visibility(self) -> list[NoLookaheadViolation]:
        """Check that bar visible_at <= decision_time for each feature."""

        violations: list[NoLookaheadViolation] = []
        if self._decision_time is None:
            return violations

        for feature in self._features:
            if feature.visible_at is not None and feature.visible_at > self._decision_time:
                violations.append(
                    NoLookaheadViolation(
                        code="bar_not_yet_visible",
                        message=(
                            f"feature '{feature.name}' visible_at "
                            f"{_format_timestamp(feature.visible_at)} exceeds "
                            f"decision_time {_format_timestamp(self._decision_time)}"
                        ),
                        feature_name=feature.name,
                        feature_timestamp=_format_timestamp(feature.visible_at),
                        cutoff_timestamp=_format_timestamp(self._decision_time),
                    )
                )
        return violations

    def _check_label_policy(self) -> list[NoLookaheadViolation]:
        """Check forward label visibility is declared and isolated."""

        violations: list[NoLookaheadViolation] = []
        if self._label_policy is None:
            return violations

        if not self._label_policy.no_lookahead:
            violations.append(
                NoLookaheadViolation(
                    code="label_no_lookahead_not_declared",
                    message="label policy does not declare no_lookahead=true",
                )
            )

        if self._label_policy.visible_after not in {
            "bar_close",
            "session_close",
            "next_session_open",
        }:
            violations.append(
                NoLookaheadViolation(
                    code="label_visibility_undeclared",
                    message=(
                        f"label policy visible_after='{self._label_policy.visible_after}' "
                        f"is not a recognized visibility boundary"
                    ),
                )
            )

        return violations

    def _check_window_overlaps(self) -> list[str]:
        """Check train/test/OOS windows are non-overlapping."""

        overlaps: list[str] = []
        if len(self._windows) < 2:
            return overlaps

        sorted_windows = sorted(self._windows, key=lambda w: w.start)
        for i in range(len(sorted_windows) - 1):
            current = sorted_windows[i]
            next_window = sorted_windows[i + 1]
            if current.end > next_window.start:
                overlaps.append(
                    f"window '{current.name}' ({current.role}) overlaps "
                    f"window '{next_window.name}' ({next_window.role})"
                )
        return overlaps

    def _check_factor_snapshot_protocol(self) -> list[NoLookaheadViolation]:
        """Check FactorSnapshotProtocol timing constraints."""

        violations: list[NoLookaheadViolation] = []
        protocol = self._factor_snapshot_protocol
        if protocol is None:
            return violations

        try:
            source_data_end = _protocol_datetime(protocol.get("source_data_end"))
            available_at = _protocol_datetime(protocol.get("available_at"))
            forward_return_start = _protocol_datetime(protocol.get("forward_return_start"))
            forward_return_end = _protocol_datetime(protocol.get("forward_return_end"))
        except (ValueError, TypeError, KeyError):
            violations.append(
                NoLookaheadViolation(
                    code="factor_snapshot_protocol_malformed",
                    message="FactorSnapshotProtocol fields are missing or unparseable",
                )
            )
            return violations

        if source_data_end > available_at:
            violations.append(
                NoLookaheadViolation(
                    code="source_data_exceeds_available_at",
                    message=(
                        f"source_data_end {_format_timestamp(source_data_end)} "
                        f"exceeds available_at {_format_timestamp(available_at)}"
                    ),
                    feature_timestamp=_format_timestamp(source_data_end),
                    cutoff_timestamp=_format_timestamp(available_at),
                )
            )

        if available_at > forward_return_start:
            violations.append(
                NoLookaheadViolation(
                    code="available_at_exceeds_forward_return_start",
                    message=(
                        f"available_at {_format_timestamp(available_at)} exceeds "
                        f"forward_return_start {_format_timestamp(forward_return_start)}"
                    ),
                    feature_timestamp=_format_timestamp(available_at),
                    cutoff_timestamp=_format_timestamp(forward_return_start),
                )
            )

        if forward_return_start >= forward_return_end:
            violations.append(
                NoLookaheadViolation(
                    code="forward_return_start_exceeds_end",
                    message=(
                        f"forward_return_start {_format_timestamp(forward_return_start)} "
                        f"must be before forward_return_end "
                        f"{_format_timestamp(forward_return_end)}"
                    ),
                )
            )

        return violations

    def _effective_label_cutoff(self) -> datetime | None:
        """Derive the label cutoff from label policy, windows, or decision time."""

        if self._label_policy is not None and self._decision_time is not None:
            return self._decision_time
        if self._decision_time is not None:
            return self._decision_time
        if self._windows:
            # Use the start of the first test/OOS window as the cutoff
            for window in sorted(self._windows, key=lambda w: w.start):
                if window.role in {"test", "out_of_sample"}:
                    return window.start
        return None

    def _max_feature_timestamp(self) -> str | None:
        """Return the latest feature timestamp as ISO string."""

        if not self._features:
            return None
        latest = max(feature.timestamp for feature in self._features)
        return _format_timestamp(latest)

    def _min_label_cutoff(self) -> str | None:
        """Return the earliest label cutoff as ISO string."""

        cutoff = self._effective_label_cutoff()
        if cutoff is None:
            return None
        return _format_timestamp(cutoff)

    @staticmethod
    def _build_payload(
        *,
        checked_features: tuple[str, ...],
        label_horizon: int | None,
        max_feature_timestamp: str | None,
        min_label_cutoff: str | None,
        violations: list[NoLookaheadViolation],
        window_overlaps: list[str],
    ) -> dict[str, Any]:
        """Build the deterministic payload for hashing (excludes payload_hash itself)."""

        return {
            "checked_features": list(checked_features),
            "label_horizon": label_horizon,
            "max_feature_timestamp": max_feature_timestamp,
            "min_label_cutoff": min_label_cutoff,
            "passed": not violations and not window_overlaps,
            "violations": [v.to_payload() for v in violations],
            "window_overlaps": list(window_overlaps),
        }


def _bool_field(payload: Mapping[str, Any], field_name: str, *, default: bool) -> bool:
    value = payload.get(field_name, default)
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _optional_datetime(payload: Mapping[str, Any], field_name: str) -> datetime | None:
    value = payload.get(field_name)
    if value is None:
        return None
    return NoLookaheadValidationRunner._parse_datetime(value)


def _protocol_datetime(value: Any) -> datetime:
    """Parse a protocol field value into a timezone-aware datetime."""

    return NoLookaheadValidationRunner._parse_datetime(value)


def _format_timestamp(value: datetime) -> str:
    """Format a datetime for deterministic JSON output."""

    if value.time() == time.min and value.utcoffset() == timedelta(0):
        return value.date().isoformat()
    return value.isoformat()


__all__ = [
    "FeatureTimingSpec",
    "LabelPolicy",
    "NoLookaheadValidationResult",
    "NoLookaheadValidationRunner",
    "NoLookaheadViolation",
    "ValidationWindow",
]
