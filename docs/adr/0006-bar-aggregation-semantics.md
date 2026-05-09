# ADR 0006: Bar Aggregation Semantics

## Decision

Use `[start, end)` intervals for all bars. Use clock alignment for `<1d` bars and session alignment for `1d` bars.

## Rationale

This separates intraday clock bars from daily session bars and avoids treating `1d` as `24h`.
