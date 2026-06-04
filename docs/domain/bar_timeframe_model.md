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
5s -> 1m -> 2m -> 3m -> 5m -> 10m -> 15m -> 30m -> 1h -> 4h -> 1d
```

## Timeframe semantics

- `5s`, `1m`, `2m`, `3m`, `5m`, `10m`, `15m`, `30m`, `1h`, `4h`: clock-aligned bars in exchange timezone.
- `1d`: session-aligned bar.
- `1d` must not be treated as 24 hours.
- All intervals use `[start, end)`.

## Time-grid completeness

For `<1d` clock-aligned bars, **every wall-clock slot inside an active
session must produce a Bar**, even when the underlying tape was silent
for that slot. Sources whose raw rows are trade-only (e.g. Databento
OHLCV CSVs that omit silent minutes) are wrapped by
`BarTimeGridSynthesizer` at the source boundary; the synthesizer emits
one synthetic bar per missing slot:

- `open = high = low = close = previous bar's close`
- `volume = 0`
- `is_synthetic = True`
- same `instrument_id`, `timeframe`, `session_id` as the trailing real bar

Synthesis only spans gaps **between observed bars of the same
`session_id`**. Leading slots before the first observed bar are not
synthesized (no previous close to carry forward); trailing slots after
the last observed bar are not synthesized. Cross-session gaps are
natural session breaks and are never bridged.

Strategy SDK indicators (`SMA`, `EMA`, `ATR`, `RSI`, `session_vwap`,
`volume_ratio`, etc.) consume the post-synthesis stream, so windows
expressed in bar counts have stable wall-clock semantics: `EMA(20)` on
a `1m` series always covers exactly 20 wall-clock minutes.

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
