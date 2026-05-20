# ResearchBook API v1

`ResearchBook` is a read-only research facade for notebooks and scripts.

It may:
- load a configured `HistoricalCatalog`;
- request bounded historical bars through QTS historical data boundaries;
- derive complete higher clock-aligned bars through the shared QTS bar
  aggregation pipeline when the catalog source timeframe is finer than the
  requested timeframe;
- return deterministic row-like research frames;
- return deterministic row dictionaries or pandas `DataFrame` objects for
  notebooks without changing the underlying history path;
- expose dataset IDs for experiment manifests.

It must not:
- mutate portfolio, account, order, runtime, or broker state;
- parse source CSV rows directly;
- create orders or target intents;
- depend on runtime/backtest config objects; callers assemble
  `ResearchBookConfig` at the boundary;
- redefine sessions, roll rules, or bar intervals.

History requests use `[start, end)` bounds. When a requested timeframe differs
from the selected dataset source timeframe, `ResearchBook` reads source bars
using the source timeframe and emits only complete target bars produced by
`qts.data.bars.BarAggregationPipeline`. It does not relabel source rows as the
requested timeframe.

`ResearchHistoryFrame.rows()` returns one dictionary per emitted bar with
deterministic column names for timestamp, instrument identity, OHLCV,
timeframe, session, completeness, synthetic, VWAP, open-interest, and
trade-count fields. `ResearchHistoryFrame.to_pandas()` creates a pandas
`DataFrame` from those rows using a local pandas import so core domain models do
not depend on pandas at import time. `ResearchBook.history_rows(...)` and
`ResearchBook.history_frame(...)` are notebook conveniences that delegate to
the existing `history(...)` method; they do not parse source files or bypass
catalog, roll, session, or aggregation rules.
