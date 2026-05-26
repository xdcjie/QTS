"""Research-run reproducibility metadata."""

from __future__ import annotations

import platform
import subprocess
import sys
from collections.abc import Mapping
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
    """Promotion-grade research-run reproducibility metadata."""

    schema_version: int
    git_sha: str
    git_dirty: bool
    python_version: str
    platform: str
    manifest_hash: str
    dependency_hashes: Mapping[str, str]
    config_hashes: Mapping[str, str]
    data_hashes: Mapping[str, str]
    command_argv: tuple[str, ...]
    random_seeds: Mapping[str, int]
    calendar_version: str
    container_digest: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != 2:
            raise ValueError("schema_version must be 2")

    @classmethod
    def collect(
        cls,
        *,
        repo_root: Path,
        dependency_hashes: Mapping[str, str],
        config_hashes: Mapping[str, str],
        data_hashes: Mapping[str, str],
        command_argv: tuple[str, ...],
        random_seeds: Mapping[str, int],
        calendar_version: str,
        manifest_hash: str | None = None,
        container_digest: str | None = None,
    ) -> ReproducibilitySnapshotV2:
        """Collect reproducibility metadata from explicit run evidence."""

        return cls(
            schema_version=2,
            git_sha=cls._git_output(repo_root, ("rev-parse", "HEAD")),
            git_dirty=bool(cls._git_output(repo_root, ("status", "--short"))),
            python_version=sys.version.split()[0],
            platform=platform.platform(),
            manifest_hash=manifest_hash or "unknown",
            dependency_hashes=dict(dependency_hashes),
            config_hashes=dict(config_hashes),
            data_hashes=dict(data_hashes),
            command_argv=tuple(command_argv),
            random_seeds=dict(random_seeds),
            calendar_version=calendar_version,
            container_digest=container_digest,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> ReproducibilitySnapshotV2:
        """Rehydrate a V2 reproducibility snapshot."""

        schema_version = payload.get("schema_version")
        if schema_version != 2:
            raise ValueError("schema_version must be 2")

        return cls(
            schema_version=schema_version,
            git_sha=cls._required_text(payload, "git_sha"),
            git_dirty=cls._required_bool(payload, "git_dirty"),
            python_version=cls._required_text(payload, "python_version"),
            platform=cls._required_text(payload, "platform"),
            manifest_hash=cls._required_text(payload, "manifest_hash"),
            dependency_hashes=cls._text_mapping(payload, "dependency_hashes"),
            config_hashes=cls._text_mapping(payload, "config_hashes"),
            data_hashes=cls._text_mapping(payload, "data_hashes"),
            command_argv=cls._text_tuple(payload, "command_argv"),
            random_seeds=cls._int_mapping(payload, "random_seeds"),
            calendar_version=cls._required_text(payload, "calendar_version"),
            container_digest=cls._optional_text(payload, "container_digest"),
        )

    def to_payload(self) -> dict[str, Any]:
        """Return a JSON-ready V2 reproducibility payload."""

        return {
            "schema_version": self.schema_version,
            "git_dirty": self.git_dirty,
            "git_sha": self.git_sha,
            "python_version": self.python_version,
            "platform": self.platform,
            "manifest_hash": self.manifest_hash,
            "dependency_hashes": dict(self.dependency_hashes),
            "config_hashes": dict(self.config_hashes),
            "data_hashes": dict(self.data_hashes),
            "command_argv": list(self.command_argv),
            "random_seeds": dict(self.random_seeds),
            "calendar_version": self.calendar_version,
            "container_digest": self.container_digest,
        }

    def promotion_blockers(self) -> tuple[str, ...]:
        """Return reasons this snapshot is not acceptable for promotion."""

        blockers: list[str] = []
        if self.git_dirty:
            blockers.append("git working tree is dirty")
        if self._is_unknown_text(self.git_sha):
            blockers.append("git_sha is missing or unknown")

        for field_name, value in (
            ("manifest_hash", self.manifest_hash),
            ("calendar_version", self.calendar_version),
        ):
            if self._is_unknown_text(value):
                blockers.append(f"{field_name} is missing or unknown")

        for field_name, hashes in (
            ("dependency_hashes", self.dependency_hashes),
            ("config_hashes", self.config_hashes),
            ("data_hashes", self.data_hashes),
        ):
            blockers.extend(self._hash_blockers(field_name, hashes))

        return tuple(blockers)

    @staticmethod
    def _git_output(repo_root: Path, args: tuple[str, ...]) -> str:
        return ReproducibilitySnapshot._git_output(repo_root, args)

    @staticmethod
    def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
        return ReproducibilitySnapshot._required_text(payload, field_name)

    @staticmethod
    def _required_bool(payload: Mapping[str, Any], field_name: str) -> bool:
        value = payload.get(field_name)
        if not isinstance(value, bool):
            raise ValueError(f"{field_name} must be bool")
        return value

    @classmethod
    def _optional_text(cls, payload: Mapping[str, Any], field_name: str) -> str | None:
        value = payload.get(field_name)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be text")
        return value.strip()

    @classmethod
    def _text_mapping(
        cls,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> dict[str, str]:
        value = payload.get(field_name)
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")

        result: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str):
                raise ValueError(f"{field_name} must map text to text")
            result[key.strip()] = item.strip()
        return result

    @classmethod
    def _int_mapping(
        cls,
        payload: Mapping[str, Any],
        field_name: str,
    ) -> dict[str, int]:
        value = payload.get(field_name)
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")

        result: dict[str, int] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, int):
                raise ValueError(f"{field_name} must map text to integers")
            result[key.strip()] = item
        return result

    @classmethod
    def _text_tuple(cls, payload: Mapping[str, Any], field_name: str) -> tuple[str, ...]:
        value = payload.get(field_name)
        if not isinstance(value, list | tuple):
            raise ValueError(f"{field_name} must be a sequence")
        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"{field_name} must contain only text")
        return tuple(value)

    @classmethod
    def _hash_blockers(cls, field_name: str, hashes: Mapping[str, str]) -> tuple[str, ...]:
        if not hashes:
            return (f"{field_name} has no recorded hashes",)

        blockers: list[str] = []
        for name, digest in hashes.items():
            label = name if name.strip() else "<unknown>"
            if cls._is_unknown_text(name) or cls._is_unknown_text(digest):
                blockers.append(f"{field_name} has missing or unknown hash for {label}")
        return tuple(blockers)

    @staticmethod
    def _is_unknown_text(value: str) -> bool:
        return not value.strip() or value.strip().lower() == "unknown"


__all__ = ["ReproducibilitySnapshot", "ReproducibilitySnapshotV2"]
