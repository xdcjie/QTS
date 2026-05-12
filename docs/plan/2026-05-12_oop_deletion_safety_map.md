# OOP Deletion Safety Map (baseline)

Date: 2026-05-12

Scope:
- Candidate files relevant to OOP-00-T02 before redundant-script cleanup.
- For each candidate: import/usage status in source/tests/docs/CLI plus package exports.

## Candidate status table

| Candidate | Source imports / runtime references | CLI or entrypoint references | Docs/examples | Package exports | Tests | Decision basis |
|---|---|---|---|---|---|---|
| `scripts/ibkr_collect_environment_evidence.py` | Not imported by other production modules. | No Makefile target currently references this script directly. | No docs/examples references found. | N/A (script module). | `tests/unit/scripts/test_ibkr_collect_environment_evidence.py` imports module and calls `collect_environment_evidence`. | Keep as wrapper unless command module is promoted and tests are migrated. |
| `scripts/ibkr_paper_order_lifecycle_drill.py` | Imported by `scripts/run_paper_ibkr.py` (`from scripts.ibkr_paper_order_lifecycle_drill import main as _run_paper_drill`). | Potential direct script entrypoint only; no Makefile target. | No docs/examples references found. | N/A (script module). | `tests/unit/scripts/test_ibkr_paper_order_lifecycle_drill.py` imports module and calls `run_paper_order_lifecycle_drill`. | Keep as wrapper currently to avoid breaking `run_paper_ibkr.py` import chain. |
| `scripts/verify_guardrails.py` | Imported by `tests/unit/scripts/test_verify_guardrails.py` (`importlib` module load). | Used by `make guardrails` in `Makefile` and docs testing guidance. | `docs/testing/testing_strategy.md` references canonical guardrail entrypoint. | N/A (script module). | `tests/unit/scripts/test_verify_guardrails.py` relies on exported module API names (`run_guardrails`, `GuardrailSuite`). | Keep as wrapper only; preserve compatibility exports.

## Additional notes

- No candidate is currently import-free in tests, so none are safe for deletion without test edits.
- `scripts/run_paper_ibkr.py` is an existing entrypoint and depends on `scripts/ibkr_paper_order_lifecycle_drill.py`.
- No package-level `__init__` exports found for these script modules.
