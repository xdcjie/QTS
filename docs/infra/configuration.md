# Configuration

Runtime config should be externalized under `configs/` and environment variables.

Do not commit real credentials.

Commit:

- `.env.example`
- `configs/paper.ibkr.example.yaml`
- `configs/live.ibkr.example.yaml`

IBKR paper and live profiles must keep market data and order execution settings
separate. Each profile should model at least:

- market data connection host, port, client ID, and source ID
- order execution connection host, port, client ID, broker ID, and account ID
- environment mode: `paper` or `live`
- risk limit profile selected for that environment
- credentials or secret references loaded from environment variables

Do not commit:

- `.env`
- `configs/paper.ibkr.yaml`
- `configs/live.ibkr.yaml`
- broker credentials

Live mode must fail closed if required live settings are missing or if paper
account/client identifiers are supplied by mistake. Error messages must not
print credentials or raw secret values.

## Market data sources and historical catalogs

Market data source configuration identifies where market data comes from. In
paper/live mode, that source is typically a gateway connection. In backtest
mode, that source is typically a historical data store and catalog.

Historical data storage layout is project/environment configuration, not a
strategy setting and not a product-domain fact.

Use a project-level historical data config such as
`configs/data/historical.local.yaml` to define:

- stores: physical layout, including root directory, bars directory, chain
  directory, filename templates, source timeframe, exchange timezone, timezone
  policy, and normalization policy
- catalogs: logical dataset groups backed by a store
- datasets: product entries such as `GC` or `SI`, with asset class, exchange,
  and only product-specific file overrides when the store template is not enough

Do not put `data_dir`, `chain_dir`, `bars_dir`, `chains_dir`, or other storage
paths under product entries such as `GC` or `SI`. Those paths belong to the
store. Product entries may describe product identity and may override
`bars_file`, `chain_file`, `source_timeframe`, or `exchange_timezone` only when
a specific product does not follow the store's default metadata or filename
template.

Backtest run configs should reference a market data source by config path and
catalog name, then define the run-specific universe and time window:

```yaml
market_data:
  source: local_historical
  config: configs/data/historical.local.yaml
  catalog: research_futures
```

The historical source timeframe is the physical dataset capability. The
backtest run `timeframe` is the strategy-requested timeframe. If they differ,
historical bars must flow through `MarketDataActor` and `BarAggregator` before
they reach strategy processing.

Strategy configs should remain separate and contain strategy class, strategy
ID, allocation, account, enabled flag, and strategy parameters.

The older `historical_data` field is accepted as a compatibility alias in
backtest run configs, but new configs should use `market_data`.
