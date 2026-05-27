from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from qts.research.data_quality import (
    DataQualityArtifact,
    DataQualityArtifactWriter,
    DataQualityIssue,
)


def test_dataset_snapshot_with_existing_paths_is_accepted(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    labels_path = tmp_path / "labels.csv"
    bars_path.write_text("timestamp,close\n2026-01-02T14:30:00Z,100\n", encoding="utf-8")
    labels_path.write_text(
        "timestamp,forward_return\n2026-01-02T14:31:00Z,0.01\n",
        encoding="utf-8",
    )

    artifact = DataQualityArtifact.from_dataset_snapshot(
        {
            "dataset_id": "dataset-001",
            "checked_paths": [bars_path, labels_path],
        }
    )

    assert artifact.schema_version == 2
    assert artifact.dataset_id == "dataset-001"
    assert artifact.accepted is True
    assert artifact.checked_paths == (str(bars_path), str(labels_path))
    assert artifact.blockers() == ()


def test_missing_checked_path_creates_blocker_issue(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing.csv"

    artifact = DataQualityArtifact.from_dataset_snapshot(
        {
            "dataset_id": "dataset-001",
            "checked_paths": [missing_path],
        }
    )

    assert artifact.accepted is False
    assert artifact.blockers() == (
        {"code": "missing_checked_path", "message": f"checked path does not exist: {missing_path}"},
        {"code": "accepted", "message": "data quality artifact is not accepted"},
    )


def test_empty_checked_paths_and_manual_rejection_create_blockers() -> None:
    artifact = DataQualityArtifact.from_payload(
        {
            "schema_version": 2,
            "dataset_id": "dataset-001",
            "accepted": False,
            "checked_paths": [],
            "issues": [],
            "duplicate_timestamps": 0,
            "missing_bars": 0,
            "session_alignment": True,
            "stale_prices": 0,
            "halted_sessions": 0,
            "label_visibility": True,
        }
    )

    assert artifact.accepted is False
    assert artifact.blockers() == (
        {"code": "checked_paths", "message": "checked_paths must not be empty"},
        {"code": "accepted", "message": "data quality artifact is not accepted"},
    )


def test_critical_quality_flags_create_blockers(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text("timestamp,close\n2026-01-02T14:30:00Z,100\n", encoding="utf-8")

    artifact = DataQualityArtifact.from_dataset_snapshot(
        {
            "dataset_id": "dataset-001",
            "file_paths": [bars_path],
            "duplicate_timestamps": 2,
            "session_alignment": False,
            "label_visibility": False,
        }
    )

    assert artifact.accepted is False
    assert artifact.blockers() == (
        {"code": "accepted", "message": "data quality artifact is not accepted"},
        {"code": "duplicate_timestamps", "message": "duplicate timestamps detected: 2"},
        {"code": "session_alignment", "message": "session alignment check failed"},
        {"code": "label_visibility", "message": "label visibility check failed"},
    )


def test_payload_round_trips_json_safe_values(tmp_path: Path) -> None:
    bars_path = tmp_path / "bars.csv"
    bars_path.write_text("timestamp,close\n2026-01-02T14:30:00Z,100\n", encoding="utf-8")
    artifact = DataQualityArtifact(
        dataset_id="dataset-001",
        accepted=False,
        checked_paths=(str(bars_path),),
        issues=(
            DataQualityIssue(
                code="manual_review_required",
                message="review split boundary before promotion",
                blocker=True,
            ),
        ),
        duplicate_timestamps=0,
        missing_bars=3,
        session_alignment=True,
        stale_prices=0,
        halted_sessions=0,
        label_visibility=True,
    )

    payload = artifact.to_payload()
    encoded = json.dumps(payload, sort_keys=True)
    restored = DataQualityArtifact.from_payload(json.loads(encoded))

    assert restored == artifact
    assert restored.blockers() == (
        {
            "code": "manual_review_required",
            "message": "review split boundary before promotion",
        },
        {"code": "accepted", "message": "data quality artifact is not accepted"},
        {"code": "missing_bars", "message": "missing bars detected: 3"},
    )


def test_from_payload_derives_accepted_from_blockers() -> None:
    restored = DataQualityArtifact.from_payload(
        {
            "schema_version": 2,
            "dataset_id": "dataset-001",
            "accepted": True,
            "checked_paths": [],
            "issues": [
                {
                    "code": "manual_review_required",
                    "message": "review split boundary before promotion",
                    "blocker": True,
                }
            ],
            "duplicate_timestamps": 1,
            "missing_bars": 0,
            "session_alignment": False,
            "stale_prices": 0,
            "halted_sessions": 0,
            "label_visibility": True,
        }
    )

    assert restored.accepted is False
    assert restored.blockers() == (
        {
            "code": "manual_review_required",
            "message": "review split boundary before promotion",
        },
        {"code": "checked_paths", "message": "checked_paths must not be empty"},
        {"code": "accepted", "message": "data quality artifact is not accepted"},
        {"code": "duplicate_timestamps", "message": "duplicate timestamps detected: 1"},
        {"code": "session_alignment", "message": "session alignment check failed"},
    )


def test_from_payload_preserves_manual_rejection_as_blocker() -> None:
    restored = DataQualityArtifact.from_payload(
        {
            "schema_version": 2,
            "dataset_id": "dataset-001",
            "accepted": False,
            "checked_paths": ["datasets/dataset-001/bars.csv"],
            "issues": [],
            "duplicate_timestamps": 0,
            "missing_bars": 0,
            "session_alignment": True,
            "stale_prices": 0,
            "halted_sessions": 0,
            "label_visibility": True,
        }
    )

    assert restored.accepted is False
    assert restored.blockers() == (
        {"code": "accepted", "message": "data quality artifact is not accepted"},
    )


def test_data_quality_boolean_fields_must_be_real_booleans() -> None:
    payload = {
        "schema_version": 2,
        "dataset_id": "dataset-001",
        "accepted": True,
        "checked_paths": [],
        "issues": [],
        "duplicate_timestamps": 0,
        "missing_bars": 0,
        "session_alignment": "false",
        "stale_prices": 0,
        "halted_sessions": 0,
        "label_visibility": True,
    }

    with pytest.raises(ValueError, match="session_alignment must be bool"):
        DataQualityArtifact.from_payload(payload)

    with pytest.raises(ValueError, match="label_visibility must be bool"):
        DataQualityArtifact.from_dataset_snapshot(
            {
                "dataset_id": "dataset-001",
                "checked_paths": [],
                "label_visibility": "false",
            }
        )


def test_data_quality_issue_blocker_must_be_real_boolean() -> None:
    with pytest.raises(ValueError, match="blocker must be bool"):
        DataQualityArtifact.from_payload(
            {
                "schema_version": 2,
                "dataset_id": "dataset-001",
                "accepted": True,
                "checked_paths": [],
                "issues": [
                    {
                        "code": "manual_review_required",
                        "message": "review before promotion",
                        "blocker": "false",
                    }
                ],
                "duplicate_timestamps": 0,
                "missing_bars": 0,
                "session_alignment": True,
                "stale_prices": 0,
                "halted_sessions": 0,
                "label_visibility": True,
            }
        )


def test_writer_emits_deterministic_canonical_json_and_hash(tmp_path: Path) -> None:
    artifact = DataQualityArtifact.from_dataset_snapshot(
        {
            "dataset_id": "dataset-001",
            "checked_paths": [],
            "missing_bars": 1,
        }
    )
    writer = DataQualityArtifactWriter(tmp_path)

    result = writer.write(artifact)

    expected_body = json.dumps(
        artifact.to_payload(include_artifact_hash=False),
        sort_keys=True,
        separators=(",", ":"),
    )
    expected_hash = f"sha256:{hashlib.sha256(expected_body.encode('utf-8')).hexdigest()}"
    payload = json.loads(result.path.read_text(encoding="utf-8"))

    assert result.path.parent == tmp_path
    assert result.path.name.endswith("_data_quality.json")
    assert result.artifact_hash == expected_hash
    assert payload == artifact.to_payload(include_artifact_hash=True, artifact_hash=expected_hash)


def test_writer_keeps_dataset_id_out_of_output_path_traversal(tmp_path: Path) -> None:
    artifact = DataQualityArtifact(
        dataset_id="../escape",
        accepted=True,
        checked_paths=(),
    )
    writer = DataQualityArtifactWriter(tmp_path)

    result = writer.write(artifact)

    assert result.path.parent == tmp_path
    assert result.path.resolve().is_relative_to(tmp_path.resolve())
