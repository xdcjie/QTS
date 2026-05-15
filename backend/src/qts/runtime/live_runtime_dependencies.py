"""Deprecated runtime dependency imports."""

from __future__ import annotations

import warnings

from qts.runtime.dependencies import RuntimeSessionDependencies

warnings.warn(
    "qts.runtime.live_runtime_dependencies is deprecated; use qts.runtime.dependencies.",
    DeprecationWarning,
    stacklevel=2,
)

LiveRuntimeDependencies = RuntimeSessionDependencies

__all__ = ["LiveRuntimeDependencies"]
