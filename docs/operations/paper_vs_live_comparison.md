# Paper vs Live Comparison Report

## Scope

Compare paper decisions against live market and broker state before enabling real order submission.

## Required Fields

- Strategy signal timestamp.
- Live market data timestamp and stale-data age.
- Paper target intent and hypothetical order.
- Live broker account, positions, cash, open orders, and margin snapshot.
- Difference classification: matched, market-data difference, risk difference, broker-state difference, or unexplained.

## Gate

Unexplained differences block production readiness.

Live observation must submit no orders. The comparison may produce hypothetical
paper decisions, but live broker state is read-only until signoff evidence
explicitly enables live capital.
