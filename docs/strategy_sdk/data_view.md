# DataView

`DataView` is a time-sliced view of market data.

Rules:

- It must not expose future data.
- It should normalize external data into project domain views.
- It should hide storage and feed implementation details.
- It reads committed market-data outputs, not live aggregation internals.
- It must not expose `BarAggregator` or `AggregationState`.
- `history`, `bar`, and `close` should use finalized bars emitted through
  `AggregationResult.completed` / `market_data.bar.closed` and filtered by `as_of`.
- In-progress buckets require a separate explicit live view if added later; they must not
  appear as normal historical bars.

Example:

```python
price = data.close(asset)
history = ctx.data.history(asset, bars=60, timeframe="1d")
chain = ctx.option_chain("SPY")
```
