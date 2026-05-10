# Research Storage Decision

Date: 2026-05-10

## Decision

Keep CSV streaming for S5. Do not add `pyarrow` or another storage dependency in
this milestone.

## Invariant

New storage dependencies require evidence that the current CSV stream or JSONL
file-backed store is insufficient. Storage format must not redefine historical
data identity, contract metadata, bar interval semantics, or spread exclusion.

## Benchmark

Command: bounded GC/SI read over `[2010-06-06T22:00:00Z, 2010-06-06T22:05:00Z)`,
then write/read the same emitted bars through the current JSONL-backed
`ParquetMarketDataStore`.

Results:

| Path | Runtime | Memory Delta | Rows / Bars | Output Size |
| --- | ---: | ---: | --- | ---: |
| CSV streaming | 0.000205s | 0.016 MB | GC rows 14, GC bars 9, GC spreads 4; SI rows 8, SI bars 6, SI spreads 1 | n/a |
| JSONL write | 0.001068s | 0.0 MB | 15 bars written | 5,807 bytes |
| JSONL read | 0.001007s | n/a | 61 observations from repeated per-instrument reads | 5,807 bytes |

## Rationale

The current S5 requirements need explicit provenance, validation, bounded
streaming, determinism, and opt-in full-data runs. The CSV reader now streams
rows lazily, excludes spreads visibly, and stops at a bounded end timestamp for
date-window runs. That is enough for S5 without loading full GC/SI files into
memory.

The existing JSONL store remains useful as a simple file-backed store behind the
market data boundary, but this benchmark does not justify adding a production
storage dependency. A future milestone can revisit `pyarrow` if full-range
research runs show CSV streaming or JSONL output is too slow, too large, or too
awkward for repeated multi-year analysis.

## Follow-Up Gate

Reconsider a new dependency only with evidence from a larger benchmark that
records runtime, peak memory, output size, and developer ergonomics for the same
query across CSV streaming, JSONL, and the proposed storage engine.
