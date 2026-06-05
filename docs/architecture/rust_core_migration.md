# Rust Core Migration

This document defines the safe migration path for adding a Rust execution core
to QTS. Rust code is an implementation accelerator, not a new source of domain
truth. Python remains the Research OS and artifact orchestration layer until
Rust output is proven equivalent through golden and parity gates.

## Migration boundary

Rust is allowed to own deterministic, performance-sensitive core work:

- historical CSV/index reading and timeframe materialization;
- replay tape/cache construction and replay sequencing;
- deterministic backtest execution after parity gates are clean;
- narrow Python bindings for reviewed Rust entrypoints.

Rust must not bypass the existing Strategy SDK -> RiskEngine ->
OrderManagerActor -> ExecutionActor -> AccountActor semantic path. If a Rust
backtest loop implements this path internally, its observable orders, fills,
account state, equity, metrics, and manifests must match the Python reference
before it is used for research selection or promotion evidence.

## Phase plan

### Phase 1: Rust data engine

Entry: `qts-rs materialize`.

Owner: `rust/crates/domain`, `rust/crates/calendar`, `rust/crates/data`, and
`rust/crates/cli`.

Required behavior:

- parse supported timeframes: `1m`, `2m`, `3m`, `5m`, `10m`, `15m`, `30m`,
  `1h`, `4h`, and `1d`;
- preserve `[start, end)` intervals;
- aggregate OHLCV with first-open, max-high, min-low, last-close, summed volume;
- keep `<1d` bars exchange-clock aligned;
- keep `1d` bars session-aligned;
- never synthesize missing source rows inside materialization unless an explicit
  source-boundary synthesizer is invoked and recorded.

Gate:

- Rust unit tests for timeframe parsing, interval membership, and aggregation;
- Python/Rust golden CSV diff for at least one GC fixture and one SI fixture;
- Python/Rust `.index.json` compatibility check before replacing Python
  materialization in any workflow.

### Phase 2: Rust replay tape

Entry: Python workflow materialized replay cache or `qts-rs replay`.

Owner: `rust/crates/replay`.

Required behavior:

- produce a deterministic replay sequence from configured historical data;
- preserve visible-at semantics: a completed bar is visible only at `bar.end`;
- preserve roll selections and provenance identity;
- use stable cache identity that includes data/config/roll/timeframe inputs.

Gate:

- Python/Rust replay sequence diff over fixed windows;
- cache identity stability tests;
- no-lookahead tests for visible-at ordering.

### Phase 3: Rust backtest core

Entry: Python bridge or `qts-rs backtest`.

Owner: `rust/crates/backtest` and `rust/crates/python`.

Required behavior:

- preserve fill timing (`next_bar_open` by default);
- preserve risk/order/execution/account state transitions;
- preserve continuous-future roll semantics;
- emit manifest-compatible metrics and artifacts.

Gate:

- orders, fills, final account, equity, and metrics match Python golden runs;
- promotion-grade fill timing remains enforced;
- Rust backtests run only in shadow or explicit experimental mode until gates
  are clean.

### Phase 4: Parity and release verification

Entry: workflow/campaign verification.

Owner: Python research orchestration plus Rust bridge.

Required behavior:

- dual-run Python and Rust on selected workflows;
- record diff artifacts;
- reject Rust-backed evidence when any required diff is not clean.

Gate:

- workflow/campaign release verify must include engine-parity evidence before
  Rust results can replace Python results.

Current executable gate:

```bash
PYTHONPATH=backend/src uv run python scripts/verify_rust_core_migration.py
```

This gate must remain clean before any workflow or campaign can treat Rust
output as replacement evidence. Until a workflow/campaign integration explicitly
records a clean engine-parity diff, `qts-rs backtest` requires `--shadow` and
Rust-backed results must not replace Python research evidence.

When `--output` is provided, the executable gate writes engine-parity evidence
plus hashed diff artifacts for at least `phase2_replay_sequence_diff`,
`phase3_engine_backtest_diff`, and
`phase3_continuous_future_roll_diff`. Workflow/campaign release verification
must validate those artifact paths, hashes, phases, and clean statuses before
accepting the evidence.

The executable gate also requires `qts-rs backtest --shadow --output-dir` to
emit summary, manifest, orders, fills, trade ledger, equity curve, and
statistics artifacts that are loadable through the Python
`BacktestRunReportLoader`. The engine-parity backtest gate must include observable
`risk.accepted`, `order.accepted`, `execution.filled`, and `account.updated`
events so the Rust path remains aligned with the required RiskEngine,
OrderManagerActor, ExecutionActor, and AccountActor semantics before any
replacement use is considered.

## Review checklist

- Does the Rust path preserve the documented Flow ID owner and entrypoint?
- Does every bar remain half-open and visible only when complete?
- Does `1d` use session intervals rather than 24-hour buckets?
- Does the migration add a golden or parity gate for every observable behavior?
- Is Python still the source of research artifact orchestration until parity is
  proven?
