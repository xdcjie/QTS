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


__all__ = ["ReproducibilitySnapshot"]
