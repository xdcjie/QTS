"""Market data validation reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum

from qts.core.time import TimeInterval
from qts.domain.market_data import Bar


class DataValidationIssueCode(StrEnum):
    """Known market data validation issue codes."""

    MISSING_BAR = "missing_bar"
    DUPLICATE_BAR = "duplicate_bar"
    NON_MONOTONIC = "non_monotonic"
    OVERLAPPING_BARS = "overlapping_bars"
    OUTSIDE_SESSION = "outside_session"
    INVALID_OHLC = "invalid_ohlc"
    UNEXPECTED_GAP = "unexpected_gap"
    EXCLUDED_SYMBOL = "excluded_symbol"
    EXCLUDED_SPREAD = "excluded_spread"
    UNDECLARED_FUTURES_OUTRIGHT_SYMBOL = "undeclared_futures_outright_symbol"


class DataValidationSeverity(StrEnum):
    """Severity for data validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DataValidationError(ValueError):
    """Raised when validation issues contain hard-gate errors."""

    def __init__(self, issues: tuple[DataValidationIssue, ...]) -> None:
        """Create an exception with the blocking validation issues."""
        self.issues = issues
        message = "; ".join(issue.message for issue in issues)
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class DataValidationIssue:
    """One validation issue for a bar sequence."""

    code: DataValidationIssueCode
    message: str
    severity: DataValidationSeverity = DataValidationSeverity.ERROR


@dataclass(frozen=True, slots=True)
class DataValidationReport:
    """Validation result for a bar sequence."""

    issues: tuple[DataValidationIssue, ...]

    @property
    def valid(self) -> bool:
        """Perform valid."""
        return not any(issue.severity is DataValidationSeverity.ERROR for issue in self.issues)

    @property
    def error_issues(self) -> tuple[DataValidationIssue, ...]:
        """Return hard-gate validation issues."""
        return tuple(
            issue for issue in self.issues if issue.severity is DataValidationSeverity.ERROR
        )

    @property
    def max_severity(self) -> DataValidationSeverity | None:
        """Perform max_severity."""
        if not self.issues:
            return None
        rank = {
            DataValidationSeverity.INFO: 0,
            DataValidationSeverity.WARNING: 1,
            DataValidationSeverity.ERROR: 2,
        }
        return max((issue.severity for issue in self.issues), key=lambda severity: rank[severity])

    def raise_for_errors(self) -> None:
        """Raise when validation contains ERROR-severity issues."""
        error_issues = self.error_issues
        if error_issues:
            raise DataValidationError(error_issues)


def validate_bars(
    bars: tuple[Bar, ...],
    *,
    session_interval: TimeInterval | None = None,
    expected_interval: timedelta | None = None,
) -> DataValidationReport:
    """Validate bar ordering, overlap, and optional session containment."""

    issues: list[DataValidationIssue] = []
    if expected_interval is not None and expected_interval <= timedelta(0):
        raise ValueError("expected_interval must be positive")
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
        _append_ohlc_issue(issues, bar)
        if (
            previous is not None
            and bar.start_time == previous.start_time
            and bar.end_time == previous.end_time
        ):
            issues.append(
                DataValidationIssue(
                    code=DataValidationIssueCode.DUPLICATE_BAR,
                    message=f"bar {bar.start_time.isoformat()} duplicates previous bar",
                )
            )
        elif previous is not None:
            if bar.start_time < previous.end_time:
                issues.append(
                    DataValidationIssue(
                        code=DataValidationIssueCode.OVERLAPPING_BARS,
                        message=f"bar {bar.start_time.isoformat()} overlaps previous bar",
                    )
                )
            if expected_interval is not None and bar.start_time > previous.end_time:
                missing = int((bar.start_time - previous.end_time) / expected_interval)
                issues.append(
                    DataValidationIssue(
                        code=DataValidationIssueCode.UNEXPECTED_GAP,
                        message=(
                            f"gap from {previous.end_time.isoformat()} "
                            f"to {bar.start_time.isoformat()}"
                        ),
                        severity=DataValidationSeverity.WARNING,
                    )
                )
                if missing > 0:
                    issues.append(
                        DataValidationIssue(
                            code=DataValidationIssueCode.MISSING_BAR,
                            message=(
                                f"{missing} expected bar(s) missing before "
                                f"{bar.start_time.isoformat()}"
                            ),
                            severity=DataValidationSeverity.WARNING,
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


def _append_ohlc_issue(issues: list[DataValidationIssue], bar: Bar) -> None:
    """Perform _append_ohlc_issue."""
    if (
        bar.low > bar.high
        or bar.high < max(bar.open, bar.close)
        or bar.low > min(bar.open, bar.close)
    ):
        issues.append(
            DataValidationIssue(
                code=DataValidationIssueCode.INVALID_OHLC,
                message=f"bar {bar.start_time.isoformat()} has invalid OHLC values",
            )
        )


__all__ = [
    "DataValidationError",
    "DataValidationIssue",
    "DataValidationIssueCode",
    "DataValidationReport",
    "DataValidationSeverity",
    "validate_bars",
]
