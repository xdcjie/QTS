"""Market data validation reports."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.core.time import TimeInterval
from qts.domain.market_data import Bar


class DataValidationIssueCode(StrEnum):
    """Known market data validation issue codes."""

    NON_MONOTONIC = "non_monotonic"
    OVERLAPPING_BARS = "overlapping_bars"
    OUTSIDE_SESSION = "outside_session"


@dataclass(frozen=True, slots=True)
class DataValidationIssue:
    """One validation issue for a bar sequence."""

    code: DataValidationIssueCode
    message: str


@dataclass(frozen=True, slots=True)
class DataValidationReport:
    """Validation result for a bar sequence."""

    issues: tuple[DataValidationIssue, ...]

    @property
    def valid(self) -> bool:
        return not self.issues


def validate_bars(
    bars: tuple[Bar, ...],
    *,
    session_interval: TimeInterval | None = None,
) -> DataValidationReport:
    """Validate bar ordering, overlap, and optional session containment."""

    issues: list[DataValidationIssue] = []
    ordered = sorted(bars, key=lambda bar: (bar.start_time, bar.end_time))
    if tuple(ordered) != bars:
        issues.append(
            DataValidationIssue(
                code=DataValidationIssueCode.NON_MONOTONIC,
                message="bars are not sorted by start_time and end_time",
            )
        )
    previous: Bar | None = None
    for bar in ordered:
        if previous is not None and bar.start_time < previous.end_time:
            issues.append(
                DataValidationIssue(
                    code=DataValidationIssueCode.OVERLAPPING_BARS,
                    message=f"bar {bar.start_time.isoformat()} overlaps previous bar",
                )
            )
        if session_interval is not None and (
            not session_interval.contains(bar.start_time) or bar.end_time > session_interval.end
        ):
            issues.append(
                DataValidationIssue(
                    code=DataValidationIssueCode.OUTSIDE_SESSION,
                    message=f"bar {bar.start_time.isoformat()} is outside session",
                )
            )
        previous = bar
    return DataValidationReport(issues=tuple(issues))


__all__ = [
    "DataValidationIssue",
    "DataValidationIssueCode",
    "DataValidationReport",
    "validate_bars",
]
