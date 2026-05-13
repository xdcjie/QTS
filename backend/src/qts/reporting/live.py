"""Live reporting outputs.

Live report writers will turn normalized runtime events into operational
reports, audit records, and live monitoring streams.
"""

from __future__ import annotations


class LiveReportWriter:
    """Boundary placeholder for live report generation."""


class LiveEventReporter:
    """Boundary placeholder for live event reporting."""


__all__ = ["LiveEventReporter", "LiveReportWriter"]
