from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any, cast


def _load_installer_module() -> ModuleType:
    module_path = Path("scripts/install_ibapi_official.py")
    spec = importlib.util.spec_from_file_location("install_ibapi_official", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["install_ibapi_official"] = module
    spec.loader.exec_module(module)
    return module


def test_installer_reads_official_ibapi_metadata_from_pyproject() -> None:
    installer = _load_installer_module()

    config = cast(Any, installer).IbkrApiPackageConfig.from_pyproject(Path("pyproject.toml"))

    assert config.package == "ibapi"
    assert config.version == "10.46.1"
    assert config.source_url.endswith("twsapi_macunix.1046.01.zip")
    assert config.subdirectory == "IBJts/source/pythonclient"
    assert len(config.sha256) == 64


def test_installer_verifies_checksum_and_extracts_python_client(tmp_path: Path) -> None:
    installer = _load_installer_module()
    config_cls = cast(Any, installer).IbkrApiPackageConfig
    archive_path = tmp_path / "twsapi.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("IBJts/source/pythonclient/setup.py", "from setuptools import setup\n")
        archive.writestr("IBJts/source/pythonclient/ibapi/__init__.py", "__version__ = '10.46.1'\n")

    digest = cast(Any, installer).sha256_file(archive_path)
    config = config_cls(
        package="ibapi",
        version="10.46.1",
        source_url="https://example.invalid/twsapi.zip",
        subdirectory="IBJts/source/pythonclient",
        sha256=digest,
    )

    client_dir = cast(Any, installer).extract_python_client(
        archive_path,
        tmp_path / "extract",
        config,
    )

    assert client_dir == tmp_path / "extract" / "IBJts" / "source" / "pythonclient"
    assert (client_dir / "setup.py").exists()
    assert (client_dir / "ibapi" / "__init__.py").exists()


def test_installer_reuses_cached_archive_when_checksum_matches(tmp_path: Path) -> None:
    installer = _load_installer_module()
    config_cls = cast(Any, installer).IbkrApiPackageConfig
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    archive_path = cache_dir / "twsapi.zip"
    archive_path.write_bytes(b"cached")
    digest = cast(Any, installer).sha256_file(archive_path)
    config = config_cls(
        package="ibapi",
        version="10.46.1",
        source_url="https://example.invalid/twsapi.zip",
        subdirectory="IBJts/source/pythonclient",
        sha256=digest,
    )

    reused_path = cast(Any, installer).download_archive(config, cache_dir)

    assert reused_path == archive_path
    assert reused_path.read_bytes() == b"cached"
