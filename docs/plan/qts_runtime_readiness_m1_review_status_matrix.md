# QTS Runtime Readiness M1 Review Status Matrix

> Source backlog: `docs/plan/qts_runtime_readiness_deep_review_tasks.md`
> Scope: Milestone 1 - Backtest / Paper readiness acceptance suite
> Baseline date: 2026-05-16
> Baseline note: working tree already contains unrelated runtime and architecture changes. This matrix records the M1 execution plan without reverting or relying on those changes.

## Completion Rules

A Milestone 1 task is `Complete` only when every acceptance condition in the source backlog has direct evidence from at least one hard gate:

- focused unit, integration, replay, anchor, or regression test
- strict guardrail rule that fails on violation
- generated artifact or manifest evidence
- real IBKR paper drill evidence for broker-connected gates
- fresh verification command output recorded in this matrix

Prior M1/M4 status matrices are evidence candidates only. They do not close this M1 unless the exact readiness gate is still present and passes in this working tree.

## M1 Correctness Invariants

| Invariant | Correct Owner / Boundary | Forbidden Shortcut | Required Gate |
|---|---|---|---|
| Same backtest config, dataset, topology, and execution assumptions produce the same normalized artifacts. | `BacktestEngine`, replay source/sequencer, runtime event sink, report writer. | Comparing only final PnL or ignoring nondeterministic event/artifact fields without an explicit normalized hash rule. | Deterministic replay test comparing normalized event, manifest, order, fill, and equity artifacts across two runs. |
| Bars are visible only at `[start, end)` close/visible time, never at bar start. | `ReplayMarketDataSource`, replay sequencer, `DataView`, aggregation/resample boundary. | Letting strategy code read full historical dataframes or using timezone display to redefine visibility. | No-lookahead contract tests for raw bars, resampled bars, same-timestamp multi-instrument ordering, and session boundary visibility. |
| Backtest manifests explain data provenance and execution assumptions. | `RuntimeManifest`, `BacktestReportWriter`, `ReplayMarketDataBundle`, execution/fill/cost capability models. | Writing partial manifest fields and treating report existence as provenance evidence. | Manifest validator positive and negative tests plus finalize-time rejection for missing required fields. |
| Paper simulated uses the shared runtime chain without broker credentials. | `RuntimeSession`, `RuntimeMarketDataCoordinator`, simulated execution adapter, actors, live/runtime event sink. | Creating a paper-only shortcut that bypasses RiskEngine, OrderManagerActor, ExecutionActor, or AccountActor. | CI smoke asserting canonical event chain and envelope fields without importing fakes from production code. |
| IBKR paper broker drill cannot accidentally hit live capital. | IBKR application command, config/environment guards, broker adapter/transport, reconciliation/reporting. | Allowing `U...` live accounts or port `4001` through a paper drill flag or compatibility path. | Paper drill tests plus real evidence gate requiring `DU...`, default port `4002`, reconciliation evidence, and artifact manifest. |

## Current Summary

| Task | Status | Evidence Candidate | Blocking Gap | Next Gate |
|---|---:|---|---|---|
| M1-1 deterministic replay suite | Complete | `tests/replay/test_backtest_determinism.py` now compares normalized manifest, events, orders, fills, trade ledger, equity curve, and event sequence gaps across two identical config/data/strategy runs. Fresh check: `uv run pytest tests/replay/test_backtest_determinism.py tests/replay/test_backtest_report_hash.py -q` -> `3 passed`. | None for automated deterministic replay artifacts. | Keep replay tests in CI/replay suite and rerun after artifact schema changes. |
| M1-2 no-lookahead / bar `visible_at` contracts | Complete | `tests/unit/data/test_replay_market_data_source.py` covers `test_bar_close_visible_only_at_bar_end`, same-timestamp deterministic ordering, and session-boundary next-open visibility; `tests/unit/runtime/test_market_data_flow.py` covers resampled bucket-end visibility; `tests/unit/strategy_sdk/test_data_view.py` blocks raw bar-store exposure. Fresh check: `21 passed`. | None for local automated no-lookahead gates. | Add broader strategy-level examples when new DataView APIs are introduced. |
| M1-3 backtest manifest completeness | Complete | `backend/src/qts/reporting/backtest.py` validates M1 manifest fields unconditionally; `backend/src/qts/backtest/engine.py` supplies dataset provenance aliases, topology hash, execution assumptions, and `risk_config_hash`; `tests/unit/backtest/test_report_metadata.py` includes negative validation tests for missing fields and a missing `execution_assumptions` block. Fresh check: `uv run pytest tests/unit/backtest/test_report_metadata.py tests/unit/backtest/test_backtest_streaming_sink.py -q` -> `12 passed`. | None for automated manifest validation. | Keep anchor contract updated when required manifest fields evolve. |
| M1-4 paper simulated CI smoke | Complete | `tests/integration/test_paper_runtime_full_chain.py` asserts the shared paper-simulated event chain and canonical envelope fields; `tests/integration/test_paper_runtime_flow.py` uses `RuntimeSession` with `FakeStreamingMarketDataAdapter` only in tests. Fresh check: `uv run pytest tests/integration/test_paper_runtime_full_chain.py tests/integration/test_paper_runtime_flow.py -q` -> `2 passed`. | None for CI smoke. | Keep `make guardrails` rejecting production imports of `qts.testing`. |
| M1-5 IBKR paper broker lifecycle drill | Complete for automated safety gates; real broker evidence remains environment-gated | `qts.application.commands.ibkr_paper_order_lifecycle_drill` rejects non-`DU...` accounts and non-`4002` order-execution ports; evidence includes order identity, restorable `BrokerOrderMap`, reconciliation, commission/idempotency flags, and manifest summary. `configs/paper.ibkr.example.yaml` now targets `4002`. Fresh check: `uv run pytest tests/unit/scripts/test_ibkr_paper_order_lifecycle_drill.py tests/integration/test_ibkr_gateway_order_lifecycle_anchor.py tests/anchor/test_ibkr_gateway_paper_readiness.py -q` -> `5 passed, 2 skipped`. | Real Gateway submit/cancel/tiny-fill evidence was not run locally; anchor skips without IBKR evidence options/environment. | Run broker-connected drill against IBKR paper Gateway and attach evidence before using this as external paper readiness proof. |

## Parallel Lanes

| Lane | Owner | Write Scope | M1 Tasks | First Output |
|---|---|---|---|---|
| A | Main session | `docs/plan/qts_runtime_readiness_m1_review_status_matrix.md` plus final integration edits | M1 coordination | This matrix and final evidence updates. |
| B | Agent | `tests/replay/`, `tests/unit/backtest/`, `backend/src/qts/backtest/`, `backend/src/qts/reporting/backtest.py` | M1-1, M1-3 | Gap report or focused red tests for deterministic artifacts and manifest completeness. |
| C | Agent | `tests/unit/data/`, `tests/unit/runtime/`, replay/data-view implementation files | M1-2 | Gap report or focused red tests for visibility and ordering contracts. |
| D | Agent | `tests/integration/test_paper_runtime*`, runtime smoke helpers, paper command tests | M1-4, M1-5 | Gap report or focused red tests for paper simulated smoke and IBKR paper drill safety. |

Agents are not allowed to add legacy wrappers, compatibility aliases, or historical-debt paths. If an existing compatibility path blocks the M1 gate, remove or tighten the canonical path instead of expanding compatibility.

## Required Verification Commands

Run narrow checks first:

```bash
uv run pytest tests/replay/test_backtest_determinism.py tests/replay/test_backtest_report_hash.py -q
uv run pytest tests/unit/data/test_replay_market_data_source.py tests/unit/runtime/test_market_data_flow.py -q
uv run pytest tests/unit/backtest/test_report_metadata.py tests/unit/backtest/test_backtest_streaming_sink.py -q
uv run pytest tests/integration/test_paper_runtime_full_chain.py tests/integration/test_paper_runtime_flow.py -q
uv run pytest tests/unit/scripts/test_ibkr_paper_order_lifecycle_drill.py tests/integration/test_ibkr_gateway_order_lifecycle_anchor.py tests/anchor/test_ibkr_gateway_paper_readiness.py -q
make guardrails
```

Run broader checks when M1 code changes land:

```bash
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
```

Do not claim M1 completion until fresh command output is recorded here.

## Verification Log

Fresh verification on 2026-05-16:

```bash
uv run pytest tests/replay/test_backtest_determinism.py tests/replay/test_backtest_report_hash.py -q
# 3 passed

uv run pytest tests/unit/data/test_replay_market_data_source.py tests/unit/runtime/test_market_data_flow.py tests/unit/strategy_sdk/test_data_view.py -q
# 21 passed

uv run pytest tests/unit/backtest/test_report_metadata.py tests/unit/backtest/test_backtest_streaming_sink.py -q
# 12 passed

uv run pytest tests/integration/test_paper_runtime_full_chain.py tests/integration/test_paper_runtime_flow.py -q
# 2 passed

uv run pytest tests/unit/scripts/test_ibkr_paper_order_lifecycle_drill.py tests/integration/test_ibkr_gateway_order_lifecycle_anchor.py tests/anchor/test_ibkr_gateway_paper_readiness.py -q
# 5 passed, 2 skipped

make guardrails
# Architecture guardrails passed.

make lint
# All checks passed.

make typecheck
# Success: no issues found in 466 source files.

make test-unit
# 688 passed

make test-integration
# 58 passed, 4 skipped

make test-anchor
# 39 passed, 1 skipped

make check
# format/lint/guardrails/typecheck/test-unit/test-integration/test-anchor passed
```

Skipped broker-connected tests require explicit IBKR paper Gateway evidence. This matrix closes automated M1 readiness gates, not real external broker evidence.
