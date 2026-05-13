"""Shared reporting contracts.

ReportWriter and RuntimeArtifactWriter describe output boundaries for
persisting runtime results. Mode-specific writers own concrete formats.
"""

from __future__ import annotations


class ReportWriter:
    """Boundary placeholder for report generation."""


class RuntimeArtifactWriter:
    """Boundary placeholder for runtime artifact persistence."""


__all__ = ["ReportWriter", "RuntimeArtifactWriter"]
