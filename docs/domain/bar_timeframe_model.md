# Bar Timeframe and Aggregation Model

## Required components

The data module must provide bar construction and aggregation:

```text
qts/data/bars/builder.py       tick/quote/trade -> base bars
qts/data/bars/aggregator.py    low timeframe bars -> high timeframe bars
qts/data/bars/timeframe.py     timeframe model
qts/data/bars/alignment.py     bucket boundary logic
qts/data/bars/validation.py    data quality and interval validation
```

## Supported chain

```text
5s -> 1m -> 5m -> 15m -> 30m -> 1h -> 4h -> 1d
```

## Timeframe semantics

- `5s`, `1m`, `5m`, `15m`, `30m`, `1h`, `4h`: clock-aligned bars in exchange timezone.
- `1d`: session-aligned bar.
- `1d` must not be treated as 24 hours.
- All intervals use `[start, end)`.

## Requested and source timeframes

Requested timeframe is strategy intent. Source timeframe is provider capability.

Provider limitations must not redefine bar semantics. If a provider such as IBKR
can supply only `5s` realtime bars for a symbol, requests for `1m`, `5m`, or
larger supported bars must be produced by the internal aggregation chain. The
physical provider subscription should be deduplicated at the source timeframe,
while strategy subscribers receive the requested timeframe.

Historical sources follow the same rule. A `5s` source can satisfy `1m` and
larger compatible requests through aggregation. A `1m` source can satisfy `1m`
and larger compatible requests, but it must reject `5s` requests explicitly
rather than fabricating finer bars.

## Clock-aligned examples

For 1m -> 5m:

```text
[09:30, 09:35)
[09:35, 09:40)
[09:40, 09:45)
...
[09:55, 10:00)
```

A bar starting exactly at `09:35` belongs to `[09:35, 09:40)`, not `[09:30, 09:35)`.

## Session-aligned daily bars

A `1d` bar is the full trading session. For COMEX Gold `[ET 18:00, ET 17:00)`, the daily bar starts at `ET 18:00` and ends at `ET 17:00` next day.

## Partial intraday bars

For `<1d` clock-aligned bars, session open/close can create partial buckets. Partial bars are allowed but must be marked explicitly with `is_partial=True`.

## OHLCV aggregation

- open = first bar open
- high = max high
- low = min low
- close = last bar close
- volume = sum volume
- vwap = weighted average by volume when available
- open_interest = last open_interest when available
- trade_count = sum trade_count when available

## Anchor tests

Add anchor tests for:

- Clock bucket boundaries
- Half-open interval membership
- Daily session boundaries
- COMEX Gold 1m session count = 1380
- Partial intraday bar marking
- Provider source timeframe capability cannot change requested timeframe semantics
