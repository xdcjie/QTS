# Data Rules

This module owns market data ingestion, storage access, sessions, and bar generation.

Rules:

- Exchange calendars and sessions are domain facts, not implementation details.
- Timezone conversions must not change session semantics.
- Use half-open intervals `[start, end)` for sessions and bars.
- Bar generation must respect holidays, early closes, and late opens.
- Session-outside data must not enter aggregated bars.
- Use `exchange-calendars` as preferred base calendar implementation when supported, wrapped behind internal services.

## Bar aggregation rules

- Provide bar aggregation for `5s -> 1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d`.
- `<1d` bars are clock-aligned in exchange timezone.
- `1d` bars are session-aligned and must not be treated as 24h bars.
- The final intraday bar of a session may be partial if natural clock alignment does not match session close; mark it explicitly.
- Important bar alignment and session-count rules must be covered by anchor tests.
