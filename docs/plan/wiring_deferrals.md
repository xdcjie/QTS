# Non-production wiring deferrals

This document is the durable registry of non-production caller-presence
deferrals accepted by the
``qts.quality.rules.caller_presence.CallerPresenceRule`` guardrail. Final-state
architecture allows no ``target=production`` deferrals: production symbols must
have a real non-test caller or fail the guardrail.

## When to add an entry

Add a fully-qualified symbol to the code block below when one of the
following non-production cases is true and ``make guardrails`` currently
rejects the symbol:

1. **Library API (target=library)** — a public class exposed for
   external consumers (user notebooks / strategies). Maximum horizon:
   1 year.
2. **Framework integration (target=framework)** — fastapi /
   prometheus_client / pydantic / similar instantiates by reflection.
   Maximum horizon: 1 year.
3. **Module-internal helper (target=internal)** — public class whose
   only direct caller is a same-file helper function. Maximum horizon:
   1 year.
4. **Subsystem component (target=subsystem)** — a component kept as an
   implementation detail behind a package/subsystem owner and not part of the
   operator-facing production launch surface. Maximum horizon: 1 year.

Items that **must not** appear here:

- ``Protocol`` subclasses (auto-detected — they should never reach the
  rule).
- ``StrEnum`` / ``IntEnum`` (auto-detected).
- Exception subclasses caught by type (auto-detected).
- Value objects referenced as return / attribute / parameter
  annotations in their defining module (auto-detected).
- Production symbols. Final-state architecture requires a real caller.
- Classes that ought to be deleted instead — see the deletion safety
  rules in CLAUDE.md §10.

## Format

Inside the fenced code block: one entry per line. Each entry has three
whitespace-separated tokens: ``<symbol>``, ``expires=<YYYY-MM-DD>``,
``target=<library | framework | internal | subsystem>``. Lines starting
with ``#`` and blank lines are ignored.

```
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
# Subsystem components (not production launch surface, 1-year horizon)
qts.application.services.promotion_runtime_config.PromotionRuntimeConfigBuilder  expires=2027-05-30  target=subsystem
qts.data.feeds.replay_feed.ReplayFeed  expires=2027-05-30  target=subsystem
qts.data.historical.adapter.HistoricalMarketDataAdapter  expires=2027-05-30  target=subsystem
qts.data.live.reconnect.ReconnectPolicy  expires=2027-05-30  target=subsystem
qts.data.sources.replay_market_data_source.SubscriptionReplayMarketDataSource  expires=2027-05-30  target=subsystem
qts.data.stores.memory_store.InMemoryMarketDataStore  expires=2027-05-30  target=subsystem
qts.data.stores.parquet_store.ParquetMarketDataStore  expires=2027-05-30  target=subsystem
qts.execution.adapters.broker_execution_adapter.BrokerExecutionAdapter  expires=2027-05-30  target=subsystem
qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter  expires=2027-05-30  target=subsystem
qts.indicators.session_regime.SessionRegimeGateConfig  expires=2027-05-30  target=subsystem
qts.indicators.session_regime.TrailingSessionRegimeGate  expires=2027-05-30  target=subsystem
qts.observability.dashboard.OperationalDashboardSnapshot  expires=2027-05-30  target=subsystem
qts.observability.errors.RuntimeErrorReason  expires=2027-05-30  target=subsystem
qts.registry.back_adjusted_series.BackAdjustedContinuousSeriesBuilder  expires=2027-05-30  target=subsystem
qts.registry.calendar_registry.CalendarRegistry  expires=2027-05-30  target=subsystem
qts.registry.future_chain_registry.FutureChainRegistry  expires=2027-05-30  target=subsystem
qts.registry.future_roll.HighestVolumeFutureContractSelector  expires=2027-05-30  target=subsystem
qts.registry.option_chain_registry.OptionChainRegistry  expires=2027-05-30  target=subsystem
qts.reporting.backtest.BacktestReportWriter  expires=2027-05-30  target=subsystem
qts.reporting.broker_runtime.BrokerRuntimeEventReporter  expires=2027-05-30  target=subsystem
qts.reporting.broker_runtime.BrokerRuntimeReportWriter  expires=2027-05-30  target=subsystem
qts.research.readiness.PaperLiveReadinessDecision  expires=2027-05-30  target=subsystem
qts.research.trade_diagnostics.PaperCandidateDiagnosticsGate  expires=2027-05-30  target=subsystem
qts.risk.rules.trading_session_rule.TradingSessionRule  expires=2027-05-30  target=subsystem
qts.runtime.config.models.ConfigMigration  expires=2027-05-30  target=subsystem
qts.runtime.config.models.TradingRuntimeConfig  expires=2027-05-30  target=subsystem
qts.runtime.config.paper.PaperSimulatedRuntimeConfig  expires=2027-05-30  target=subsystem
qts.runtime.partitioning.AccountBrokerMapping  expires=2027-05-30  target=subsystem
qts.runtime.partitioning.AccountPartitionPolicy  expires=2027-05-30  target=subsystem
qts.runtime.partitioning.AccountRiskConfig  expires=2027-05-30  target=subsystem
qts.runtime.router.EventRouter  expires=2027-05-30  target=subsystem
qts.runtime.state_recovery.InMemorySnapshotStore  expires=2027-05-30  target=subsystem
```

## Rationale for current entries

| Symbol | Category | Notes |
|---|---|---|
| `qts.api.schemas.common.RiskRuleSchema` | framework | Pydantic schema; fastapi instantiates via reflection during request validation. |
| `qts.application.commands.start_runtime.RuntimeStartResult` | internal | Application command result; consumed via DI through dynamic dispatch in tests / API layer. |
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
| `qts.reporting.backtest.StreamingEquityMetrics` | internal | Composed into `BacktestArtifactWriter`. |
| `qts.runtime.durability.RuntimeDurabilityDrill` | internal | Durability drill harness; remains opt-in. |
| `qts.runtime.intent_processing.OrderPlanBuilder` | internal | Composed into `TargetIntentProcessor` in the same file. |
| `qts.runtime.durable_recovery.DurableAccountRecovery` | library | Library entry-point for cross-restart account recovery; consumed by external recovery scripts. |

### C5a batch (surfaced by the re-export-aware caller gate)

When the caller-presence gate stopped counting bare re-exports as callers
(and started counting same-module owner-use), SDK-facing baseline symbols with
no real internal caller surfaced:

- **`library` (8)** — Strategy SDK portfolio-construction and universe-selector
  classes exposed for user strategies. Wired by an example strategy; 1-year
  horizon.
- **`subsystem` (32)** — components kept behind subsystem owners rather than
  directly exposed as operator-facing production launch entrypoints. These
  entries are not production wiring exceptions; `target=production` remains
  forbidden by `CallerPresenceRule` and final-readiness.

## Subsystem deferral decisions

Every `target=subsystem` entry above must have an explicit final-state decision
and owner-use proof. The decision values are:

- `keep-owned`: retained as a non-operator-facing implementation detail with a
  concrete owner and tests/docs.
- `wire-entrypoint`: retained because a runtime/research/reporting entrypoint
  already consumes it or must consume it.
- `move-experimental`: retained outside production launch wiring.
- `delete`: scheduled for deletion when the entry is no longer present in the
  code block.

| Symbol | Decision | Owner | Owner-use evidence |
|---|---|---|---|
| `qts.application.services.promotion_runtime_config.PromotionRuntimeConfigBuilder` | wire-entrypoint | Promotion runtime config builder | `PromotionRuntimeConfigBuilder.paper_start_command(...)` materializes `RuntimeLaunchPlan` and is covered by `tests/integration/test_promotion_to_paper_runtime_config.py`. |
| `qts.data.feeds.replay_feed.ReplayFeed` | keep-owned | Replay data source stack | Store-backed replay library API covered by `tests/unit/data/test_market_data_store.py`; canonical flow documented in `docs/architecture/replay_data_flow.md`. |
| `qts.data.historical.adapter.HistoricalMarketDataAdapter` | keep-owned | Historical data adapter boundary | Historical source adaptation boundary retained in `docs/architecture/replay_data_flow.md` and `docs/architecture/runtime_flow.md`. |
| `qts.data.live.reconnect.ReconnectPolicy` | keep-owned | Live data reconnect policy | Live reconnect policy is a data-live boundary object, not an operator launch entrypoint. |
| `qts.data.sources.replay_market_data_source.SubscriptionReplayMarketDataSource` | wire-entrypoint | Replay market-data source stack | Subscription replay source is the actor-facing replay source in `docs/architecture/replay_data_flow.md`. |
| `qts.data.stores.memory_store.InMemoryMarketDataStore` | keep-owned | Market-data store boundary | In-memory store backs replay/feed tests and local deterministic replay. |
| `qts.data.stores.parquet_store.ParquetMarketDataStore` | keep-owned | Market-data store boundary | Parquet store is the persisted market-data library API recorded by `docs/decision/2026-05-10_research_storage_decision.md`. |
| `qts.execution.adapters.broker_execution_adapter.BrokerExecutionAdapter` | keep-owned | Generic broker execution adapter facade | Retained as execution-layer protocol/facade; architecture coverage in `tests/unit/architecture/test_runtime_file_layout.py`. |
| `qts.execution.adapters.ibkr_order_execution.IbkrOrderExecutionAdapter` | wire-entrypoint | Canonical IBKR order-execution adapter | Production adapter path documented in `docs/architecture/broker_adapters.md`; covered by IBKR order execution tests. |
| `qts.indicators.session_regime.SessionRegimeGateConfig` | keep-owned | Session regime indicator boundary | Production strategy regime gate config, retained with strategy tests under `tests/unit/strategies`. |
| `qts.indicators.session_regime.TrailingSessionRegimeGate` | keep-owned | Session regime indicator boundary | Production strategy regime gate, retained with strategy tests under `tests/unit/strategies`. |
| `qts.observability.dashboard.OperationalDashboardSnapshot` | keep-owned | Observability dashboard boundary | Operator dashboard DTO/evidence object retained by observability package. |
| `qts.observability.errors.RuntimeErrorReason` | keep-owned | Observability error taxonomy | Runtime error reason value object retained by observability package. |
| `qts.registry.back_adjusted_series.BackAdjustedContinuousSeriesBuilder` | keep-owned | Registry continuous futures analytics | Registry-owned continuous futures series utility; not a runtime launch shortcut. |
| `qts.registry.calendar_registry.CalendarRegistry` | keep-owned | Registry calendar service | Registry-owned calendar lookup boundary required by domain calendar/session rules. |
| `qts.registry.future_chain_registry.FutureChainRegistry` | keep-owned | Registry futures chain service | Registry-owned futures chain lookup boundary required by roll/economics rules. |
| `qts.registry.future_roll.HighestVolumeFutureContractSelector` | keep-owned | Registry futures roll service | Alternate roll selector retained under registry ownership, not data-source-specific code. |
| `qts.registry.option_chain_registry.OptionChainRegistry` | keep-owned | Registry option chain service | Registry-owned option chain lookup boundary for option instruments. |
| `qts.reporting.backtest.BacktestReportWriter` | keep-owned | Backtest reporting boundary | Human report writer over machine artifact writer; documented in `docs/architecture/reporting_boundary.md`. |
| `qts.reporting.broker_runtime.BrokerRuntimeEventReporter` | keep-owned | Broker runtime reporting boundary | Broker event report owner documented in `docs/architecture/reporting_boundary.md`. |
| `qts.reporting.broker_runtime.BrokerRuntimeReportWriter` | keep-owned | Broker runtime reporting boundary | Broker runtime manifest/report writer covered by `tests/unit/reporting/test_reporting_contracts.py`. |
| `qts.research.readiness.PaperLiveReadinessDecision` | keep-owned | Research readiness evidence boundary | Research readiness verdict object, not a runtime start path. |
| `qts.research.trade_diagnostics.PaperCandidateDiagnosticsGate` | keep-owned | Research trade diagnostics boundary | Paper candidate diagnostics gate retained as research evidence validation. |
| `qts.risk.rules.trading_session_rule.TradingSessionRule` | keep-owned | Risk rule boundary | Trading-session risk rule retained under `qts.risk`, not strategy/runtime code. |
| `qts.runtime.config.models.ConfigMigration` | wire-entrypoint | Runtime config migration boundary | Runtime config migration is retained with `TradingRuntimeConfig` compatibility and runtime config tests. |
| `qts.runtime.config.models.TradingRuntimeConfig` | wire-entrypoint | Runtime config model boundary | Runtime config model is consumed by launch-plan/runtime config assembly and retained for compatibility. |
| `qts.runtime.config.paper.PaperSimulatedRuntimeConfig` | wire-entrypoint | Paper simulated runtime config boundary | Paper simulated config is retained for paper launch compatibility. |
| `qts.runtime.partitioning.AccountBrokerMapping` | keep-owned | Runtime partitioning boundary | Multi-account/multi-broker partition config retained by runtime topology. |
| `qts.runtime.partitioning.AccountPartitionPolicy` | keep-owned | Runtime partitioning boundary | Account partition policy retained by runtime topology. |
| `qts.runtime.partitioning.AccountRiskConfig` | keep-owned | Runtime partitioning boundary | Account risk config retained by runtime topology. |
| `qts.runtime.router.EventRouter` | keep-owned | Runtime router boundary | Runtime event router retained as actor/message routing boundary. |
| `qts.runtime.state_recovery.InMemorySnapshotStore` | keep-owned | Runtime recovery boundary | In-memory snapshot store retained for local recovery tests and drills. |

## How the rule reads this file

``qts.quality.rules.caller_presence._load_deferrals`` parses every
non-blank, non-comment line inside fenced code blocks. Each line must
match the format above; the rule rejects expired entries by emitting
``EXPIRED_DEFERRAL`` violations.
