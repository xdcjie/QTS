# QTS Redundancy and Deletion Plan

This document lists deletion or consolidation candidates from `CODE_INVENTORY(1).md`. It does not authorize deletion by itself. Each item must pass the deletion gate below.

## Deletion gate

Before deleting a file, class, function, method, or wrapper, verify all of the following:

```bash
rg "<symbol_or_file_stem>" .
rg "from .* import <symbol>" backend tests scripts examples docs
rg "<module_path>" backend tests scripts examples docs pyproject.toml Makefile
```

Also check:

- package `__init__.py` exports
- FastAPI route registration
- CLI scripts and Makefile targets
- Protocol/interface methods
- dependency injection and callback registration
- docs and examples
- external compatibility assumptions
- tests and anchor tests

If the item is part of a public API or CLI contract, prefer a thin compatibility wrapper over deletion.

## Keep by default

- Empty `__init__.py` files. They are package markers and should not be deleted unless the repository explicitly switches to namespace packages.
- Protocol methods. Static inventory may show no direct callers, but implementations depend on them.
- Framework route handlers. FastAPI or other frameworks register them dynamically.
- CLI `main()` functions. They may be invoked by scripts/Makefile.
- Pydantic schema classes used by API serialization.

## Candidate group A — empty or ambiguous non-`__init__` scripts

### `scripts/ibkr_collect_environment_evidence.py`

Inventory status: zero class/function symbols while `qts.application.commands.ibkr_environment_evidence` exists with real command symbols.

Recommended action:

1. If this script is a documented CLI entrypoint, implement a single `main()` that delegates to `qts.application.commands.ibkr_environment_evidence`.
2. If there is no Makefile/docs/examples reference, delete it.
3. Do not duplicate IBKR evidence collection logic inside the script.

Verification:

```bash
make guardrails
make test-unit
rg "ibkr_collect_environment_evidence" docs scripts Makefile pyproject.toml tests examples
```

### `scripts/ibkr_paper_order_lifecycle_drill.py`

Inventory status: zero class/function symbols while `qts.application.commands.ibkr_paper_order_lifecycle_drill` exists with real command symbols.

Recommended action:

1. If the script is a CLI entrypoint, implement a thin `main()` delegating to the application command.
2. If not referenced, delete it.
3. Do not duplicate drill logic in scripts.

Verification:

```bash
make guardrails
make test-unit
rg "ibkr_paper_order_lifecycle_drill" docs scripts Makefile pyproject.toml tests examples
```

## Candidate group B — script wrappers that must remain thin

### `scripts/verify_guardrails.py`

Current inventory suggests the central implementation owner is `qts.quality.guardrails`, with `run_guardrails` and `main` available. The script should remain a thin wrapper only.

Recommended action:

- If duplicate guardrail logic exists in the script, remove it and delegate to `qts.quality.guardrails.main`.
- If already thin, keep it.

Verification:

```bash
make guardrails
make test-unit
python scripts/verify_guardrails.py
```

## Candidate group C — module density, not immediate deletion

These are not deletion candidates yet. They are split/refactor candidates.

### `qts.reconciliation`

Contains snapshots, drift kinds/items, reports, startup gate decisions, engine, and helper comparisons. Split into a package after characterization tests. Do not delete symbols directly.

Target:

```text
qts/reconciliation/
  snapshots.py
  drift.py
  report.py
  engine.py
  startup_gate.py
```

### `qts.data.live_feed`

Contains live feed capabilities, subscription DTOs, live events, failure types, reconnect policy, protocol, and fake adapter. Split by concept; do not delete until compatibility re-exports are in place.

Target:

```text
qts/data/live/
  capabilities.py
  subscriptions.py
  events.py
  reconnect.py
  adapter.py
  fake_adapter.py
```

### `qts.execution.broker`

Currently cohesive as an execution boundary, but dense. Decide whether to split only after tests and public import review.

Possible target:

```text
qts/execution/broker/
  capabilities.py
  requests.py
  reports.py
  adapter.py
  fake_adapter.py
```

## Candidate group D — helper ownership review

Run:

```bash
rg -n "^def _|^class _" backend/src/qts
```

Class-centric modules should not keep module-private helpers that only implement one class's construction, validation, mapping, serialization, or state transitions. Move such helpers onto the owning class. Keep module-private helpers only for pure shared algorithm steps.

High-priority files:

- `qts.quality.guardrails`: many module-private helper algorithms; acceptable for now because they implement rule checks, but should eventually be grouped if maintenance pressure grows.
- `qts.backtest.engine`: `_dataset_payload`, `_zero_time`, `_BacktestExecutionAdapter` should move to owning concepts.
- `qts.backtest.actor_loop`: mailbox extraction helpers can remain private static methods if they only serve the loop.

## Candidate group E — docstring cleanup, not deletion

Many public symbols lack docstrings and are inferred as “Perform x.” Do not delete them. Add concise docstrings for public stable APIs.

Priority:

- `StrategyContext` public methods
- `BacktestEngine` public methods
- `BacktestActorLoop`
- `OrderManager`
- `ReconciliationEngine`
- Live feed adapter boundary
- API route schemas

## Final deletion rule

Only delete after:

```text
1. Deletion safety map is complete.
2. Behavior characterization exists if behavior is non-trivial.
3. Compatibility decision is documented.
4. make guardrails passes.
5. make test-unit passes.
6. make test-integration passes if the item touches module flow.
7. make check passes before milestone completion.
```
