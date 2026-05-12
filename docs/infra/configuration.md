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

Keep the axes separate:

- `historical` vs `realtime` describes the market data source and its temporal
  delivery model.
- `backtest`, `paper`, and `live` describe execution modes.

A backtest commonly uses a historical source, but historical sources are not
owned by the backtest package. Realtime sources are not synonymous with live
execution either: paper and live can both use realtime adapters, and historical
replay can use feed-like event contracts.

Use a project-level `HistoricalMarketDataConfig` such as
`configs/data/historical.local.yaml` to define:

- stores: physical layout, including root directory, bars directory, chain
  directory, filename templates, and default schema/timezone/normalization
  metadata
- schemas: framework semantic fields mapped to concrete CSV column names
- catalogs: logical dataset groups backed by a store
- datasets: product entries such as `GC` or `SI`, with asset class, exchange,
  chain file, and concrete bar files

Do not put `data_dir`, `chain_dir`, `bars_dir`, `chains_dir`, or other storage
paths under product entries such as `GC` or `SI`. Those paths belong to the
store. Product entries may describe product identity and may override
`chain_file` when a specific product does not follow the store's default
metadata or filename template.

Historical source timeframe is a property of a concrete bar file, not a global
property of the whole historical project. Configure it under each dataset's
`bars` list:

```yaml
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: historical
      bars_dir: data
      chains_dir: chains
      defaults:
        schema: databento_ohlcv
        exchange_timezone: US/Eastern
        timezone_policy: source_utc_exchange_sessions
        normalization: raw
  schemas:
    databento_ohlcv:
      timestamp: ts_event
      symbol: symbol
      instrument_id: instrument_id
      open: open
      high: high
      low: low
      close: close
      volume: volume
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc.csv
              timeframe: 1m
        SI:
          asset_class: future
          exchange: CME
          chain_file: SI.json
          bars:
            - file: si.csv
              timeframe: 1m
```

Each dataset must use `bars[]` so every concrete file declares its own source
timeframe. Store-level `source_timeframe` and dataset-level `bars_file` are not
supported.

Backtest run configs should reference a market data source by config path and
catalog name, then define the run-specific universe and time window. A
`BacktestRunConfig` must not duplicate stores, catalogs, chain file locations,
or CSV schemas from the historical market data system config:

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

Backtest run configs must use `market_data`; `historical_data` is reserved for
the project-level historical market data system config.
