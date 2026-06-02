"""Walk-forward validation artifact ownership tests."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qts.research.orchestrator.walk_forward_validation_artifact import (
    WalkForwardValidationArtifact,
)


def test_walk_forward_validation_artifact_accepts_consistent_positive_test_window() -> None:
    payload = WalkForwardValidationArtifact().payload(
        train_objective_value=Decimal("1.00"),
        train_manifest={"manifest_hash": "train-hash"},
        train_manifest_path=Path("train.json"),
        test_objective_value=Decimal("0.90"),
        test_manifest={"manifest_hash": "test-hash", "statistics_hash": "stats-hash"},
        test_manifest_path=Path("test.json"),
    )

    assert payload["consistent"] is True
    assert payload["test_windows"][0]["accepted"] is True
    assert payload["max_train_test_gap"] == 0.1
    assert payload["manifest_statistics_hash"] == "stats-hash"


def test_walk_forward_validation_artifact_rejects_losing_or_unstable_test_window() -> None:
    losing = WalkForwardValidationArtifact().payload(
        train_objective_value=Decimal("1.00"),
        train_manifest={"manifest_hash": "train-hash"},
        train_manifest_path=Path("train.json"),
        test_objective_value=Decimal("-0.01"),
        test_manifest={"manifest_hash": "test-hash"},
        test_manifest_path=Path("test.json"),
    )
    unstable = WalkForwardValidationArtifact().payload(
        train_objective_value=Decimal("2.00"),
        train_manifest={"manifest_hash": "train-hash"},
        train_manifest_path=Path("train.json"),
        test_objective_value=Decimal("0.10"),
        test_manifest={"manifest_hash": "test-hash"},
        test_manifest_path=Path("test.json"),
    )

    assert losing["consistent"] is False
    assert losing["test_windows"][0]["accepted"] is False
    assert unstable["consistent"] is False
    assert unstable["test_windows"][0]["accepted"] is False
