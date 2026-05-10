"""Idempotent local bootstrap helpers."""

from __future__ import annotations

from pathlib import Path


def bootstrap_local(root: Path) -> dict[str, str]:
    """Create local runtime directories and marker files safely."""

    root.mkdir(parents=True, exist_ok=True)
    data_dir = root / "data"
    logs_dir = root / "logs"
    data_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    marker = root / ".qts-bootstrap"
    marker.write_text("ok\n", encoding="utf-8")
    return {
        "root": str(root),
        "data": str(data_dir),
        "logs": str(logs_dir),
        "marker": str(marker),
    }


__all__ = ["bootstrap_local"]
