"""Startup reconciliation gating."""

from __future__ import annotations

from dataclasses import dataclass

from .report import ReconciliationReport


@dataclass(frozen=True, slots=True)
class StartupReconciliationDecision:
    """Decision object returned before runtime startup."""

    trading_enabled: bool
    report: ReconciliationReport
    reason_code: str | None = None


def startup_reconciliation_gate(
    report: ReconciliationReport,
) -> StartupReconciliationDecision:
    """Return startup decision based on whether report has critical drift."""
    if report.has_drift:
        return StartupReconciliationDecision(
            trading_enabled=False,
            report=report,
            reason_code="RECONCILIATION_DRIFT",
        )
    return StartupReconciliationDecision(trading_enabled=True, report=report)


__all__ = ["StartupReconciliationDecision", "startup_reconciliation_gate"]
