"""Unit tests for NoLookaheadValidationRunner timing-protocol validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from qts.research.validation import (
    FeatureTimingSpec,
    LabelPolicy,
    NoLookaheadArtifactWriter,
    NoLookaheadValidationResult,
    NoLookaheadValidationRunner,
    NoLookaheadViolation,
    ValidationWindow,
)

# ---------------------------------------------------------------------------
# FeatureTimingSpec
# ---------------------------------------------------------------------------


class TestFeatureTimingSpec:
    def test_valid_spec(self) -> None:
        spec = FeatureTimingSpec(name="momentum_5", timestamp=datetime(2026, 1, 1, tzinfo=UTC))
        assert spec.name == "momentum_5"
        assert spec.visible_at is None

    def test_valid_with_visible_at(self) -> None:
        ts = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
        va = datetime(2026, 1, 1, 12, 1, tzinfo=UTC)
        spec = FeatureTimingSpec(name="close", timestamp=ts, visible_at=va)
        assert spec.visible_at == va

    def test_visible_at_before_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError, match="visible_at must be >= timestamp"):
            FeatureTimingSpec(
                name="bad",
                timestamp=datetime(2026, 1, 1, 12, 1, tzinfo=UTC),
                visible_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            )

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValueError, match="name is required"):
            FeatureTimingSpec(name="", timestamp=datetime(2026, 1, 1, tzinfo=UTC))

    def test_to_payload(self) -> None:
        spec = FeatureTimingSpec(
            name="rsi",
            timestamp=datetime(2026, 3, 15, tzinfo=UTC),
            visible_at=datetime(2026, 3, 15, 0, 1, tzinfo=UTC),
        )
        payload = spec.to_payload()
        assert payload["name"] == "rsi"
        assert "timestamp" in payload
        assert "visible_at" in payload


# ---------------------------------------------------------------------------
# LabelPolicy
# ---------------------------------------------------------------------------


class TestLabelPolicy:
    def test_valid_policy(self) -> None:
        policy = LabelPolicy(horizon_bars=5, visible_after="bar_close")
        assert policy.horizon_bars == 5
        assert policy.no_lookahead is True

    def test_zero_horizon_rejected(self) -> None:
        with pytest.raises(ValueError, match="horizon_bars must be positive"):
            LabelPolicy(horizon_bars=0, visible_after="bar_close")

    def test_empty_visible_after_rejected(self) -> None:
        with pytest.raises(ValueError, match="visible_after is required"):
            LabelPolicy(horizon_bars=5, visible_after="")

    def test_no_lookahead_false(self) -> None:
        policy = LabelPolicy(horizon_bars=5, visible_after="bar_close", no_lookahead=False)
        assert policy.no_lookahead is False


# ---------------------------------------------------------------------------
# ValidationWindow
# ---------------------------------------------------------------------------


class TestValidationWindow:
    def test_valid_window(self) -> None:
        w = ValidationWindow(
            name="train-1",
            role="train",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 6, 1, tzinfo=UTC),
        )
        assert w.role == "train"

    def test_invalid_role_rejected(self) -> None:
        with pytest.raises(ValueError, match="unsupported window role"):
            ValidationWindow(
                name="bad",
                role="invalid",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 6, 1, tzinfo=UTC),
            )

    def test_start_after_end_rejected(self) -> None:
        with pytest.raises(ValueError, match="start must be before end"):
            ValidationWindow(
                name="bad",
                role="train",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 1, 1, tzinfo=UTC),
            )


# ---------------------------------------------------------------------------
# NoLookaheadValidationRunner - basic validation
# ---------------------------------------------------------------------------


class TestNoLookaheadValidationRunnerBasic:
    def test_empty_inputs_pass(self) -> None:
        result = NoLookaheadValidationRunner().validate()
        assert result.passed is True
        assert result.violations == ()
        assert result.window_overlaps == ()
        assert result.string_scan_only is False

    def test_valid_features_pass(self) -> None:
        features = [
            FeatureTimingSpec(name="momentum", timestamp=datetime(2026, 1, 1, tzinfo=UTC)),
            FeatureTimingSpec(name="volatility", timestamp=datetime(2026, 1, 2, tzinfo=UTC)),
        ]
        decision_time = datetime(2026, 6, 1, tzinfo=UTC)
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=decision_time,
        ).validate()
        assert result.passed is True
        assert result.checked_features == ("momentum", "volatility")

    def test_result_payload_is_deterministic(self) -> None:
        features = [
            FeatureTimingSpec(name="a", timestamp=datetime(2026, 1, 1, tzinfo=UTC)),
        ]
        result1 = NoLookaheadValidationRunner(features=features).validate()
        result2 = NoLookaheadValidationRunner(features=features).validate()
        assert result1.payload_hash == result2.payload_hash

    def test_artifact_writer(self, tmp_path: object) -> None:
        import pathlib

        tmp = pathlib.Path(str(tmp_path))
        result = NoLookaheadValidationRunner().validate()
        path = NoLookaheadArtifactWriter(tmp / "validation").write(result)
        assert path.exists()
        assert path.name == "no_lookahead.json"
        import json

        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["passed"] is True
        assert "payload_hash" in loaded


# ---------------------------------------------------------------------------
# Acceptance criterion: deliberate future_return feature is rejected
# ---------------------------------------------------------------------------


class TestFutureReturnFeatureRejected:
    def test_future_return_feature_rejected_even_with_valid_timestamp(self) -> None:
        """A feature named future_return is rejected regardless of its timestamp."""
        features = [
            FeatureTimingSpec(
                name="future_return_5",
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ]
        decision_time = datetime(2026, 6, 1, tzinfo=UTC)
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=decision_time,
        ).validate()
        assert result.passed is False
        assert any(v.code == "forward_return_feature_detected" for v in result.violations)

    def test_forward_return_feature_rejected(self) -> None:
        features = [
            FeatureTimingSpec(
                name="forward_return_10",
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=datetime(2026, 6, 1, tzinfo=UTC),
        ).validate()
        assert result.passed is False
        assert any(v.code == "forward_return_feature_detected" for v in result.violations)

    def test_future_shift_feature_rejected(self) -> None:
        features = [
            FeatureTimingSpec(
                name="future_shift_3",
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=datetime(2026, 6, 1, tzinfo=UTC),
        ).validate()
        assert result.passed is False
        assert any(v.code == "forward_return_feature_detected" for v in result.violations)

    def test_legitimate_momentum_feature_passes(self) -> None:
        """A legitimate feature name does not trigger forward_return detection."""
        features = [
            FeatureTimingSpec(
                name="momentum_10",
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=datetime(2026, 6, 1, tzinfo=UTC),
        ).validate()
        assert result.passed is True


# ---------------------------------------------------------------------------
# Acceptance criterion: label with horizon leaking into train selection
# ---------------------------------------------------------------------------


class TestLabelHorizonLeakageRejected:
    def test_feature_exceeds_label_cutoff_rejected(self) -> None:
        """Feature with timestamp after label cutoff is a lookahead violation."""
        features = [
            FeatureTimingSpec(
                name="leaky_feature",
                timestamp=datetime(2026, 6, 15, tzinfo=UTC),
            ),
        ]
        # The decision_time is the label cutoff - feature is after it
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=datetime(2026, 6, 1, tzinfo=UTC),
        ).validate()
        assert result.passed is False
        assert any(v.code == "feature_exceeds_label_cutoff" for v in result.violations)

    def test_feature_at_cutoff_boundary_passes(self) -> None:
        """Feature exactly at the cutoff is allowed (<= semantics)."""
        cutoff = datetime(2026, 6, 1, tzinfo=UTC)
        features = [
            FeatureTimingSpec(name="ok_feature", timestamp=cutoff),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=cutoff,
        ).validate()
        assert result.passed is True

    def test_label_policy_no_lookahead_false_rejected(self) -> None:
        """Label policy with no_lookahead=False is rejected."""
        policy = LabelPolicy(horizon_bars=5, visible_after="bar_close", no_lookahead=False)
        result = NoLookaheadValidationRunner(label_policy=policy).validate()
        assert result.passed is False
        assert any(v.code == "label_no_lookahead_not_declared" for v in result.violations)

    def test_label_policy_unrecognized_visible_after_rejected(self) -> None:
        """Label policy with unrecognized visible_after is rejected."""
        policy = LabelPolicy(horizon_bars=5, visible_after="instantly", no_lookahead=True)
        result = NoLookaheadValidationRunner(label_policy=policy).validate()
        assert result.passed is False
        assert any(v.code == "label_visibility_undeclared" for v in result.violations)

    def test_label_horizon_windows_oos_as_cutoff(self) -> None:
        """When no decision_time, the first OOS window start is the cutoff."""
        features = [
            FeatureTimingSpec(
                name="leaky",
                timestamp=datetime(2026, 7, 1, tzinfo=UTC),
            ),
        ]
        windows = [
            ValidationWindow(
                name="train",
                role="train",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 6, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="oos",
                role="out_of_sample",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 12, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            windows=windows,
        ).validate()
        # Feature is at 2026-07-01, cutoff is 2026-06-01 (OOS start)
        assert result.passed is False
        assert result.min_label_cutoff == "2026-06-01"


# ---------------------------------------------------------------------------
# Acceptance criterion: non-overlapping train/test/OOS windows pass
# ---------------------------------------------------------------------------


class TestNonOverlappingWindowsPass:
    def test_non_overlapping_windows_pass(self) -> None:
        windows = [
            ValidationWindow(
                name="train",
                role="train",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 6, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="test",
                role="test",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 9, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="oos",
                role="out_of_sample",
                start=datetime(2026, 9, 1, tzinfo=UTC),
                end=datetime(2026, 12, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(windows=windows).validate()
        assert result.passed is True
        assert result.window_overlaps == ()

    def test_overlapping_windows_rejected(self) -> None:
        windows = [
            ValidationWindow(
                name="train",
                role="train",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 7, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="test",
                role="test",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 9, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(windows=windows).validate()
        assert result.passed is False
        assert len(result.window_overlaps) == 1
        assert "train" in result.window_overlaps[0]
        assert "test" in result.window_overlaps[0]

    def test_touching_windows_pass(self) -> None:
        """Windows that touch at the boundary (end == start) are non-overlapping."""
        windows = [
            ValidationWindow(
                name="train",
                role="train",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 6, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="oos",
                role="out_of_sample",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 12, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(windows=windows).validate()
        assert result.passed is True


# ---------------------------------------------------------------------------
# Bar visibility check
# ---------------------------------------------------------------------------


class TestBarVisibilityCheck:
    def test_visible_at_after_decision_time_rejected(self) -> None:
        features = [
            FeatureTimingSpec(
                name="late_bar",
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                visible_at=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=datetime(2026, 6, 15, 11, 0, tzinfo=UTC),
        ).validate()
        assert result.passed is False
        assert any(v.code == "bar_not_yet_visible" for v in result.violations)

    def test_visible_at_equal_to_decision_time_passes(self) -> None:
        dt = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
        features = [
            FeatureTimingSpec(
                name="on_time",
                timestamp=datetime(2026, 1, 1, tzinfo=UTC),
                visible_at=dt,
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=dt,
        ).validate()
        assert result.passed is True


# ---------------------------------------------------------------------------
# FactorSnapshotProtocol timing proof
# ---------------------------------------------------------------------------


class TestFactorSnapshotProtocolTimingProof:
    def test_valid_protocol_passes(self) -> None:
        protocol = {
            "source_data_end": "2026-01-01",
            "available_at": "2026-01-01",
            "forward_return_start": "2026-01-02",
            "forward_return_end": "2026-01-03",
        }
        result = NoLookaheadValidationRunner(
            factor_snapshot_protocol=protocol,
        ).validate()
        assert result.passed is True

    def test_source_data_exceeds_available_at_rejected(self) -> None:
        protocol = {
            "source_data_end": "2026-01-02",
            "available_at": "2026-01-01",
            "forward_return_start": "2026-01-03",
            "forward_return_end": "2026-01-04",
        }
        result = NoLookaheadValidationRunner(
            factor_snapshot_protocol=protocol,
        ).validate()
        assert result.passed is False
        assert any(v.code == "source_data_exceeds_available_at" for v in result.violations)

    def test_available_at_exceeds_forward_return_start_rejected(self) -> None:
        protocol = {
            "source_data_end": "2026-01-01",
            "available_at": "2026-01-04",
            "forward_return_start": "2026-01-03",
            "forward_return_end": "2026-01-05",
        }
        result = NoLookaheadValidationRunner(
            factor_snapshot_protocol=protocol,
        ).validate()
        assert result.passed is False
        assert any(v.code == "available_at_exceeds_forward_return_start" for v in result.violations)

    def test_forward_return_start_exceeds_end_rejected(self) -> None:
        protocol = {
            "source_data_end": "2026-01-01",
            "available_at": "2026-01-01",
            "forward_return_start": "2026-01-05",
            "forward_return_end": "2026-01-04",
        }
        result = NoLookaheadValidationRunner(
            factor_snapshot_protocol=protocol,
        ).validate()
        assert result.passed is False
        assert any(v.code == "forward_return_start_exceeds_end" for v in result.violations)

    def test_malformed_protocol_rejected(self) -> None:
        protocol = {"source_data_end": "2026-01-01"}
        result = NoLookaheadValidationRunner(
            factor_snapshot_protocol=protocol,
        ).validate()
        assert result.passed is False
        assert any(v.code == "factor_snapshot_protocol_malformed" for v in result.violations)


# ---------------------------------------------------------------------------
# Acceptance criterion: string-only scan is NOT sufficient to pass
# ---------------------------------------------------------------------------


class TestStringOnlyScanInsufficient:
    def test_result_marks_string_scan_only_false(self) -> None:
        """Timing-protocol validation sets string_scan_only=False."""
        result = NoLookaheadValidationRunner().validate()
        assert result.string_scan_only is False

    def test_from_payloads_class_method(self) -> None:
        """from_payloads constructs a runner from raw mappings."""
        runner = NoLookaheadValidationRunner.from_payloads(
            features=[
                {"name": "momentum", "timestamp": "2026-01-01"},
                {"name": "vol", "timestamp": "2026-01-01"},
            ],
            label_policy={
                "horizon_bars": 5,
                "visible_after": "bar_close",
                "no_lookahead": True,
            },
            windows=[
                {
                    "name": "train",
                    "role": "train",
                    "start": "2026-01-01",
                    "end": "2026-06-01",
                },
                {
                    "name": "oos",
                    "role": "out_of_sample",
                    "start": "2026-06-01",
                    "end": "2026-12-01",
                },
            ],
        )
        result = runner.validate()
        assert result.passed is True
        assert result.checked_features == ("momentum", "vol")
        assert result.label_horizon == 5

    def test_no_lookahead_gate_rejects_string_only(self) -> None:
        """NoLookaheadGate in the gauntlet rejects string-only evidence."""
        from qts.research.selector.gauntlet import NoLookaheadGate

        # Simulate the old string-only format (no timing_validation key)
        candidate = {
            "candidate_id": "c-001",
            "validation": {
                "no_lookahead": {
                    "passed": True,
                    "forbidden_terms": ["future_return"],
                    "violations": [],
                    "string_scan_only": True,
                },
            },
        }
        gate = NoLookaheadGate()
        decision = gate.evaluate(candidate)
        assert decision.accepted is False
        assert any("string-only scan is insufficient" in reason for reason in decision.reasons)

    def test_no_lookahead_gate_rejects_missing_timing_validation(self) -> None:
        """NoLookaheadGate rejects evidence without timing_validation."""
        from qts.research.selector.gauntlet import NoLookaheadGate

        candidate = {
            "candidate_id": "c-001",
            "validation": {
                "no_lookahead": {
                    "passed": True,
                    "violations": [],
                    "forbidden_terms": ["future_return"],
                },
            },
        }
        gate = NoLookaheadGate()
        decision = gate.evaluate(candidate)
        assert decision.accepted is False
        assert any("timing_validation" in reason for reason in decision.reasons)

    def test_no_lookahead_gate_accepts_timing_validation(self) -> None:
        """NoLookaheadGate accepts evidence with valid timing_validation."""
        from qts.research.selector.gauntlet import NoLookaheadGate

        candidate = {
            "candidate_id": "c-001",
            "validation": {
                "no_lookahead": {
                    "passed": True,
                    "string_scan_only": False,
                    "string_scan_violations": [],
                    "timing_validation": {
                        "passed": True,
                        "checked_features": ["momentum"],
                        "violations": [],
                        "window_overlaps": [],
                    },
                    "violations": [],
                },
            },
        }
        gate = NoLookaheadGate()
        decision = gate.evaluate(candidate)
        assert decision.accepted is True


# ---------------------------------------------------------------------------
# NoLookaheadViolation
# ---------------------------------------------------------------------------


class TestNoLookaheadViolation:
    def test_to_payload_minimal(self) -> None:
        v = NoLookaheadViolation(code="test_code", message="test message")
        payload = v.to_payload()
        assert payload == {"code": "test_code", "message": "test message"}

    def test_to_payload_with_details(self) -> None:
        v = NoLookaheadViolation(
            code="feature_exceeds_label_cutoff",
            message="feature exceeds cutoff",
            feature_name="future_return",
            feature_timestamp="2026-06-15",
            cutoff_timestamp="2026-06-01",
        )
        payload = v.to_payload()
        assert payload["feature_name"] == "future_return"
        assert payload["feature_timestamp"] == "2026-06-15"
        assert payload["cutoff_timestamp"] == "2026-06-01"

    def test_empty_code_rejected(self) -> None:
        with pytest.raises(ValueError, match="code is required"):
            NoLookaheadViolation(code="", message="msg")

    def test_empty_message_rejected(self) -> None:
        with pytest.raises(ValueError, match="message is required"):
            NoLookaheadViolation(code="code", message="")


# ---------------------------------------------------------------------------
# NoLookaheadValidationResult
# ---------------------------------------------------------------------------


class TestNoLookaheadValidationResult:
    def test_to_payload_roundtrip(self) -> None:
        result = NoLookaheadValidationResult(
            passed=True,
            checked_features=("momentum", "vol"),
            label_horizon=5,
            max_feature_timestamp="2026-01-01",
            min_label_cutoff="2026-06-01",
            violations=(),
            window_overlaps=(),
            string_scan_only=False,
            payload_hash="sha256:abc",
        )
        payload = result.to_payload()
        assert payload["passed"] is True
        assert payload["checked_features"] == ["momentum", "vol"]
        assert payload["label_horizon"] == 5
        assert payload["payload_hash"] == "sha256:abc"


# ---------------------------------------------------------------------------
# Combined scenario: all acceptance criteria
# ---------------------------------------------------------------------------


class TestCombinedAcceptanceCriteria:
    def test_deliberate_future_return_rejected(self) -> None:
        """Acceptance: deliberate future_return feature is rejected."""
        features = [
            FeatureTimingSpec(
                name="future_return",
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            decision_time=datetime(2026, 6, 1, tzinfo=UTC),
        ).validate()
        assert result.passed is False

    def test_label_leaking_into_train_rejected(self) -> None:
        """Acceptance: label with horizon leaking into train selection is rejected."""
        features = [
            FeatureTimingSpec(
                name="leaky_label",
                timestamp=datetime(2026, 7, 1, tzinfo=UTC),
            ),
        ]
        windows = [
            ValidationWindow(
                name="train",
                role="train",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 6, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="oos",
                role="out_of_sample",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 12, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            windows=windows,
        ).validate()
        assert result.passed is False

    def test_non_overlapping_windows_pass(self) -> None:
        """Acceptance: non-overlapping train/test/OOS windows pass."""
        features = [
            FeatureTimingSpec(
                name="momentum",
                timestamp=datetime(2025, 12, 1, tzinfo=UTC),
            ),
        ]
        policy = LabelPolicy(horizon_bars=5, visible_after="bar_close")
        windows = [
            ValidationWindow(
                name="train",
                role="train",
                start=datetime(2026, 1, 1, tzinfo=UTC),
                end=datetime(2026, 6, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="test",
                role="test",
                start=datetime(2026, 6, 1, tzinfo=UTC),
                end=datetime(2026, 9, 1, tzinfo=UTC),
            ),
            ValidationWindow(
                name="oos",
                role="out_of_sample",
                start=datetime(2026, 9, 1, tzinfo=UTC),
                end=datetime(2026, 12, 1, tzinfo=UTC),
            ),
        ]
        result = NoLookaheadValidationRunner(
            features=features,
            label_policy=policy,
            windows=windows,
            decision_time=datetime(2026, 6, 1, tzinfo=UTC),
        ).validate()
        assert result.passed is True
        assert result.max_feature_timestamp == "2025-12-01"
        assert result.min_label_cutoff == "2026-06-01"
        assert result.label_horizon == 5
