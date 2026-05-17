# Production wiring deferrals

This document is the durable registry of production symbols that are
**knowingly accepted as unwired** by the
``qts.quality.rules.caller_presence.CallerPresenceRule`` guardrail.

## When to add an entry

Add a fully-qualified symbol to the code block below when one of the
following is true and ``make guardrails`` currently rejects the symbol:

1. **Documented deferral** — the wiring work belongs to a follow-up PR
   and the source backlog entry has been flipped to
   ``IN-PROGRESS / wiring deferred`` with an explicit successor commit
   target. The deferral should be removed in the same PR that adds the
   caller.
2. **Library API meant for external consumers** — a public class
   exported under e.g. ``qts.research.optimizer`` that is exercised by
   user notebooks / external scripts rather than QTS-internal code.
   These remain deferred indefinitely or until an in-repo example
   strategy / script provides a wiring example.
3. **Framework integration point** — a class that fastapi /
   prometheus_client / pydantic / similar instantiates via reflection
   and never explicitly imports by name.
4. **Module-internal helper exported via a thin wrapper** — a class
   whose only caller is a module-level helper function in the same file
   (e.g. ``BarAggregator`` consumed by ``aggregate_bars``); the helper
   is the public surface, the class is the implementation.

Items that **must not** appear here:

- ``Protocol`` subclasses (auto-detected — they should never reach the
  rule).
- ``StrEnum`` / ``IntEnum`` (auto-detected).
- Exception subclasses caught by type (auto-detected).
- Value objects returned from another class's methods in the same file
  (auto-detected — the owner type is the wiring signal).
- Classes that ought to be deleted instead — see the deletion safety
  rules in CLAUDE.md before adding an entry that could be removed.

## Format

Inside the code block: one fully-qualified symbol per line,
``qts.module.submodule.ClassName``. Comments and blank lines are ignored.

```
qts.api.schemas.common.RiskRuleSchema
qts.application.commands.start_runtime.RuntimeStartResult
qts.application.strategy_lifecycle.StrategyRegistry
qts.backtest.runner.BacktestRun
qts.core.ids.RuntimeInstanceId
qts.data.bars.aggregator.BarAggregator
qts.data.market_data_pipeline.MarketDataPipeline
qts.data.sources.replay_market_data_source.ReplayClock
qts.data.sources.replay_market_data_source.ReplayEventSequencer
qts.observability.audit_sink.InMemoryAuditSink
qts.quality.guardrails.PlatformFreezeConfig
qts.reconciliation.persistent_drift.PersistentDriftKillSwitch
qts.reporting.backtest.StreamingEquityMetrics
qts.research.optimizer.job.OptimizationJob
qts.research.optimizer.parameter_space.ParameterGrid
qts.research.optimizer.parameter_space.ParameterSpace
qts.research.optimizer.result.OptimizationResult
qts.research.optimizer.runner.OptimizationRunner
qts.runtime.durability.RuntimeDurabilityDrill
qts.runtime.intent_processing.OrderPlanBuilder
qts.runtime.state_recovery.DurableSnapshotStore
qts.runtime.state_recovery.SnapshotFrequencyPolicy
```

## Rationale for current entries

| Symbol | Category | Notes |
|---|---|---|
| `qts.api.schemas.common.RiskRuleSchema` | framework integration | Pydantic schema; fastapi instantiates via reflection during request validation. |
| `qts.application.commands.start_runtime.RuntimeStartResult` | DI value object | Application command result; consumed via DI through dynamic dispatch in tests / API layer. |
| `qts.application.strategy_lifecycle.StrategyRegistry` | wiring follow-up | StrategyRegistry is the planned hub for OPT-34 scheduler integration; not yet wired into the runtime. |
| `qts.backtest.runner.BacktestRun` | DI value object | Application-layer DTO; same pattern as RuntimeStartResult. |
| `qts.core.ids.RuntimeInstanceId` | newtype | StringId-style ID; passed as a string, rarely named directly. |
| `qts.data.bars.aggregator.BarAggregator` | module-internal helper | Public caller is `aggregate_bars` in the same file; BarAggregator is the implementation. |
| `qts.data.market_data_pipeline.MarketDataPipeline` | library API | Library entry-point used by external research scripts; no in-repo caller yet. |
| `qts.data.sources.replay_market_data_source.ReplayClock` | replay internals | Used through `ReplayMarketDataSource` composition; no direct external caller. |
| `qts.data.sources.replay_market_data_source.ReplayEventSequencer` | replay internals | Same pattern as ReplayClock. |
| `qts.observability.audit_sink.InMemoryAuditSink` | test helper | Documented test/in-process sink; production deployments use `StderrJsonAuditSink`. |
| `qts.quality.guardrails.PlatformFreezeConfig` | guardrails internals | Consumed inside the guardrails module via dynamic AST walks. |
| `qts.reconciliation.persistent_drift.PersistentDriftKillSwitch` | wiring follow-up | OPT-47 shipped the class and anchors; runtime integration is the next slice. |
| `qts.reporting.backtest.StreamingEquityMetrics` | reporting internal | Composed into `BacktestArtifactWriter`; never directly instantiated by external code. |
| `qts.research.optimizer.*` (5) | library API | OPT-19 first slice; external CLI / notebook driver pending. |
| `qts.runtime.durability.RuntimeDurabilityDrill` | wiring follow-up | Durability drill harness; CLI wrapper pending. |
| `qts.runtime.intent_processing.OrderPlanBuilder` | module-internal helper | Composed into `TargetIntentProcessor` in the same file. |
| `qts.runtime.state_recovery.DurableSnapshotStore` | wiring follow-up | Production durable store; only FileSnapshotStore / InMemorySnapshotStore have current callers. |
| `qts.runtime.state_recovery.SnapshotFrequencyPolicy` | wiring follow-up | Same as DurableSnapshotStore. |

## How the rule reads this file

``qts.quality.rules.caller_presence._load_deferrals`` parses every
non-blank line inside fenced code blocks as a fully-qualified symbol.
The single code block above is the canonical source.
