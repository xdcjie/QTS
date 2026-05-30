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
qts.application.strategy_lifecycle.StrategyRegistry  expires=2026-08-17  target=OPT-34
# framework integration (1-year horizon)
qts.api.schemas.common.RiskRuleSchema  expires=2027-05-17  target=framework
# library APIs (1-year horizon)
qts.data.market_data_pipeline.MarketDataPipeline  expires=2027-05-17  target=library
qts.runtime.durable_recovery.DurableAccountRecovery  expires=2027-05-17  target=library
# module-internal helpers (1-year horizon)
qts.application.commands.start_runtime.RuntimeStartResult  expires=2027-05-17  target=internal
qts.backtest.actor_loop.PendingFill  expires=2027-05-30  target=internal
qts.backtest.runner.BacktestRun  expires=2027-05-17  target=internal
qts.core.ids.RuntimeInstanceId  expires=2027-05-17  target=internal
qts.data.bars.aggregator.BarAggregator  expires=2027-05-17  target=internal
qts.data.sources.replay_market_data_source.ReplayClock  expires=2027-05-17  target=internal
qts.data.sources.replay_market_data_source.ReplayEventSequencer  expires=2027-05-17  target=internal
qts.observability.audit_sink.InMemoryAuditSink  expires=2027-05-17  target=internal
qts.quality.guardrails.PlatformFreezeConfig  expires=2027-05-17  target=internal
qts.research.factor_discovery.UrllibFactorDiscoveryHttpClient  expires=2027-05-25  target=internal
qts.reporting.backtest.StreamingEquityMetrics  expires=2027-05-17  target=internal
qts.runtime.durability.RuntimeDurabilityDrill  expires=2027-05-17  target=internal
qts.runtime.intent_processing.OrderPlanBuilder  expires=2027-05-17  target=internal
# --- C5a batch: surfaced when the caller-presence gate stopped counting bare
# re-exports. Owner-used helpers auto-pass; these have no caller yet. ---
# SDK exports for user strategies (library, 1-year horizon)
qts.strategy_sdk.portfolio_construction.EqualWeightSignalPortfolioConstruction  expires=2027-05-30  target=library
qts.strategy_sdk.portfolio_construction.ConfidenceWeightedSignalPortfolioConstruction  expires=2027-05-30  target=library
qts.strategy_sdk.portfolio_construction.MagnitudeWeightedSignalPortfolioConstruction  expires=2027-05-30  target=library
qts.strategy_sdk.portfolio_construction.RiskParitySignalPortfolioConstruction  expires=2027-05-30  target=library
qts.strategy_sdk.portfolio_construction.HorizonAwareSignalPortfolioConstruction  expires=2027-05-30  target=library
qts.strategy_sdk.portfolio_construction.VolatilityTargetedSignalPortfolioConstruction  expires=2027-05-30  target=library
qts.strategy_sdk.universe.FundamentalTopNSelector  expires=2027-05-30  target=library
qts.strategy_sdk.universe.TopNVolumeSelector  expires=2027-05-30  target=library
# Live/paper/research subsystems pending their roadmap milestone wiring
# (M8 paper, M10 live, research deploy). OPT-65 batch; 3-month review fuse.
qts.application.services.promotion_runtime_config.PromotionRuntimeConfigBuilder  expires=2026-08-30  target=OPT-65
qts.data.feeds.replay_feed.ReplayFeed  expires=2026-08-30  target=OPT-65
qts.data.historical.adapter.HistoricalMarketDataAdapter  expires=2026-08-30  target=OPT-65
qts.data.live.reconnect.ReconnectPolicy  expires=2026-08-30  target=OPT-65
qts.data.sources.replay_market_data_source.SubscriptionReplayMarketDataSource  expires=2026-08-30  target=OPT-65
qts.data.stores.memory_store.InMemoryMarketDataStore  expires=2026-08-30  target=OPT-65
qts.data.stores.parquet_store.ParquetMarketDataStore  expires=2026-08-30  target=OPT-65
qts.data.transports.ib_async_market_data_transport.IbAsyncMarketDataTransport  expires=2026-08-30  target=OPT-65
qts.execution.adapters.broker_execution_adapter.BrokerExecutionAdapter  expires=2026-08-30  target=OPT-65
qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter  expires=2026-08-30  target=OPT-65
qts.execution.transports.ib_async_order_execution_transport.IbAsyncOrderExecutionTransport  expires=2026-08-30  target=OPT-65
qts.indicators.session_regime.SessionRegimeGateConfig  expires=2026-08-30  target=OPT-65
qts.indicators.session_regime.TrailingSessionRegimeGate  expires=2026-08-30  target=OPT-65
qts.observability.dashboard.OperationalDashboardSnapshot  expires=2026-08-30  target=OPT-65
qts.observability.errors.RuntimeErrorReason  expires=2026-08-30  target=OPT-65
qts.registry.back_adjusted_series.BackAdjustedContinuousSeriesBuilder  expires=2026-08-30  target=OPT-65
qts.registry.calendar_registry.CalendarRegistry  expires=2026-08-30  target=OPT-65
qts.registry.future_chain_registry.FutureChainRegistry  expires=2026-08-30  target=OPT-65
qts.registry.future_roll.HighestVolumeFutureContractSelector  expires=2026-08-30  target=OPT-65
qts.registry.option_chain_registry.OptionChainRegistry  expires=2026-08-30  target=OPT-65
qts.reporting.backtest.BacktestReportWriter  expires=2026-08-30  target=OPT-65
qts.reporting.broker_runtime.BrokerRuntimeEventReporter  expires=2026-08-30  target=OPT-65
qts.reporting.broker_runtime.BrokerRuntimeReportWriter  expires=2026-08-30  target=OPT-65
qts.research.readiness.PaperLiveReadinessDecision  expires=2026-08-30  target=OPT-65
qts.research.trade_diagnostics.PaperCandidateDiagnosticsGate  expires=2026-08-30  target=OPT-65
qts.research.validation.NoLookaheadArtifactWriter  expires=2026-08-30  target=OPT-65
qts.risk.rules.trading_session_rule.TradingSessionRule  expires=2026-08-30  target=OPT-65
qts.runtime.config.models.ConfigMigration  expires=2026-08-30  target=OPT-65
qts.runtime.config.models.TradingRuntimeConfig  expires=2026-08-30  target=OPT-65
qts.runtime.config.paper.PaperSimulatedRuntimeConfig  expires=2026-08-30  target=OPT-65
qts.runtime.partitioning.AccountBrokerMapping  expires=2026-08-30  target=OPT-65
qts.runtime.partitioning.AccountPartitionPolicy  expires=2026-08-30  target=OPT-65
qts.runtime.partitioning.AccountRiskConfig  expires=2026-08-30  target=OPT-65
qts.runtime.router.EventRouter  expires=2026-08-30  target=OPT-65
qts.runtime.state_recovery.InMemorySnapshotStore  expires=2026-08-30  target=OPT-65
```

## Rationale for current entries

| Symbol | Category | Notes |
|---|---|---|
| `qts.api.schemas.common.RiskRuleSchema` | framework | Pydantic schema; fastapi instantiates via reflection during request validation. |
| `qts.application.commands.start_runtime.RuntimeStartResult` | internal | Application command result; consumed via DI through dynamic dispatch in tests / API layer. |
| `qts.application.strategy_lifecycle.StrategyRegistry` | OPT-34 | Planned hub for scheduler integration. |
| `qts.backtest.actor_loop.PendingFill` | internal | Next-bar-open deferred-fill record; only caller is `defer_strategy_intent`/`flush_pending_fills` in the same backtest actor loop. |
| `qts.backtest.runner.BacktestRun` | internal | Application-layer DTO; same pattern as RuntimeStartResult. |
| `qts.core.ids.RuntimeInstanceId` | internal | StringId-style ID; passed as a string, rarely named directly. |
| `qts.data.bars.aggregator.BarAggregator` | internal | Public caller is `aggregate_bars` in the same file. |
| `qts.data.market_data_pipeline.MarketDataPipeline` | library | Library entry-point used by external research scripts. |
| `qts.data.sources.replay_market_data_source.ReplayClock` | internal | Used through `ReplayMarketDataSource` composition. |
| `qts.data.sources.replay_market_data_source.ReplayEventSequencer` | internal | Same pattern as ReplayClock. |
| `qts.observability.audit_sink.InMemoryAuditSink` | internal | Test/in-process sink; production deployments use `StderrJsonAuditSink`. |
| `qts.quality.guardrails.PlatformFreezeConfig` | internal | Consumed inside the guardrails module via dynamic AST walks. |
| `qts.research.factor_discovery.UrllibFactorDiscoveryHttpClient` | internal | Default HTTP implementation composed by factor discovery source classes in the same module. |
| `qts.reconciliation.persistent_drift.PersistentDriftKillSwitch` | OPT-63 | Runtime reconciliation integration (this batch). |
| `qts.reporting.backtest.StreamingEquityMetrics` | internal | Composed into `BacktestArtifactWriter`. |
| `qts.runtime.durability.RuntimeDurabilityDrill` | internal | Durability drill harness; remains opt-in. |
| `qts.runtime.intent_processing.OrderPlanBuilder` | internal | Composed into `TargetIntentProcessor` in the same file. |
| `qts.runtime.state_recovery.DurableSnapshotStore` | OPT-64 | Cross-restart state recovery wiring (this batch). |
| `qts.runtime.state_recovery.SnapshotFrequencyPolicy` | OPT-64 | Same as DurableSnapshotStore. |

### C5a batch (surfaced by the re-export-aware caller gate)

When the caller-presence gate stopped counting bare re-exports as callers
(and started counting same-module owner-use), 43 baseline symbols with no real
caller surfaced. They fall into two groups:

- **`library` (8)** — Strategy SDK portfolio-construction and universe-selector
  classes exposed for user strategies. Wired by an example strategy; 1-year
  horizon.
- **`OPT-65` (35)** — real, test-exercised components of the live/paper/research
  subsystems that are not yet driven by a production entrypoint (IBKR/replay
  market-data + execution transports and adapters, runtime router/partitioning/
  snapshot/config scaffolding, registry chain/calendar/roll/back-adjustment
  capabilities, broker/backtest report writers, research readiness/diagnostics/
  no-lookahead writers, the session/observability/risk gates). The wiring is
  blocked on the roadmap milestones (M8 paper, M10 live, research deploy); the
  3-month fuse forces a conscious re-defer-or-wire at each review rather than
  letting the debt hide.

## How the rule reads this file

``qts.quality.rules.caller_presence._load_deferrals`` parses every
non-blank, non-comment line inside fenced code blocks. Each line must
match the format above; the rule rejects expired entries by emitting
``EXPIRED_DEFERRAL`` violations.
