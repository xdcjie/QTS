#!/usr/bin/env python
"""Install the official IBKR TWS API Python client from the configured ZIP."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class IbkrApiPackageConfig:
    """Official IBKR API package metadata recorded in pyproject.toml."""

    package: str
    version: str
    source_url: str
    subdirectory: str
    sha256: str

    @classmethod
    def from_pyproject(cls, path: Path) -> IbkrApiPackageConfig:
        """Load official IBKR API metadata from pyproject.toml."""

        payload = tomllib.loads(path.read_text(encoding="utf-8"))
        config = payload["tool"]["qts"]["ibkr_api"]
        if not isinstance(config, dict):
            raise ValueError("tool.qts.ibkr_api must be a TOML table")
        return cls(
            package=_read_non_empty(config, "package"),
            version=_read_non_empty(config, "version"),
            source_url=_read_non_empty(config, "source_url"),
            subdirectory=_read_non_empty(config, "subdirectory"),
            sha256=_read_non_empty(config, "sha256"),
        )

    def validate(self) -> None:
        """Validate configured package metadata."""

        if self.package != "ibapi":
            raise ValueError("tool.qts.ibkr_api.package must be ibapi")
        if len(self.sha256) != 64:
            raise ValueError("tool.qts.ibkr_api.sha256 must be a SHA256 hex digest")


def sha256_file(path: Path) -> str:
    """Return the SHA256 hex digest for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive(config: IbkrApiPackageConfig, destination: Path) -> Path:
    """Download the configured official IBKR API archive."""

    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / Path(config.source_url).name
    if archive_path.exists() and sha256_file(archive_path) == config.sha256:
        return archive_path

    temp_path = archive_path.with_suffix(f"{archive_path.suffix}.tmp")
    if temp_path.exists():
        temp_path.unlink()
    try:
        with urllib.request.urlopen(config.source_url, timeout=300) as response:
            with temp_path.open("wb") as handle:
                shutil.copyfileobj(response, handle, length=1024 * 1024)
        temp_path.replace(archive_path)
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
    return archive_path


def extract_python_client(
    archive_path: Path,
    extract_dir: Path,
    config: IbkrApiPackageConfig,
) -> Path:
    """Extract the configured Python client subdirectory from the official ZIP."""

    config.validate()
    actual_digest = sha256_file(archive_path)
    if actual_digest != config.sha256:
        raise ValueError(
            f"IBKR API archive checksum mismatch: expected {config.sha256}, got {actual_digest}"
        )
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(extract_dir)
    client_dir = extract_dir / config.subdirectory
    if not (client_dir / "setup.py").exists():
        raise ValueError(f"IBKR Python client setup.py not found under {client_dir}")
    return client_dir


def install_ibapi(client_dir: Path, *, installer: str) -> None:
    """Install the extracted Python client into the active environment."""

    if installer == "uv":
        command = ["uv", "pip", "install", str(client_dir)]
    elif installer == "pip":
        command = [sys.executable, "-m", "pip", "install", str(client_dir)]
    else:
        raise ValueError("installer must be uv or pip")
    subprocess.run(command, check=True)


def main() -> None:
    """Install the official IBKR API package."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--download-dir", type=Path, default=Path(".cache/ibkr-api"))
    parser.add_argument("--installer", choices=("uv", "pip"), default="uv")
    args = parser.parse_args()

    config = IbkrApiPackageConfig.from_pyproject(args.pyproject)
    with tempfile.TemporaryDirectory(prefix="qts-ibapi-") as temp_dir:
        archive_path = download_archive(config, args.download_dir)
        client_dir = extract_python_client(archive_path, Path(temp_dir), config)
        install_ibapi(client_dir, installer=args.installer)


def _read_non_empty(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"tool.qts.ibkr_api.{key} must be a non-empty string")
    return value.strip()


if __name__ == "__main__":
    main()
