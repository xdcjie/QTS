"""Shared reporting contracts.

ReportWriter and RuntimeArtifactWriter describe output boundaries for
persisting runtime results. Mode-specific writers own concrete formats.
"""

from __future__ import annotations


class ReportWriter:
    """Boundary for writing run-level report manifests."""


class RuntimeArtifactWriter:
    """Boundary for persisting runtime artifact files."""


__all__ = ["ReportWriter", "RuntimeArtifactWriter"]
