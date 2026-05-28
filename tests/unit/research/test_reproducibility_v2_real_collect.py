from __future__ import annotations

from pathlib import Path

from qts.research.reproducibility import ReproducibilitySnapshotV2


def test_reproducibility_v2_collect_uses_real_repo_metadata() -> None:
    snapshot = ReproducibilitySnapshotV2.collect(
        repo_root=Path.cwd(),
        dependency_hashes={"pyproject.toml": _sha256(Path("pyproject.toml"))},
        config_hashes={"config": "sha256:config"},
        data_hashes={"data": "sha256:data"},
        command_argv=("research-experiment-runner", "--job-id=test"),
        random_seeds={"experiment": 7},
        calendar_version="CME",
        manifest_hash="sha256:manifest",
    )

    assert snapshot.git_sha != "research-git-sha"
    assert snapshot.platform != "research-platform"
    assert snapshot.dependency_hashes["pyproject.toml"].startswith("sha256:")


def _sha256(path: Path) -> str:
    import hashlib

    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
