"""Research-run reproducibility metadata."""

from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ReproducibilitySnapshot:
    """Git and interpreter metadata that make a research run reproducible."""

    git_sha: str
    git_dirty: bool
    python_version: str
    platform: str
    manifest_hash: str

    @classmethod
    def collect(cls, *, repo_root: Path, manifest_hash: str) -> ReproducibilitySnapshot:
        """Collect reproducibility metadata from the repository."""

        return cls(
            git_sha=cls._git_output(repo_root, ("rev-parse", "HEAD")),
            git_dirty=bool(cls._git_output(repo_root, ("status", "--short"))),
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            manifest_hash=manifest_hash,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ReproducibilitySnapshot:
        """Rehydrate a reproducibility snapshot."""

        return cls(
            git_sha=cls._required_text(payload, "git_sha"),
            git_dirty=bool(payload.get("git_dirty")),
            python_version=cls._required_text(payload, "python_version"),
            platform=cls._required_text(payload, "platform"),
            manifest_hash=cls._required_text(payload, "manifest_hash"),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready reproducibility payload."""

        return {
            "git_dirty": self.git_dirty,
            "git_sha": self.git_sha,
            "manifest_hash": self.manifest_hash,
            "platform": self.platform,
            "python_version": self.python_version,
        }

    @staticmethod
    def _git_output(repo_root: Path, args: tuple[str, ...]) -> str:
        result = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode != 0:
            return "unknown"
        return result.stdout.strip()

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} is required")
        return value.strip()


@dataclass(frozen=True, slots=True)
class ReproducibilitySnapshotV2:
    """Owns promotion-grade reproducibility metadata for a research artifact set."""

    schema_version: int
    git_sha: str
    git_dirty: bool | str
    python_version: str
    platform: str
    manifest_hash: str
    dependency_hashes: Mapping[str, str]
    config_hashes: Mapping[str, str]
    data_hashes: Mapping[str, str]
    command_argv: tuple[str, ...]
    random_seeds: Mapping[str, int]

    @classmethod
    def collect(
        cls,
        *,
        repo_root: Path,
        manifest_hash: str,
        config_paths: Sequence[Path] = (),
        data_paths: Sequence[Path] = (),
        command_argv: Sequence[str] = (),
        random_seeds: Mapping[str, int] | None = None,
    ) -> ReproducibilitySnapshotV2:
        """Collect reproducibility metadata with dependency, config, and data hashes."""

        return cls(
            schema_version=2,
            git_sha=_git_output(repo_root, ("rev-parse", "HEAD")),
            git_dirty=_git_dirty(repo_root),
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            manifest_hash=manifest_hash,
            dependency_hashes=_named_hashes(
                repo_root,
                (repo_root / "pyproject.toml", repo_root / "uv.lock"),
            ),
            config_hashes=_named_hashes(repo_root, config_paths),
            data_hashes=_named_hashes(repo_root, data_paths),
            command_argv=tuple(str(item) for item in command_argv),
            random_seeds={str(key): int(value) for key, value in (random_seeds or {}).items()},
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ReproducibilitySnapshotV2:
        """Rehydrate a v2 reproducibility snapshot."""

        if int(payload.get("schema_version", 0)) != 2:
            raise ValueError("schema_version must be 2")
        return cls(
            schema_version=2,
            git_sha=_required_text(payload, "git_sha"),
            git_dirty=payload.get("git_dirty", "unknown"),
            python_version=_required_text(payload, "python_version"),
            platform=_required_text(payload, "platform"),
            manifest_hash=_required_text(payload, "manifest_hash"),
            dependency_hashes=_string_mapping(payload.get("dependency_hashes", {})),
            config_hashes=_string_mapping(payload.get("config_hashes", {})),
            data_hashes=_string_mapping(payload.get("data_hashes", {})),
            command_argv=tuple(str(item) for item in payload.get("command_argv", ())),
            random_seeds={str(key): int(value) for key, value in _mapping(payload.get("random_seeds", {})).items()},
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready reproducibility v2 payload."""

        return {
            "command_argv": list(self.command_argv),
            "config_hashes": dict(self.config_hashes),
            "data_hashes": dict(self.data_hashes),
            "dependency_hashes": dict(self.dependency_hashes),
            "git_dirty": self.git_dirty,
            "git_sha": self.git_sha,
            "manifest_hash": self.manifest_hash,
            "platform": self.platform,
            "python_version": self.python_version,
            "random_seeds": dict(self.random_seeds),
            "schema_version": self.schema_version,
        }

    def promotion_blockers(self) -> tuple[str, ...]:
        """Return reproducibility gaps that block promotion-grade evidence."""

        blockers: list[str] = []
        if _is_unknown(self.git_sha):
            blockers.append("git_sha must be known")
        if self.git_dirty is not False:
            blockers.append(f"git_dirty must be false, got {self.git_dirty}")
        for group_name, hashes in (
            ("dependency_hashes", self.dependency_hashes),
            ("config_hashes", self.config_hashes),
            ("data_hashes", self.data_hashes),
        ):
            for path, digest in hashes.items():
                if _is_unknown(digest) or digest == "missing":
                    blockers.append(f"{group_name}.{path} must be hashable")
        return tuple(blockers)


def _git_output(repo_root: Path, args: tuple[str, ...]) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip()


def _git_dirty(repo_root: Path) -> bool | str:
    output = _git_output(repo_root, ("status", "--short"))
    if output == "unknown":
        return "unknown"
    return bool(output.strip())


def _named_hashes(repo_root: Path, paths: Sequence[Path]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        resolved = path if path.is_absolute() else repo_root / path
        key = _display_path(repo_root, resolved)
        hashes[key] = _sha256_or_missing(resolved)
    return hashes


def _sha256_or_missing(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return "missing"
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _display_path(repo_root: Path, path: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    return value.strip()


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("expected mapping")
    return value


def _string_mapping(value: Any) -> dict[str, str]:
    return {str(key): str(item) for key, item in _mapping(value).items()}


def _is_unknown(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip().lower() in {"", "unknown"})


__all__ = ["ReproducibilitySnapshot", "ReproducibilitySnapshotV2"]
