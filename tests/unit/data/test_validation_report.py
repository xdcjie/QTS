from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.market_data import Bar


def _bar(start: datetime, minutes: int = 1) -> Bar:
    return Bar(
        instrument_id=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        start_time=start,
        end_time=start + timedelta(minutes=minutes),
        timeframe="1m",
        session_id="2026-01-02",
        open=Decimal("100"),
        high=Decimal("100"),
        low=Decimal("100"),
        close=Decimal("100"),
        is_complete=True,
    )


def test_validation_report_detects_ordering_overlap_and_session_outside() -> None:
    from qts.core.time import TimeInterval
    from qts.data.validation_report import (
        DataValidationIssueCode,
        DataValidationSeverity,
        validate_bars,
    )

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    report = validate_bars(
        (
            _bar(start + timedelta(minutes=1)),
            _bar(start, minutes=2),
            _bar(start + timedelta(minutes=3)),
        ),
        session_interval=TimeInterval(start=start, end=start + timedelta(minutes=3)),
    )

    assert {issue.code for issue in report.issues} == {
        DataValidationIssueCode.NON_MONOTONIC,
        DataValidationIssueCode.OVERLAPPING_BARS,
        DataValidationIssueCode.OUTSIDE_SESSION,
    }
    assert report.valid is False
    assert report.max_severity is DataValidationSeverity.ERROR


def test_validation_report_classifies_duplicates_missing_bars_and_gaps() -> None:
    from qts.data.validation_report import (
        DataValidationIssueCode,
        DataValidationSeverity,
        validate_bars,
    )

    start = datetime(2026, 1, 2, 14, 30, tzinfo=UTC)
    report = validate_bars(
        (
            _bar(start),
            _bar(start),
            _bar(start + timedelta(minutes=3)),
        ),
        expected_interval=timedelta(minutes=1),
    )

    assert {issue.code for issue in report.issues} == {
        DataValidationIssueCode.DUPLICATE_BAR,
        DataValidationIssueCode.UNEXPECTED_GAP,
        DataValidationIssueCode.MISSING_BAR,
    }
    assert {issue.severity for issue in report.issues} == {
        DataValidationSeverity.ERROR,
        DataValidationSeverity.WARNING,
    }


def test_validation_report_hard_gate_blocks_errors_but_not_warnings() -> None:
    import pytest
    from qts.data.validation_report import (
        DataValidationError,
        DataValidationIssue,
        DataValidationIssueCode,
        DataValidationReport,
        DataValidationSeverity,
    )

    warning_report = DataValidationReport(
        issues=(
            DataValidationIssue(
                code=DataValidationIssueCode.MISSING_BAR,
                message="one expected bar missing",
                severity=DataValidationSeverity.WARNING,
            ),
        )
    )
    error_report = DataValidationReport(
        issues=(
            DataValidationIssue(
                code=DataValidationIssueCode.INVALID_OHLC,
                message="invalid high/low",
                severity=DataValidationSeverity.ERROR,
            ),
        )
    )

    warning_report.raise_for_errors()
    with pytest.raises(DataValidationError, match="invalid high/low"):
        error_report.raise_for_errors()
