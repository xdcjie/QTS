# 2026-05-12 — OOP-13 Final Deletion Register

## Updated inventory snapshot

The cleanup after OOP refactors is based on:
- `docs/plan/2026-05-12_qts_redundancy_deletion_candidates.md`
- `git status` and cross-boundary checks from the finalization point
- `make test-unit`, `make test-integration`, and `make test-anchor` for behavior and API safety

## Approved deletions

| File | Rationale | Status |
|---|---|---|
| `backend/src/qts/data/bars/builder.py` | Empty placeholder module in `OOP-01` cleanup window | Deleted |
| `backend/src/qts/data/bars/validation.py` | Empty placeholder module in `OOP-01` cleanup window | Deleted |

## Deferred / kept intentionally

| File | Why kept | Guardrail impact |
|---|---|---|
| `scripts/run_api.py` | Needed thin CLI wrapper | No deletion |
| `scripts/run_paper_ibkr.py` | Needed script entrypoint for paper drill workflow | No deletion |
| `scripts/run_worker.py` | Obsolete placeholder script | Deleted |
| `backend/src/qts/strategy_sdk/context.py` | Current Strategy SDK facade and initialization semantics still in use | No deletion |
| `backend/src/qts/execution/order_manager.py` | Domain-facing orchestrator for order lifecycle; retained as shared execution service | No deletion |

## Verification gates completed before finalization

- `make test-unit`
- `make test-integration`
- `make test-anchor`
- `make guardrails` (via `scripts/verify_guardrails.py`)

## Deletion constraints satisfied
- `builder.py` and `validation.py` were imported nowhere in runtime path at time of deletion.
- No public API symbols were removed in this batch.
- Backtest and API tests pass with the current tree.

## Change request for downstream cleanup
- `scripts/run_worker.py` has been removed; runtime worker ownership should be added through a concrete command when needed.
