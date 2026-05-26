# Factor Snapshot Protocol

Factor evaluation must preserve the no-lookahead timing contract:

```text
source_data_end <= available_at <= forward_return_start < forward_return_end
```

Dates and intraday ISO datetimes are accepted, including `Z` and timezone offset
forms. Intraday values must be preserved in the factor artifact
`forward_return_protocol`; they must not be truncated to date-only values.

Example snapshot payload:

```yaml
as_of: "2026-01-02"
source_data_end: "2026-01-02T10:00:00Z"
available_at: "2026-01-02T10:05:00+00:00"
forward_return_start: "2026-01-02T10:05:00+00:00"
forward_return_end: "2026-01-02T10:20:00+00:00"
```

Known failure modes: future labels entering factor scores, available time after
forward start, daily bars treated as fixed 24-hour bars, and report-only windows
used for selection.
