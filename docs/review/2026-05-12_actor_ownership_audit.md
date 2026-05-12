# 2026-05-12 — Actor Ownership Audit (OOP-07-T01)

## Scope
- Review target: runtime actor state ownership and cross-actor interactions.
- Files inspected: `backend/src/qts/runtime/actors/*`, `backend/src/qts/runtime/router.py`,
  `backend/src/qts/runtime/actor_ref.py`, `backend/src/qts/runtime/actor.py`,
  `backend/src/qts/backtest/actor_loop.py`.
- Goal: confirm actor state is locally owned and mutable actor state is changed only by actor message handling.

## Findings

### 1) Runtime actor state ownership
- `AccountActor` owns mutable runtime account state:
  - `self._cash`
  - `self._positions`
  - `self._fill_ids`
- Mutation path: only `AccountActor._apply_fill`, reached only from `AccountActor.handle` when receiving `ApplyFill`.
- There are no writes to `_cash`, `_positions`, or `_fill_ids` outside `AccountActor`.

- `OrderManagerActor` owns mutable order state:
  - `self._manager`
  - `self._fills`
- Mutation paths:
  - `OrderManagerActor._handle_submit`
  - `OrderManagerActor._handle_report`
- Ownership is intact: other modules use `SubmitOrder` messages or snapshot-style reads.

- `ExecutionActor` does not own mutable order state beyond `_order_manager_ref` and `_execution_adapter`.
- `MarketDataActor` owns message fan-out/subscription state:
  - `_logical_subscribers`
  - `_source_timeframe_by_logical`
  - `_physical_subscriptions`
  - `_aggregation_pipeline`
- Mutations occur only in `_subscribe`.

- `StrategyActor` owns strategy runtime state (`_strategy`, `_context`, `_result_ref`) and emits `StrategyBarResult` / `StrategyFinalized` as output messages.
- `SignalAggregatorActor` owns `_result_ref` and forwards `StrategySignalEvent`.

### 2) Cross-actor communication
- All runtime actors communicate by `ActorRef.tell(...)` or via actor-internal mailbox (`ActorRef.process_all` on refs created for orchestration).
- No direct business-method call patterns were found between actor classes for live-path behavior.
- Direct interactions stay limited to message types:
  - `SubmitOrder`
  - `ExecutionReport`
  - `ApplyFill`
  - `Strategy*` and `MarketData*` messages
  - internal `ActorRef` message relay

## Exceptions observed
- Backtest loop (`backend/src/qts/backtest/actor_loop.py` and `intent_processor.py`) operates actor instances in-process for synchronous orchestration:
  - direct reads like `account_actor.snapshot()`
  - read helpers/counters like `order_manager_actor.fill_count`
  - direct order lookups like `order_manager_actor.get_order(...)`
- This is intentional for testable backtest execution and not a runtime actor bus path.

## Acceptance check
- No direct cross-actor business method call was found in the live actor runtime path.
- Mutable runtime state ownership is consistent with actor boundaries.
