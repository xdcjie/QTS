# QTS vs Lean P1 Module Health Review Status Matrix

Source backlog: `docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md`

Scope: P1 - Module health and breadth, OPT-04 through OPT-11.

Out of scope: P1 Frontend and DX items are tracked separately.

Baseline: 2026-05-17, `HEAD 2ac77a0`

## Completion Rules

P1 Module Health is complete only when OPT-04 through OPT-11 are closed with
hard evidence in this repository:

- module decomposition keeps ownership boundaries explicit and testable;
- new breadth features enter through current domain, SDK, runtime, risk, and
  execution boundaries;
- every new public concept has a first failing behavior, guardrail, anchor, or
  architecture test before production edits;
- durable docs, generated inventories, and platform-freeze exceptions are
  updated only for current canonical concepts;
- no legacy path, no compatibility alias, no compatibility wrapper, and no
  historical-debt branch may satisfy an acceptance condition.

## P1 Module Health Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Guardrail decomposition must preserve the same public verification contract. | `qts.quality` rule modules plus the `scripts/verify_guardrails.py` entrypoint. | Keeping a shadow monolith, compatibility registry, or duplicate rule path after the split. | `tests/unit/scripts/test_verify_guardrails.py`, `make guardrails`, and a no-legacy-import guard. |
| Runtime startup and topology decomposition must preserve fail-closed broker readiness semantics. | `BrokerRuntimeStartupChecklist`, runtime topology builder, startup gate, and broker lifecycle boundaries. | Moving broker/data/execution/capital/reconciliation checks into generic helpers that bypass startup decisions. | Focused startup/topology tests plus paper/live readiness integration gates. |
| Indicator breadth must be numerically anchored before registration. | `qts.indicators`, `IndicatorFactory`, and strategy SDK docs. | Adding approximations without reference fixtures or registering indicators before anchor tests exist. | One numerical anchor test per indicator plus SDK factory/docs tests. |
| Consolidators must preserve `[start, end)` bar visibility and exchange-time alignment. | `qts.data.bars` and runtime market-data coordination boundary. | Strategy-local resampling, backtest-only derived bars, or treating 1d as 24h clock bars. | Bar/session anchor tests and multi-timeframe replay equivalence tests. |
| Risk rules must be configured and ordered by a current rule registry. | `qts.risk.rules`, `RiskEngine`, and runtime config boundary. | Hardcoding one-off risk checks, bypassing `RiskEngine`, or adding mode-specific rule branches. | Rule rejection anchor tests, config loading tests, and order-flow integration tests. |
| Brokerage model facts stay at execution/broker boundaries. | `qts.execution` brokerage model, broker adapters, risk capability checks. | Leaking IBKR/product facts into shared runtime or strategy SDK code. | Fee/margin/capability tests plus adapter boundary guardrails. |
| Universe selection is a Strategy SDK contract, not a market-data shortcut. | `qts.strategy_sdk.universe`, `StrategyContext`, subscription planning, and market-data coordinator. | Letting strategies mutate subscriptions directly or using broker symbols as universe identities. | SDK universe tests, subscription delta tests, and `InstrumentId` guardrails. |

## Status Matrix

| Task | Status | Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| OPT-04 Split `quality/guardrails.py` | IN-PROGRESS / Gate planned | `backend/src/qts/quality/guardrails.py`, `scripts/verify_guardrails.py`, `tests/unit/scripts/test_verify_guardrails.py`. | Rule ownership modules and registry are not yet split; generated imports and docs still point at the monolith. | Add tests that require rules to live under `qts.quality.rules` while `run_guardrails` remains the only public script entrypoint. |
| OPT-05 Decompose `BrokerRuntimeStartupChecklist.from_config` | IN-PROGRESS / Gate planned | `backend/src/qts/runtime/broker_startup.py`, startup guard tests, readiness smoke tests. | Builder sections for data, execution, capital, and reconciliation are not yet explicit. | Add focused tests that each startup subsystem can fail independently and still aggregate into one fail-closed checklist. |
| OPT-06 Decompose `RuntimeTopologyBuilder.from_live_config` | IN-PROGRESS / Gate planned | `backend/src/qts/runtime/topology.py`, runtime topology tests, broker topology tests. | Broker topology assembly still lives in one method. | Add tests that require account, strategy, broker route, and market-data route assembly to be independently observable. |
| OPT-07 Add core indicators | IN-PROGRESS / Gate planned | `backend/src/qts/indicators/`, `backend/src/qts/strategy_sdk/indicators.py`, indicator docs. | Reference fixtures and SDK registration plan are missing for the industrial baseline. | Add one failing numerical anchor fixture for the first indicator group before implementation. |
| OPT-08 Introduce Consolidator primitive | IN-PROGRESS / Gate planned | `backend/src/qts/data/bars/`, `backend/src/qts/runtime/market_data_coordinator.py`, bar/session tests. | No consolidator protocol or multi-timeframe replay equivalence gate exists. | Add a 1m-to-5m fixture test proving `[start, end)` derived bars match the historical 5m fixture. |
| OPT-09 Pluginize risk rules and add standard 5 | IN-PROGRESS / Gate planned | `backend/src/qts/risk/rules/`, `backend/src/qts/risk/risk_engine.py`, risk config tests. | Rule registry, config ordering, and standard rule anchors are absent. | Add a config-ordering test that fails until `RiskEngine` loads declared rules through a registry. |
| OPT-10 Brokerage Model: fees, margin, capabilities matrix | IN-PROGRESS / Gate planned | `backend/src/qts/execution/adapters/`, proposed `qts.execution.brokerage_model`, broker capability tests. | Fee, margin, slippage, and capability facts are not unified behind a brokerage model. | Add a brokerage model test that computes a known fee/margin/capability decision without leaking broker facts outside execution boundaries. |
| OPT-11 Universe Selection framework | IN-PROGRESS / Gate planned | Proposed `backend/src/qts/strategy_sdk/universe.py`, `StrategyContext`, subscription planning, market-data coordinator. | Universe selector contract and subscription delta materialization are missing. | Add SDK tests for `ctx.set_universe(...)` and runtime tests for `InstrumentId` subscription delta materialization. |

## Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main session | This matrix, backlog links, cross-item integration, graph refresh, final verification. | Matrix and backlog stay aligned with actual P1 module-health status and fresh command output. |
| B | Main session | `qts.quality`, guardrail script tests, architecture docs. | OPT-04 lands without legacy rule import paths or duplicate registries. |
| C | Main session | runtime startup/topology boundaries and focused runtime tests. | OPT-05 and OPT-06 reduce method size while preserving fail-closed startup semantics. |
| D | Main session | indicators and consolidators plus anchor fixtures. | OPT-07 and OPT-08 add breadth only after reference fixtures prove numerical/bar semantics. |
| E | Main session | risk, brokerage, and universe SDK/runtime contracts. | OPT-09 through OPT-11 land through current boundaries without broker/runtime leakage into strategy code. |

## Verification Plan

Run the matrix gate first:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p1_module_health_review_status_matrix.py -q
```

Focused gates before production edits:

```bash
uv run pytest tests/unit/scripts/test_verify_guardrails.py -q
uv run pytest tests/unit/runtime/test_live_startup_guard.py tests/unit/runtime/test_runtime_topology.py -q
uv run pytest tests/unit/indicators -q
uv run pytest tests/unit/data/test_bar_aggregator.py tests/unit/data/test_bar_alignment.py tests/unit/data/test_timeframe.py -q
uv run pytest tests/unit/risk tests/unit/execution -q
uv run pytest tests/unit/strategy_sdk tests/unit/data/test_subscription_planning.py -q
make guardrails
```

Run broader gates as P1 code lands:

```bash
make format
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
```

Do not claim P1 Module Health completion until fresh command output is recorded
in this matrix and every OPT-04 through OPT-11 backlog row is updated to `DONE`.

## Verification Log

Initial matrix gate on 2026-05-17:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p1_module_health_review_status_matrix.py -q
# 2 failed as expected before this matrix existed and before OPT-04 through OPT-11 linked to it.
```

Matrix gate after writing the matrix and backlog links:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p1_module_health_review_status_matrix.py -q
# 2 passed

PYTHONPATH=backend/src uv run pytest tests/unit/docs/test_qts_vs_lean_p0_review_status_matrix.py tests/unit/docs/test_qts_vs_lean_p1_module_health_review_status_matrix.py -q
# 4 passed

make format
# 1 file reformatted, 526 files left unchanged

make lint
# All checks passed

make guardrails
# Architecture guardrails passed

make typecheck
# Success: no issues found in 504 source files

make test-unit
# 852 passed
```
