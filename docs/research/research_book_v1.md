# ResearchBook API v1

`ResearchBook` is a read-only research facade for notebooks and scripts.

It may:
- load a configured `HistoricalCatalog`;
- request bounded historical bars through QTS historical data boundaries;
- derive complete higher clock-aligned bars through the shared QTS bar
  aggregation pipeline when the catalog source timeframe is finer than the
  requested timeframe;
- return deterministic row-like research frames;
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
