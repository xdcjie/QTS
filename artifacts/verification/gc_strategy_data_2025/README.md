# GC 2025 Historical Data To Strategy Validation

Window: `[2025-01-01T00:00:00Z, 2026-01-01T00:00:00Z)`; timeframe `1m`.

## Summary

- Raw CSV rows in window: `1368789`
- Raw spread rows excluded: `604033`
- Raw outright rows: `764756` across `33` symbols
- Concrete all-contract source bars: `3109460`
- Concrete all-contract strategy bars: `3109460`
- Concrete synthetic gap bars: `2344704`
- Continuous source bars: `354570`
- Continuous strategy bars: `354570`

## Concrete All-Contract Mode

Top strategy counts: `{'FUTURE.CME.GC.GCZ5': 334551, 'FUTURE.CME.GC.GCV5': 263268, 'FUTURE.CME.GC.GCG6': 250581, 'FUTURE.CME.GC.GCQ5': 217535, 'FUTURE.CME.GC.GCJ6': 209694, 'FUTURE.CME.GC.GCM5': 164341, 'FUTURE.CME.GC.GCM6': 160282, 'FUTURE.CME.GC.GCQ6': 148046, 'FUTURE.CME.GC.GCZ6': 141781, 'FUTURE.CME.GC.GCU5': 140183, 'FUTURE.CME.GC.GCF6': 134467, 'FUTURE.CME.GC.GCX5': 132780}`

Top synthetic counts: `{'FUTURE.CME.GC.GCV5': 190803, 'FUTURE.CME.GC.GCJ6': 181762, 'FUTURE.CME.GC.GCZ5': 178274, 'FUTURE.CME.GC.GCG6': 172231, 'FUTURE.CME.GC.GCM6': 146902, 'FUTURE.CME.GC.GCQ6': 143849, 'FUTURE.CME.GC.GCZ6': 136247, 'FUTURE.CME.GC.GCU5': 122652, 'FUTURE.CME.GC.GCX5': 120115, 'FUTURE.CME.GC.GCH6': 118745, 'FUTURE.CME.GC.GCF6': 115646, 'FUTURE.CME.GC.GCQ5': 112202}`

## Continuous Root Mode

Selected concrete contracts: `{'FUTURE.CME.GC.GCG5': 26176, 'FUTURE.CME.GC.GCG6': 34731, 'FUTURE.CME.GC.GCH5': 2, 'FUTURE.CME.GC.GCJ5': 56306, 'FUTURE.CME.GC.GCM5': 59127, 'FUTURE.CME.GC.GCQ5': 60455, 'FUTURE.CME.GC.GCU5': 1, 'FUTURE.CME.GC.GCV5': 12, 'FUTURE.CME.GC.GCZ5': 116945, 'FUTURE.CME.GC.GCZ8': 1}`

Dataset stats: `{'rows_seen': 14676152, 'bars_emitted': 353756, 'symbols_excluded': 604033, 'spreads_excluded': 604033, 'contracts_excluded': 411000, 'invalid_rows': 0}`

Full per-contract counts, first/last bars, samples, and roll selection samples are in `gc_strategy_data_2025_validation.json`.
