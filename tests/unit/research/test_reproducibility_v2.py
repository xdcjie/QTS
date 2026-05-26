from pathlib import Path

import pytest
from qts.research.reproducibility import (
    ReproducibilitySnapshot,
    ReproducibilitySnapshotV2,
)


def test_reproducibility_snapshot_v2_collects_round_trippable_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = {
        ("rev-parse", "HEAD"): "abc123",
        ("status", "--short"): "",
    }
    monkeypatch.setattr(
        ReproducibilitySnapshotV2,
        "_git_output",
        staticmethod(lambda _repo_root, args: outputs[args]),
    )

    snapshot = ReproducibilitySnapshotV2.collect(
        repo_root=Path("."),
        manifest_hash="sha256:manifest",
        dependency_hashes={"uv.lock": "sha256:deps"},
        config_hashes={"research.yaml": "sha256:config"},
        data_hashes={"dataset.parquet": "sha256:data"},
        command_argv=("--config", "research.yaml"),
        random_seeds={"python": 7, "numpy": 11},
        calendar_version="XNYS-2026a",
        container_digest="sha256:container",
    )

    payload = snapshot.to_payload()

    assert payload["schema_version"] == 2
    assert payload["dependency_hashes"] == {"uv.lock": "sha256:deps"}
    assert payload["config_hashes"] == {"research.yaml": "sha256:config"}
    assert payload["data_hashes"] == {"dataset.parquet": "sha256:data"}
    assert payload["command_argv"] == ["--config", "research.yaml"]
    assert payload["random_seeds"] == {"python": 7, "numpy": 11}
    assert payload["calendar_version"] == "XNYS-2026a"
    assert payload["container_digest"] == "sha256:container"
    assert ReproducibilitySnapshotV2.from_payload(payload) == snapshot


def test_reproducibility_snapshot_v2_clean_snapshot_has_no_promotion_blockers() -> None:
    snapshot = ReproducibilitySnapshotV2(
        schema_version=2,
        git_sha="abc123",
        git_dirty=False,
        python_version="3.13.0",
        platform="macOS",
        manifest_hash="sha256:manifest",
        dependency_hashes={"uv.lock": "sha256:deps"},
        config_hashes={"research.yaml": "sha256:config"},
        data_hashes={"dataset.parquet": "sha256:data"},
        command_argv=("--config", "research.yaml"),
        random_seeds={"python": 7},
        calendar_version="XNYS-2026a",
        container_digest=None,
    )

    assert snapshot.promotion_blockers() == ()


def test_reproducibility_snapshot_v2_reports_promotion_blockers() -> None:
    snapshot = ReproducibilitySnapshotV2(
        schema_version=2,
        git_sha="unknown",
        git_dirty=True,
        python_version="3.13.0",
        platform="macOS",
        manifest_hash="",
        dependency_hashes={},
        config_hashes={"research.yaml": "unknown"},
        data_hashes={"dataset.parquet": ""},
        command_argv=("--config", "research.yaml"),
        random_seeds={},
        calendar_version="unknown",
        container_digest=None,
    )

    assert snapshot.promotion_blockers() == (
        "git working tree is dirty",
        "git_sha is missing or unknown",
        "manifest_hash is missing or unknown",
        "calendar_version is missing or unknown",
        "dependency_hashes has no recorded hashes",
        "config_hashes has missing or unknown hash for research.yaml",
        "data_hashes has missing or unknown hash for dataset.parquet",
    )


def test_reproducibility_snapshot_v2_rejects_wrong_schema_version() -> None:
    payload = {
        "schema_version": 1,
        "git_sha": "abc123",
        "git_dirty": False,
        "python_version": "3.13.0",
        "platform": "macOS",
        "manifest_hash": "sha256:manifest",
        "dependency_hashes": {"uv.lock": "sha256:deps"},
        "config_hashes": {"research.yaml": "sha256:config"},
        "data_hashes": {"dataset.parquet": "sha256:data"},
        "command_argv": ["--config", "research.yaml"],
        "random_seeds": {"python": 7},
        "calendar_version": "XNYS-2026a",
        "container_digest": None,
    }

    with pytest.raises(ValueError, match="schema_version must be 2"):
        ReproducibilitySnapshotV2.from_payload(payload)


def test_reproducibility_snapshot_v2_rejects_string_git_dirty() -> None:
    payload = {
        "schema_version": 2,
        "git_sha": "abc123",
        "git_dirty": "false",
        "python_version": "3.13.0",
        "platform": "macOS",
        "manifest_hash": "sha256:manifest",
        "dependency_hashes": {"uv.lock": "sha256:deps"},
        "config_hashes": {"research.yaml": "sha256:config"},
        "data_hashes": {"dataset.parquet": "sha256:data"},
        "command_argv": ["--config", "research.yaml"],
        "random_seeds": {"python": 7},
        "calendar_version": "XNYS-2026a",
        "container_digest": None,
    }

    with pytest.raises(ValueError, match="git_dirty must be bool"):
        ReproducibilitySnapshotV2.from_payload(payload)


def test_existing_reproducibility_snapshot_payload_remains_compatible() -> None:
    snapshot = ReproducibilitySnapshot(
        git_sha="abc",
        git_dirty=True,
        python_version="3.13.0",
        platform="test",
        manifest_hash="sha256:manifest",
    )

    assert ReproducibilitySnapshot.from_payload(snapshot.to_payload()) == snapshot


def test_reproducibility_snapshot_v2_is_public_package_export() -> None:
    import qts.research as research

    assert research.ReproducibilitySnapshotV2 is ReproducibilitySnapshotV2
