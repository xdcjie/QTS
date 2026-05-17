# OPT-62..66 — Close Existing Capabilities

- Document type: plan + status matrix
- Owner: TBD
- Created: 2026-05-17
- Predecessor: `docs/plan/2026-05-17_opt_56_57_58_19_quant_workflow_plan.md`
- Scope: stop adding new capabilities; finish wiring the 22 deferred
  symbols + give them an expiry; eliminate the new-user onboarding gap.

## 0. Why this batch, why now

Six rounds of project review converged on a structural finding: capability
accrual has outpaced capability adoption. OPT-61 made the gap visible (22
deferred production symbols); this batch starts closing it.

| Item | Theme | Bytes saved or value unlocked |
|---|---|---|
| OPT-62 | enforce deferral expiry | prevent permanent "shipped-but-unwired" debt |
| OPT-63 | wire `PersistentDriftKillSwitch` | live-trading safety net finally active |
| OPT-64 | wire `DurableSnapshotStore` | cross-day / cross-restart state preserved |
| OPT-65 | optimizer CLI + quickstart | OPT-19 actually invocable by a user |
| OPT-66 | `GETTING_STARTED.md` + minimal strategy | new-user time-to-first-backtest |

End of batch: the wiring_deferrals.md list shrinks by ≥8 entries
(persistent-drift 1 + durable-snapshot 2 + optimizer 5).

## 1. Non-negotiable platform invariants

All items must preserve invariants from
`docs/architecture/backtest_live_parity.md` + CLAUDE.md / AGENTS.md:

| # | Invariant | Anchor |
|---|---|---|
| 1 | Risk runs before order submission in every mode. | RiskEngine |
| 2 | OrderManagerActor owns order state. | order_manager |
| 3 | AccountActor owns cash and positions. | account_actor |
| 4 | Backtest cannot use a shortcut that live cannot use. | parity doc |
| 5 | New production symbols must have a non-test caller or be deferred. | OPT-61 CallerPresenceRule |
| 6 | Smallest correct solution. | §5 Simplicity |
| 7 | Every spec touched needs a first failing test before production edits. | matrix style |

## 2. Status matrix (updated as items land)

| Item | Status | First red gate | Verified green | Commit |
|---|---|---|---|---|
| OPT-62 deferral expiry + target_pr fields | TODO | `test_deferral_entries_have_expiry.py` | — | — |
| OPT-63 wire `PersistentDriftKillSwitch` to runtime | TODO | `test_persistent_drift_trips_runtime_kill_switch.py` | — | — |
| OPT-64 wire `DurableSnapshotStore` + cross-restart anchor | TODO | `test_durable_snapshot_cross_session_recovery.py` | — | — |
| OPT-65 optimizer CLI + quickstart example | TODO | `test_run_optimizer_cli_outputs_ranked_results.py` | — | — |
| OPT-66 `GETTING_STARTED.md` + `hello_world.py` | TODO | `test_getting_started_quickstart.py` | — | — |

Marking an item DONE requires: first red gate recorded, focused green
recorded, `make check` recorded, commit linked, this matrix updated.

---

# Lane A — Deferral discipline (OPT-62)

## OPT-62 — Deferrals carry `expires_on` + `target_pr`

### Goal
Every entry in `docs/plan/wiring_deferrals.md` has a structured expiry
date and a target follow-up identifier. `CallerPresenceRule` rejects
entries whose expiry has passed, preventing the deferral list from
silently accumulating into permanent debt.

### Domain fact / invariant
A wiring deferral without an expiry is a permanent deferral. Same lesson
as `platform_freeze_exceptions.yaml` learned in OPT-18 — give every
exception a clock.

### Correct owner / boundary
`docs/plan/wiring_deferrals.md` (data) +
`qts.quality.rules.caller_presence` (loader / enforcement).

### Forbidden shortcut
Allowing existing 22 entries to expire on the same day (the OPT-18
"avalanche" risk); leaving entries without a target identifier.

### Scope
- Extend deferral line format:
  ```
  qts.foo.Bar  expires=YYYY-MM-DD  target=OPT-NN
  ```
  Three whitespace-separated tokens: FQ symbol, expiry date, target.
  `target=` may be a category sentinel (`framework`, `library`,
  `internal`) when no follow-up OPT is planned.
- Migrate the 22 existing entries with expiry dates **spread across
  the next 8 weeks** based on category:
  - framework / library / internal: 2027-05-17 (1 year, like freeze exceptions)
  - wiring_followup: 2026-08-17 (3 months) so re-evaluation is forced
- `CallerPresenceRule._load_deferrals` parses the new format and stores
  expiry per symbol. New helper method
  `expired_deferrals(today)` returns the list of expired entries.
- New violation code `EXPIRED_DEFERRAL` issued when a deferral expires
  and the symbol still lacks a caller.

### Required gates
- `tests/quality/test_deferral_entries_have_expiry.py`:
  - Every line in the fenced code block has 3 tokens.
  - Every expiry is ISO date.
  - No expiry is more than 1 year out.
  - No expiry is in the past.
  - `wiring_followup` category entries expire within 3 months.

### ETA
0.5 day.

---

# Lane B — Wire existing classes into the runtime

## OPT-63 — `PersistentDriftKillSwitch` connected to reconciliation

### Goal
After N consecutive `DIVERGENT` reconciliation cycles on the same drift
key (default N=3, from `PersistentDriftConfig`), the runtime activates
its kill switch and transitions to `OBSERVATION_ONLY`. Further order
submissions are blocked.

### Domain fact / invariant
Persistent broker/internal state drift is a financial-correctness
emergency. The class to detect it shipped in OPT-47; the runtime to
react to it shipped earlier. Connecting the two is the wire that has
been missing.

### Correct owner / boundary
`qts.reconciliation.engine.ReconciliationEngine` (or wherever
reconciliation reports are produced per cycle) feeds reports into
`PersistentDriftKillSwitch.observe(report)`. On `decision.tripped`, the
existing kill-switch path is invoked (e.g., setting
`OrderSubmissionPermission.OBSERVATION_ONLY` via `SafetyController`).

### Forbidden shortcut
Bypassing the existing kill-switch path; embedding drift counting into
`ReconciliationEngine` (it should remain stateless).

### Scope
- Locate the reconciliation result emitter and inject a
  `PersistentDriftKillSwitch` instance.
- On `decision.tripped`: emit `runtime.kill_switch_activated` event
  through the existing observability path; trigger the runtime
  `SafetyController.activate_kill_switch(...)` (or equivalent).
- One end-to-end anchor in `tests/integration/`.

### Required gates
- `tests/integration/test_persistent_drift_trips_runtime_kill_switch.py`:
  - Construct a reconciliation pipeline; feed 2 divergent reports on
    same key → runtime not in observation_only yet.
  - Feed the 3rd → runtime is in observation_only AND a
    `runtime.kill_switch_activated` event is recorded.
  - Subsequent order intent is rejected by runtime.
- Remove `qts.reconciliation.persistent_drift.PersistentDriftKillSwitch`
  from `docs/plan/wiring_deferrals.md`.

### ETA
1 day.

---

## OPT-64 — `DurableSnapshotStore` + cross-restart recovery

### Goal
A backtest or paper run can be configured with a `DurableSnapshotStore`;
the runtime persists actor snapshots at the cadence dictated by
`SnapshotFrequencyPolicy`; after a simulated restart, the previous run's
state is restored byte-identically.

### Domain fact / invariant
Cross-restart state preservation is a hard requirement for live trading.
Snapshot infrastructure (DurableSnapshotStore, FileSnapshotStore,
SnapshotFrequencyPolicy) has existed; no production caller has used it.

### Correct owner / boundary
`qts.runtime.session.RuntimeSession` (or backtest equivalent) accepts an
optional `snapshot_store + snapshot_frequency_policy` pair; the runtime
calls `store.save(snapshot)` per the policy schedule. On startup,
`store.load_latest()` returns the most recent snapshot for restoration.

### Forbidden shortcut
Reimplementing snapshot logic at a higher layer; allowing
test-only `InMemorySnapshotStore` to satisfy the production caller gate
on its own (use the real `DurableSnapshotStore` / `FileSnapshotStore`).

### Scope
- Inspect `qts.runtime.state_recovery` to understand the current
  Protocol vs concrete split. Determine which class becomes the wired
  production caller.
- Add a runtime API that accepts the snapshot store; invoke save +
  load at appropriate phases.
- One end-to-end anchor: backtest runs 5 bars, snapshot at bar 3, fresh
  run is restored from the snapshot, completes bars 4-5, final state
  byte-identical to a continuous run.

### Required gates
- `tests/anchor/test_durable_snapshot_cross_session_recovery.py`:
  - Continuous run: produce final `AccountSnapshot` over 5 bars.
  - Two-phase run: bars 1-3 + snapshot save + restart + bars 4-5.
  - Final cash, holdings, and realized PnL match byte-for-byte.
- Remove `qts.runtime.state_recovery.DurableSnapshotStore` and
  `qts.runtime.state_recovery.SnapshotFrequencyPolicy` from
  `docs/plan/wiring_deferrals.md`.

### ETA
1-2 days.

---

# Lane C — Unlock OPT-19 + onboarding

## OPT-65 — `scripts/run_optimizer.py` CLI + quickstart example

### Goal
A user invokes
```
uv run python scripts/run_optimizer.py configs/optimizer/quickstart.yaml
```
and gets a printed ranked-results table from a real parameter sweep.

### Domain fact / invariant
The optimizer is a library API exposed for user consumption. Without a
script driver + example config + working example strategy, the
OPT-19 classes remain technically deferred forever.

### Correct owner / boundary
- `scripts/run_optimizer.py` — CLI entrypoint, parses YAML config,
  builds `OptimizationJob`, calls `OptimizationRunner.run`, prints
  ranked results.
- `examples/strategies/quickstart_optimizer.py` — minimal
  parameterizable strategy used by the config.
- `configs/optimizer/quickstart.yaml` — the example config.

### Forbidden shortcut
Embedding strategy code into the CLI; bypassing `BacktestEngine`.

### Scope
- YAML schema for the config:
  ```yaml
  strategy_module: examples.strategies.quickstart_optimizer
  strategy_factory: build_strategy
  initial_cash: "100000"
  bars_config: path/to/historical/spec.yaml  # or inline list
  objective_metric: sharpe_ratio
  output_root: artifacts/optimizer
  parameters:
    - name: window
      values: [5, 10, 20]
    - name: target_quantity
      values: ["1", "2"]
  ```
- `quickstart_optimizer.py` — small (~30 line) MA-cross style strategy
  that reads `window` + `target_quantity` from constructor kwargs.
- `scripts/run_optimizer.py` parses YAML, imports the module + factory
  via dotted path, builds `OptimizationJob`, runs it, formats a
  Markdown / ASCII table of ranked results.

### Required gates
- `tests/integration/test_run_optimizer_cli_outputs_ranked_results.py`:
  - Invoke the CLI on a tmp_path-resolved minimal config (with
    inline bars so the test is hermetic).
  - Stdout contains a ranked results table with one row per parameter
    combination.
  - Best-objective row's parameters match the offline-computed best.
- Remove `qts.research.optimizer.*` (5 entries) from
  `docs/plan/wiring_deferrals.md`.

### ETA
1 day.

---

## OPT-66 — `GETTING_STARTED.md` + minimal `hello_world.py`

### Goal
A new user reads `docs/GETTING_STARTED.md`, copies the 5-line strategy
example, runs the backtest CLI, sees a manifest with statistics — in
under 10 minutes.

### Domain fact / invariant
Onboarding friction is the leading cause of project abandonment.
The current `examples/strategies/` smallest entry is 23 lines; users
need ~5.

### Correct owner / boundary
- `docs/GETTING_STARTED.md` — durable onboarding doc.
- `examples/strategies/hello_world.py` — minimal strategy.

### Forbidden shortcut
Adding more example strategies that hide the smallest one;
GETTING_STARTED that links to N other docs instead of being
self-contained for first-90-seconds.

### Scope
- `hello_world.py`: ≤ 25 lines including imports. Buy on first bar,
  sell on last. Pure SDK use, no `Any` typing.
- `docs/GETTING_STARTED.md` covers:
  1. What QTS is (2 sentences).
  2. Install (`uv sync --group api`).
  3. The 5-line strategy (full file shown).
  4. Run the backtest (`uv run python scripts/run_backtest.py ...`).
  5. Look at the manifest + statistics (1 paragraph).
  6. "Where to go next" — links to SDK docs + example strategies +
     optimizer CLI (OPT-65).

### Required gates
- `tests/quality/test_getting_started_quickstart.py`:
  - `hello_world.py` exists; ≤ 25 lines.
  - `hello_world.py` parses + mypy clean (via existing typecheck).
  - `GETTING_STARTED.md` references `hello_world.py` and
    `scripts/run_backtest.py` (real paths exist).
- `tests/integration/test_hello_world_strategy_runs.py`:
  - Build a `BacktestEngine` with `HelloWorldStrategy` from
    `examples.strategies.hello_world`, run 3 bars, assert manifest
    produced + `total_return` key present.

### ETA
0.5 day.

---

## 3. Execution lanes (parallel)

| Lane | Owner | Files | Exit evidence |
|---|---|---|---|
| A | Main session | `qts.quality.rules.caller_presence`, `docs/plan/wiring_deferrals.md` | OPT-62 green |
| B | Main session | `qts.runtime.session`, `qts.reconciliation.engine`, `qts.runtime.safety_controller` | OPT-63 + 64 green; 3 deferrals removed |
| C | Main session | `scripts/run_optimizer.py`, `examples/strategies/quickstart_optimizer.py`, `configs/optimizer/`, `docs/GETTING_STARTED.md`, `examples/strategies/hello_world.py` | OPT-65 + 66 green; 5 deferrals removed |

Sequencing within lanes:
- A is independent; can land anytime. Lands first so the deferral format
  for entries removed by B and C is up to date.
- B: OPT-63 before OPT-64 (no shared files, but B's wiring patterns
  inform B's other slice).
- C: OPT-65 before OPT-66 (the getting-started doc can reference the
  optimizer CLI as a "where to go next" link).

## 4. Verification commands

```bash
PYTHONPATH=backend/src uv run pytest tests/anchor tests/integration tests/unit tests/quality -q
make guardrails
make typecheck
make lint
make check
PYTHONPATH=backend/src uv run python scripts/run_optimizer.py configs/optimizer/quickstart.yaml
```

## 5. Out of scope (explicit defer)

Items in the round-six analysis but not in this batch:

- **OPT-67** — 7-day IBKR paper soak with evidence. This is the
  capstone validating "internal team can run live"; it depends on
  OPT-63 + 64 landing first.
- **OPT-19 follow-up** — walk-forward + concurrency for the optimizer.
- **OPT-34** — scheduler / `on_end_of_day` SDK.
- **OPT-30** — corporate actions / dividends / splits.

These stay in the backlog and land after the current batch ships.

## 6. How this plan is used

- Each item is referenced by ID in PR titles.
- Status flips to `IN-PROGRESS` when work starts and to `DONE` with
  commit hash when verified green.
- New gaps discovered during this work go to the source backlog with
  the next free OPT-NN; no renumbering.
- Entries removed from `wiring_deferrals.md` must be explicitly named
  in the relevant commit message so the audit trail is intact.
