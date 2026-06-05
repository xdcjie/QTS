# Rust Core Migration Implementation Plan

## Goal

Build Rust acceleration for QTS without changing financial semantics. Python
remains the reference implementation until Rust passes golden and shadow gates.

## Phase 1: Data materialization

Files:

- `rust/crates/domain`: shared Rust domain values.
- `rust/crates/calendar`: session intervals and close-date session ids.
- `rust/crates/data`: timeframe parsing, bar aggregation, CSV/index materialize.
- `rust/crates/cli`: `qts-rs materialize`.

Acceptance:

- Rust unit tests cover timeframe parsing, `[start,end)` intervals, COMEX-style
  regular sessions, and OHLCV aggregation.
- Golden diff compares Rust materialized CSV/index output against Python output
  for fixed GC and SI fixtures.
- Rust output is not used by workflow/campaign until golden diff is clean.

## Phase 2: Replay tape

Files:

- `rust/crates/replay`: replay tape identity, serialization, deterministic
  sequencing, visible-at ordering.
- Python bridge only after replay sequence diff is clean.

Acceptance:

- Python/Rust replay sequence diff is clean for fixed GC/SI windows.
- Replay cache identity includes dataset hashes, timeframe, date range, symbols,
  roots, instrument ids, and roll policy.
- No bar is visible before `bar.end_time`.

## Phase 3: Backtest core

Files:

- `rust/crates/backtest`: deterministic backtest loop.
- `rust/crates/python`: narrow Python bridge.

Acceptance:

- Python/Rust golden backtests match processed bars, orders, fills, account
  state, equity curve samples, metrics, and manifest-compatible payloads.
- `next_bar_open` remains default and promotion-grade; optimistic fills remain
  gated.
- Rust backtests are shadow-only until release gates pass.

## Phase 4: Shadow/release verification

Files:

- Python research workflow/campaign verification paths.
- Rust bridge and diff artifact writers.

Acceptance:

- Workflow/campaign can run Python and Rust in shadow mode.
- Diff artifacts are deterministic and recorded with hashes.
- Release verification rejects Rust-backed evidence when any required diff is
  not clean.
