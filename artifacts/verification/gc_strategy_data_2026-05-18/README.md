# GC Historical Data To Strategy Validation

Window: `2010-06-06T22:00:00+00:00` to `2010-06-06T22:05:00+00:00`; timeframe `1m`.

## Concrete Contract Mode

Raw CSV actual counts: `{'FUTURE.CME.GC.GCN0': 3, 'FUTURE.CME.GC.GCQ0': 5}`
Replay source counts after gap synthesis: `{'FUTURE.CME.GC.GCN0': 5, 'FUTURE.CME.GC.GCQ0': 5}`
Strategy counts: `{'FUTURE.CME.GC.GCN0': 5, 'FUTURE.CME.GC.GCQ0': 5}`
Strategy final DataView history counts: `{'GCN0': 5, 'GCQ0': 5}`
Synthetic source bars: `2`

## Continuous Root Mode

Raw selected counts: `{'CONTINUOUS_FUTURE.CME.GC': 5}`
Replay source counts: `{'CONTINUOUS_FUTURE.CME.GC': 5}`
Strategy counts: `{'CONTINUOUS_FUTURE.CME.GC': 5}`
Selected concrete contracts: `{'FUTURE.CME.GC.GCQ0': 5}`
Strategy final DataView history counts: `{'GC': 5}`

## Semantic Note

Strategy.on_bar receives CONTINUOUS_FUTURE.CME.GC in root roll mode; the selected concrete contract is recorded by roll selection and used by execution resolution, not exposed as the strategy bar.instrument_id.

Full event samples and roll selections are in `gc_strategy_data_validation.json`.
