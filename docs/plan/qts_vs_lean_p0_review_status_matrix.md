# QTS vs Lean P0 Review Status Matrix

Source backlog: `docs/plan/2026-05-17_qts_vs_lean_platform_gap_and_optimization_backlog.md`

Scope: P0 - Strategy SDK ergonomics and hot-path correctness.

Baseline: 2026-05-17, `HEAD b8b0d43`

## Completion Rules

P0 is complete only when OPT-01, OPT-02, and OPT-03 are all closed with hard
evidence in this repository:

- Strategy SDK callbacks expose current typed domain contracts to strategy
  authors without `Any` in shipped example strategies.
- `RuntimeMarketDataCoordinator.on_market_data` is decomposed into named,
  independently tested stages without changing event ordering.
- `BacktestActorLoop.run` is decomposed into named, independently tested phases
  without changing warmup, trading, finalization, or artifact semantics.
- Each P0 item has a failing test or guardrail before production edits, then
  fresh passing focused checks recorded here.
- No legacy path, no compatibility alias, no compatibility wrapper, and no
  historical-debt branch may satisfy a P0 acceptance condition.

## P0 Correctness Invariants

| Invariant | Correct owner or boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Strategy authors see typed SDK data, while strategy code still emits intents only. | `qts.strategy_sdk.Strategy`, `StrategyContext`, domain market-data and order-event types. | Leaving callbacks as `object`, adding `Any`, or adding a compatibility protocol that hides current SDK types. | SDK signature tests, mypy over `examples/strategies/vwap_pullback.py`, and strategy API docs check. |
| Market-data dispatch preserves the current shared runtime chain and event ordering. | `RuntimeMarketDataCoordinator` stage methods and runtime event sink. | Creating a backtest-only dispatch path, a direct strategy call bypass, or a legacy monolith wrapper that remains the real owner. | Focused coordinator stage tests plus existing replay/paper integration gates. |
| Backtest loop decomposition preserves warmup, trading, risk/order/account/reporting behavior. | `BacktestActorLoop` phase methods and existing actor/runtime boundaries. | Moving business decisions into a helper outside the owning loop or bypassing RiskEngine/OrderManager/Execution/Account actors. | Backtest phase tests plus anchor/integration tests that cover shared runtime parity. |
| P0 status is reviewable from durable evidence, not verbal progress. | This matrix and source backlog item links. | Marking an item complete without a first red gate, verification log, or backlog status update. | `tests/unit/docs/test_qts_vs_lean_p0_review_status_matrix.py`. |

## Status Matrix

| Task | Status | Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| OPT-01 Strongly-type Strategy SDK callbacks | DONE / Focused gates passed | `qts.strategy_sdk.events` owns public `TimerEvent`, `OrderUpdate`, and `Fill`; `Strategy` callbacks use `StrategyContext`, `Bar`, `Tick`, and SDK events; VWAP example has no `Any`; `strategy_api.md` documents callback payloads. | None for focused SDK typing gates. | `test_strategy_callback_signatures_use_public_sdk_types` and `test_vwap_pullback_example_does_not_use_any` failed before the SDK event module and typed signatures existed. |
| OPT-02 Decompose `RuntimeMarketDataCoordinator.on_market_data` | IN-PROGRESS / Gate planned | `backend/src/qts/runtime/market_data_coordinator.py`, existing market-data flow tests, replay/paper integration tests. | Hot path is still monolithic; named stage boundaries and tests are not yet in place. | Add tests for normalize, route, derive-bar, and strategy-trigger stages that fail until stages exist. |
| OPT-03 Decompose `BacktestActorLoop.run` | IN-PROGRESS / Gate planned | `backend/src/qts/backtest/actor_loop.py`, backtest integration and anchor tests. | Loop phases are not yet explicit; phase-level tests are not yet in place. | Add tests that require warmup, trading, and finalize phase ownership before extracting production code. |

## Execution Lanes

| Lane | Owner | Write Scope | Exit Evidence |
| --- | --- | --- | --- |
| A | Main session | This matrix, backlog links, cross-item integration, graph refresh, final verification. | Matrix and backlog stay aligned with actual P0 status and fresh command output. |
| B | Main session | `qts.strategy_sdk`, VWAP example, SDK docs, focused SDK tests. | OPT-01 typed callbacks land without `Any` or compatibility aliases. |
| C | Main session | `qts.runtime.market_data_coordinator` and focused runtime tests. | OPT-02 stage boundaries are tested and existing integration gates stay green. |
| D | Main session | `qts.backtest.actor_loop` and focused backtest tests. | OPT-03 phases are tested and backtest/live parity gates stay green. |

## Verification Plan

Run red gates before each production edit, then focused green checks:

```bash
uv run pytest tests/unit/docs/test_qts_vs_lean_p0_review_status_matrix.py -q
uv run pytest tests/unit/strategy_sdk tests/unit/strategies/test_vwap_pullback.py -q
uv run mypy examples/strategies/vwap_pullback.py
uv run pytest tests/unit/runtime/test_market_data_flow.py tests/integration/test_paper_runtime_full_chain.py -q
uv run pytest tests/integration/test_backtest_runtime_flow.py tests/anchor -q
make guardrails
```

Run broader gates after P0 code changes:

```bash
make format
make lint
make typecheck
make test-unit
make test-integration
make test-anchor
```

Do not claim P0 completion until fresh command output is recorded in this
matrix and every P0 backlog row is updated to `DONE`.

## Verification Log

Initial matrix gate on 2026-05-17:

```bash
uv run pytest tests/unit/docs/test_qts_vs_lean_p0_review_status_matrix.py -q
# 2 failed as expected before this matrix existed and before P0 backlog rows linked to it.
```

Matrix gate after writing the matrix and backlog links:

```bash
uv run pytest tests/unit/docs/test_qts_vs_lean_p0_review_status_matrix.py -q
# 2 passed
```

OPT-01 focused gates on 2026-05-17:

```bash
PYTHONPATH=backend/src uv run pytest tests/unit/strategy_sdk/test_strategy_base.py tests/unit/strategy_sdk/test_strategy_events.py tests/unit/strategies/test_vwap_pullback.py -q
# 14 passed

PYTHONPATH=backend/src uv run mypy examples/strategies/vwap_pullback.py
# Success: no issues found in 1 source file

PYTHONPATH=backend/src uv run pytest tests/unit/strategy_sdk/test_strategy_base.py tests/unit/strategy_sdk/test_strategy_events.py tests/unit/strategies/test_vwap_pullback.py tests/unit/docs/test_qts_vs_lean_p0_review_status_matrix.py -q
# 16 passed

make format
# 1 file reformatted, 525 files left unchanged

make lint
# All checks passed

make guardrails
# Architecture guardrails passed

make typecheck
# Success: no issues found in 503 source files

make test-unit
# 849 passed

make test-integration
# 78 passed, 4 skipped
```
