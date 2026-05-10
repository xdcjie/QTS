# Market Data Outage Incident

## Detection

- Feed status changes to disconnected or degraded.
- Stale data age exceeds the configured risk threshold.
- Strategies stop receiving fresh clock-aligned bars.

## Immediate Action

- Pause dependent strategies.
- Ensure risk rejects orders that rely on stale or missing prices.
- Record affected instruments and feed subscription IDs.

## Recovery

- Reconnect market data using the market-data client ID.
- Backfill or mark gaps explicitly before resuming strategies.
- Verify bars remain inside exchange sessions and preserve `[start, end)` semantics.

## Postmortem

- Record stale-data duration, missing bar ranges, affected strategies, and any data-quality remediations.
