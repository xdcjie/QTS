# QTS Runtime Readiness M0 Review Status Matrix

Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`

Scope: Milestone 0 - canonical runtime entrypoint, architecture inventory, and guardrail trust

Baseline: 2026-05-16, `HEAD 526b3eb`

## Completion Rules

M0 is complete only when `RuntimeSession` is the sole broker-capable runtime
entrypoint, broker startup/order-result concepts live in canonical modules,
architecture inventory generation blocks stale text, and guardrails are enforced
by CI and unit fixtures.

No retained alias, transitional import path, second runtime facade, or passive
documentation note may satisfy an acceptance condition. Renamed or removed
production APIs must be updated at call sites directly, with tests or guardrails
blocking reintroduction.

## Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Broker-capable runtime order submission has one production entrypoint. | `RuntimeSession` and its actor/risk/order path. | Keeping another runtime facade with `submit_order`, `degrade`, or `recover`. | Import/search guard plus runtime tests proving only `RuntimeSession` owns broker-capable submission. |
| Broker startup and runtime order-result concepts use canonical module names. | `qts.runtime.broker_startup` and `qts.runtime.order_result`. | Importing broker startup/order result from a live-named module. | Removed-import guard and import tests for canonical paths. |
| Architecture HTML/source inventory cannot carry stale review text. | Source inventory generator and generated architecture docs. | Manually editing generated HTML while stale detector stays blind. | `test_panorama_has_no_stale_architecture_text` and generator failure on stale tokens. |
| Guardrails are a hard gate, not a note. | `make guardrails`, CI workflow, and `GuardrailSuite`. | Having rules that are not in the suite or lack failing fixtures. | Rule membership tests, positive/negative fixture tests, and CI workflow assertion. |

## Status Matrix

| Task | Status | Current Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M0-1 Repair panorama/source inventory stale text | Implemented | `scripts/update_project_panorama_source_index.py` rejects stale generated-doc tokens during `--check`; `project_panorama.html` and `docs/architecture/backtest_live_parallel_sequence.html` were regenerated from current source. | None. | `tests/unit/test_project_panorama_html.py` covers stale-token rejection and generated-doc cleanliness. |
| M0-2 Retire `LiveRuntime` as a second runtime entrypoint | Implemented | `backend/src/qts/runtime/live.py` was removed; `qts.runtime` no longer exports `LiveRuntime`; runtime tests assert `RuntimeSession` is the broker-capable entrypoint. | None. | `tests/unit/runtime/test_live_runtime.py`, `tests/unit/runtime/test_live_startup_guard.py`, architecture smoke tests, and guardrail fixtures fail on reintroduction. |
| M0-3 Split/rename `qts.runtime.live` concepts | Implemented | Broker startup types live in `qts.runtime.broker_startup`; `RuntimeOrderResult` lives in `qts.runtime.order_result`; production and test imports were updated directly. | None. | `tests/unit/architecture/test_runtime_value_model_boundaries.py` and `tests/unit/scripts/test_verify_guardrails.py` block old import paths. |
| M0-4 GuardrailSuite CI hard gate | Implemented | `RemovedImportNoNewUsageRule` and `StaleArchitectureTextRule` are exported and included in `GuardrailSuite`; CI/local `make guardrails` enforces them. | None. | Rule membership, positive fixtures, negative fixtures, and report-output tests live in `tests/unit/scripts/test_verify_guardrails.py`. |

## Parallel Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main agent | Matrix, cross-lane integration, graph refresh, full verification, final commit. | Matrix updated with actual evidence, repository gates passing, and clean worktree after commit. |
| B | Worker | M0-2/M0-3 runtime entrypoint and canonical module migration. | `LiveRuntime` removed, canonical imports updated, focused runtime tests passing. |
| C | Worker | M0-1 source inventory stale detector and generated docs. | Generator/test fails on stale tokens, architecture docs regenerated cleanly. |
| D | Worker | M0-4 guardrail suite/CI rule coverage. | Guardrail suite membership and violation fixtures prove removed runtime imports and stale docs are blocked. |

## Verification Evidence

Fresh verification on 2026-05-16:

- `uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py tests/unit/scripts/test_verify_guardrails.py -q` -> 75 passed.
- `uv run pytest tests/unit/runtime/test_live_runtime.py tests/unit/runtime/test_live_startup_guard.py tests/unit/runtime/test_runtime_startup_gate.py tests/unit/runtime/test_runtime_session.py tests/integration/test_live_beta_flows.py -q` -> 58 passed.
- `uv run python scripts/update_project_panorama_source_index.py --html project_panorama.html --check && uv run python scripts/update_project_panorama_source_index.py --html docs/architecture/backtest_live_parallel_sequence.html --check` -> passed.
- `make format` -> 492 files left unchanged.
- `make lint` -> passed.
- `make guardrails` -> Architecture guardrails passed.
- `make typecheck` -> no issues in 473 source files.
- `make test-unit` -> 747 passed.
- `make test-integration` -> 75 passed, 4 skipped.
- `make test-anchor` -> 39 passed, 2 skipped.
- `make check` -> format, lint, guardrails, typecheck, unit, integration, and anchor gates passed.

The production source and generated architecture documents contain no direct
`qts.runtime.live` import path or `LiveRuntime` class definition outside the
guardrail blocklist/remediation text.

## Verification Plan

```bash
uv run pytest tests/unit/runtime tests/integration/test_live_beta_flows.py tests/unit/test_architecture_baseline_smokes.py -q
uv run pytest tests/unit/test_backtest_live_parallel_sequence_html.py tests/unit/test_project_panorama_html.py tests/unit/scripts/test_verify_guardrails.py -q
make format
make lint
make guardrails
make typecheck
make test-unit
make test-integration
make test-anchor
make check
```

M0 cannot close while any production code imports `qts.runtime.live`, while
`LiveRuntime` exists, or while generated architecture docs contain stale review
tokens.
