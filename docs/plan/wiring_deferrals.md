# Production wiring deferrals

This document is the durable registry of production symbols that are
**knowingly accepted as unwired** by the
``qts.quality.rules.caller_presence.CallerPresenceRule`` guardrail.

## When to add an entry

Add a fully-qualified symbol to the code block below when one of the
following is true and ``make guardrails`` currently rejects the symbol:

1. **Documented deferral (target=OPT-NN)** — the wiring work belongs
   to a follow-up PR. The deferral must be removed in the same PR that
   adds the caller. **Maximum horizon: 3 months** from today.
2. **Library API (target=library)** — a public class exposed for
   external consumers (user notebooks / strategies). Maximum horizon:
   1 year.
3. **Framework integration (target=framework)** — fastapi /
   prometheus_client / pydantic / similar instantiates by reflection.
   Maximum horizon: 1 year.
4. **Module-internal helper (target=internal)** — public class whose
   only direct caller is a same-file helper function. Maximum horizon:
   1 year.

Items that **must not** appear here:

- ``Protocol`` subclasses (auto-detected — they should never reach the
  rule).
- ``StrEnum`` / ``IntEnum`` (auto-detected).
- Exception subclasses caught by type (auto-detected).
- Value objects referenced as return / attribute / parameter
  annotations in their defining module (auto-detected).
- Classes that ought to be deleted instead — see the deletion safety
  rules in CLAUDE.md §10.

## Format

Inside the fenced code block: one entry per line. Each entry has three
whitespace-separated tokens: ``<symbol>``, ``expires=<YYYY-MM-DD>``,
``target=<OPT-NN | library | framework | internal>``. Lines starting
with ``#`` and blank lines are ignored.

```
# wiring-followup (target=OPT-NN, 3-month horizon)
qts.research.optimizer.job.OptimizationJob  expires=2026-08-17  target=OPT-65
qts.research.optimizer.parameter_space.ParameterGrid  expires=2026-08-17  target=OPT-65
qts.research.optimizer.parameter_space.ParameterSpace  expires=2026-08-17  target=OPT-65
qts.research.optimizer.result.OptimizationResult  expires=2026-08-17  target=OPT-65
qts.research.optimizer.runner.OptimizationRunner  expires=2026-08-17  target=OPT-65
qts.application.strategy_lifecycle.StrategyRegistry  expires=2026-08-17  target=OPT-34
# framework integration (1-year horizon)
qts.api.schemas.common.RiskRuleSchema  expires=2027-05-17  target=framework
# library APIs (1-year horizon)
qts.data.market_data_pipeline.MarketDataPipeline  expires=2027-05-17  target=library
qts.runtime.durable_recovery.DurableAccountRecovery  expires=2027-05-17  target=library
# module-internal helpers (1-year horizon)
qts.application.commands.start_runtime.RuntimeStartResult  expires=2027-05-17  target=internal
qts.backtest.runner.BacktestRun  expires=2027-05-17  target=internal
qts.core.ids.RuntimeInstanceId  expires=2027-05-17  target=internal
qts.data.bars.aggregator.BarAggregator  expires=2027-05-17  target=internal
qts.data.sources.replay_market_data_source.ReplayClock  expires=2027-05-17  target=internal
qts.data.sources.replay_market_data_source.ReplayEventSequencer  expires=2027-05-17  target=internal
qts.observability.audit_sink.InMemoryAuditSink  expires=2027-05-17  target=internal
qts.quality.guardrails.PlatformFreezeConfig  expires=2027-05-17  target=internal
qts.reporting.backtest.StreamingEquityMetrics  expires=2027-05-17  target=internal
qts.runtime.durability.RuntimeDurabilityDrill  expires=2027-05-17  target=internal
qts.runtime.intent_processing.OrderPlanBuilder  expires=2027-05-17  target=internal
```

## Rationale for current entries

| Symbol | Category | Notes |
|---|---|---|
| `qts.api.schemas.common.RiskRuleSchema` | framework | Pydantic schema; fastapi instantiates via reflection during request validation. |
| `qts.application.commands.start_runtime.RuntimeStartResult` | internal | Application command result; consumed via DI through dynamic dispatch in tests / API layer. |
| `qts.application.strategy_lifecycle.StrategyRegistry` | OPT-34 | Planned hub for scheduler integration. |
| `qts.backtest.runner.BacktestRun` | internal | Application-layer DTO; same pattern as RuntimeStartResult. |
| `qts.core.ids.RuntimeInstanceId` | internal | StringId-style ID; passed as a string, rarely named directly. |
| `qts.data.bars.aggregator.BarAggregator` | internal | Public caller is `aggregate_bars` in the same file. |
| `qts.data.market_data_pipeline.MarketDataPipeline` | library | Library entry-point used by external research scripts. |
| `qts.data.sources.replay_market_data_source.ReplayClock` | internal | Used through `ReplayMarketDataSource` composition. |
| `qts.data.sources.replay_market_data_source.ReplayEventSequencer` | internal | Same pattern as ReplayClock. |
| `qts.observability.audit_sink.InMemoryAuditSink` | internal | Test/in-process sink; production deployments use `StderrJsonAuditSink`. |
| `qts.quality.guardrails.PlatformFreezeConfig` | internal | Consumed inside the guardrails module via dynamic AST walks. |
| `qts.reconciliation.persistent_drift.PersistentDriftKillSwitch` | OPT-63 | Runtime reconciliation integration (this batch). |
| `qts.reporting.backtest.StreamingEquityMetrics` | internal | Composed into `BacktestArtifactWriter`. |
| `qts.research.optimizer.*` (5) | OPT-65 | CLI driver + quickstart example (this batch). |
| `qts.runtime.durability.RuntimeDurabilityDrill` | internal | Durability drill harness; remains opt-in. |
| `qts.runtime.intent_processing.OrderPlanBuilder` | internal | Composed into `TargetIntentProcessor` in the same file. |
| `qts.runtime.state_recovery.DurableSnapshotStore` | OPT-64 | Cross-restart state recovery wiring (this batch). |
| `qts.runtime.state_recovery.SnapshotFrequencyPolicy` | OPT-64 | Same as DurableSnapshotStore. |

## How the rule reads this file

``qts.quality.rules.caller_presence._load_deferrals`` parses every
non-blank, non-comment line inside fenced code blocks. Each line must
match the format above; the rule rejects expired entries by emitting
``EXPIRED_DEFERRAL`` violations.
