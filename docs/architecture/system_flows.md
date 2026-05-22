# System Flow Catalog

This catalog is the durable owner for flow-first implementation rules. Before
changing non-trivial behavior, choose the applicable Flow ID and verify that the
entrypoint, config owner, implementation owner, iteration point, future-data
risk, and verification gate are explicit.

Flow rules do not replace module boundaries. They bind module boundaries to the
user-facing path that exercises them.

## Flow IDs

| Flow ID | Purpose |
| --- | --- |
| `FLOW-DATA` | Ingest, validate, resolve, replay, aggregate, and fan out market data. |
| `FLOW-RESEARCH` | Produce research evidence, factor ideas, factor evaluations, and research reports without trading side effects. |
| `FLOW-OPTIMIZER` | Sweep parameters and validate optimizer candidates through completed backtest manifests. |
| `FLOW-BACKTEST` | Execute strategies against replayed historical data through the shared trading path. |
| `FLOW-PAPER` | Execute promoted strategies in paper/simulated broker modes through broker-capable runtime boundaries. |
| `FLOW-LIVE` | Execute or observe promoted strategies against live broker/data-source adapters. |
| `FLOW-PROMOTION` | Move reviewed research/backtest/paper evidence into an approved paper or live runtime configuration. |
| `FLOW-REPORTING` | Read completed artifacts and emit deterministic reports, manifests, and operator evidence. |

## Common Rules

- Every flow must preserve `InstrumentId` inside core runtime/domain logic.
- Every trading flow must preserve the shared Strategy SDK -> RiskEngine ->
  OrderManagerActor -> ExecutionActor -> AccountActor path.
- Research, optimizer, and reporting artifacts are evidence. They do not create
  paper/live behavior until `FLOW-PROMOTION` approves reviewed code and exact
  runtime configuration.
- Market data bars use `[start, end)` intervals. Strategy-facing bars are
  visible only when complete, never at bar start.
- A flow may iterate only at its documented iteration points. If a proposed
  change needs a different point, update this catalog and the relevant
  guardrail/test documentation in the same change.

## FLOW-DATA

| Field | Rule |
| --- | --- |
| Canonical entrypoint | Historical datasets enter through data-source/catalog boundaries such as `HistoricalCatalog.load(HistoricalCatalogLoadConfig)` and source adapters; runtime subscriptions enter through `StrategyContext.subscribe(...) -> MarketDataActor`. |
| Config owner | Source/catalog/load config, source symbol resolver config, instrument registry/calendar/session config, and provider capability config. |
| Allowed implementation owners | `qts.data`, `qts.data.historical`, `qts.data.sessions`, `qts.data.bars`, `qts.data.adapters`, `qts.data.feeds`, `qts.data.stores`, and shared registry owners for instruments, calendars, mappings, and futures roll resolution. |
| Allowed iteration points | Source schema mapping, dataset validation policy, symbol resolver mappings, provider capability declarations, calendar/session provider data, aggregation settings, and replay/source adapter behavior. |
| Forbidden shortcuts | Product-specific hardcoding in shared code, broker symbols entering runtime/domain internals, historical source code owning shared roll/session semantics, direct strategy subscriptions to provider adapters, market data mutating order/account state, or provider source timeframe redefining requested bar semantics. |
| No-future-data rule | Source adapters and replay services must expose ticks, quotes, and bars only at their event time or `visible_at` time. A bar `[start, end)` becomes strategy-visible at `end`, and generated higher-timeframe bars become visible only after their completed bucket closes. |
| Required verification | Unit tests for parsers/resolvers/adapters, anchor tests for sessions/bar intervals/source timeframe semantics, integration tests for historical and live/fake market data using the same actor-facing contract, plus `make guardrails` when boundaries change. |
| Exit/promotion criteria | Dataset/source evidence is validated, source limitations are explicit, no-lookahead tests pass, and the source can feed research/backtest/paper/live through the documented data boundary without changing trading semantics. |

## FLOW-RESEARCH

| Field | Rule |
| --- | --- |
| Canonical entrypoint | `PYTHONPATH=backend/src uv run python scripts/run_research.py --config <research-config> workflow <workflow-config>`. New VWAP research must use `PYTHONPATH=backend/src uv run python scripts/run_research.py --config configs/research/vwap.yaml workflow configs/research/workflows/vwap_factor_search.yaml`. |
| Config owner | `ResearchSession` owns research session YAML. `ResearchWorkflowConfig` owns gate-based workflow YAML. Factor-spec, factor-evaluation, tearsheet, experiment-store, and research-report configs stay under `qts.research` owners. |
| Allowed implementation owners | `qts.research`, `qts.factors`, `qts.indicators`, strategy code under reviewed strategy boundaries, `scripts/run_research.py` as a thin CLI, and `qts.backtest` only through `ResearchSession.run_backtest(...)` / `ResearchSession.optimize(...)` public paths. |
| Allowed iteration points | Research queries, non-executable factor spec drafts/reviews, factor evaluation input snapshots, workflow gate thresholds, research-only strategy parameters, tearsheet/report contents, and optimizer/backtest steps declared in workflow YAML. |
| Forbidden shortcuts | Generating trading code from research YAML, importing runtime/broker/risk/order internals into workflow execution, starting paper/live runtime, creating orders/target intents outside a reviewed strategy, bypassing `BacktestPipeline`, or using ad hoc VWAP runners. Legacy VWAP ad hoc runners such as `scripts/research/run_vwap_*.py` and VWAP-specific `configs/optimizer` entries are not allowed to remain or be reintroduced. |
| No-future-data rule | Research datasets, factor snapshots, forward-return labels, train/test windows, OOS windows, and workflow validation windows must be predeclared and time ordered. Later OOS, report-only, or live/paper evidence must not tune earlier IS choices without a new research workflow record. |
| Required verification | Unit tests for research workflow/session/factor evaluation/tearsheet behavior, integration tests for `scripts/run_research.py`, optimizer validation tests when workflow optimizer steps change, backtest pipeline tests when backtest steps change, and a manual review that no research artifact is consumed directly by paper/live. |
| Exit/promotion criteria | The workflow exits successfully, records deterministic artifacts and manifests, identifies reviewed code or factor specs, and produces evidence that may enter `FLOW-OPTIMIZER`, `FLOW-BACKTEST`, or `FLOW-PROMOTION`. Research success alone is not paper/live promotion. |

## FLOW-OPTIMIZER

| Field | Rule |
| --- | --- |
| Canonical entrypoint | Optimizer work enters through `ResearchSession.optimize(...)` from a `FLOW-RESEARCH` workflow step or through the generic `scripts/run_optimizer.py <config>` path. VWAP optimizer work must be declared inside `configs/research/workflows/vwap_factor_search.yaml`, not in VWAP-specific `configs/optimizer` YAML. |
| Config owner | `qts.research.optimizer` owns parameter grids, objective metrics, validation constraints, walk-forward splits, failure-window vetoes, and optimizer validation summaries. `BacktestPipelineJob` / `BacktestPipelineRunner` own backtest-config execution. |
| Allowed implementation owners | `qts.research.optimizer`, `qts.research.session`, `scripts/run_optimizer.py` as a thin CLI, `scripts/run_research.py` as the workflow CLI, and `qts.backtest` through the shared backtest pipeline. |
| Allowed iteration points | Parameter spaces, objective metric, validation constraints, train/test windows, failure-window veto windows, selected top-N candidates, capital metric derivations, and output/report locations. |
| Forbidden shortcuts | Vectorized or hand-rolled optimizer paths for backtest-config candidates, direct calls into strategy internals, tuning market data/session/risk/execution/account semantics from optimizer code, silently dropping failed runs, or reintroducing VWAP-specific `configs/optimizer` configs. |
| No-future-data rule | Candidate selection must use only the declared training/evaluation evidence for that optimizer step. Walk-forward test windows and report-only windows may validate or reject candidates but must not feed back into parameter selection unless a new earlier-date training workflow is declared. |
| Required verification | Unit tests for parameter grids, constraints, walk-forward, failure-veto, and validation summaries; integration tests proving optimizer candidates run through `BacktestPipelineRunner`; deterministic artifact/manifest hash checks when output contracts change. |
| Exit/promotion criteria | Validation summaries identify accepted/rejected candidates with reasons, every accepted candidate has backtest manifest evidence, failure-window veto decisions are final for that workflow, and accepted candidates can enter promotion review only as evidence. |

## FLOW-BACKTEST

| Field | Rule |
| --- | --- |
| Canonical entrypoint | `PYTHONPATH=backend/src uv run python scripts/run_backtest.py --config <backtest-config> --output-dir <runs-dir>` or `ResearchSession.run_backtest(...)` / `BacktestPipelineRunner` when invoked from research and optimizer flows. |
| Config owner | Backtest config and `BacktestPipeline` / runner owners own strategy module/params, dataset references, replay clock, simulated execution assumptions, report output, and artifact paths. |
| Allowed implementation owners | `qts.backtest`, `qts.runtime`, `qts.strategy_sdk`, `qts.data`, `qts.registry`, `qts.risk`, `qts.execution`, `qts.portfolio`, and `qts.reporting` through their documented boundaries. |
| Allowed iteration points | Strategy parameters, historical date range, dataset/catalog config, warmup policy, simulated fill/latency/cost assumptions at the execution adapter boundary, and report output selection. |
| Forbidden shortcuts | Backtest-only business paths that bypass RiskEngine, OrderManagerActor, ExecutionActor, AccountActor, Strategy SDK intents, registry roll resolution, or normal market-data aggregation/fan-out. |
| No-future-data rule | `DataView` and strategy callbacks may see only completed bars/events at their visible time. Backtest code must not expose full future dataframes, future account state, later fills, or final-run statistics to strategy decisions. |
| Required verification | Unit tests for changed owners, integration tests for actor/order/account/backtest pipeline flow, replay determinism tests, report hash/manifest tests, and anchor tests for sessions, bar intervals, instrument identity, order state, risk, and portfolio semantics when touched. |
| Exit/promotion criteria | The run writes deterministic manifests/artifacts, no-lookahead and parity tests pass, risk/order/execution/account flow evidence is intact, and results may support research or promotion review but do not themselves enable paper/live. |

## FLOW-PAPER

| Field | Rule |
| --- | --- |
| Canonical entrypoint | `start_runtime(StartRuntimeCommand(runtime_mode="paper_simulated" | "paper_broker", ...))`; local smoke entry may use `scripts/run_paper.py`, and broker drill entry may use paper-only IBKR drill scripts. |
| Config owner | Paper runtime config owns mode, account, strategy set, market-data adapter config, execution adapter config, risk limits, kill switch, and evidence output. |
| Allowed implementation owners | `qts.application.commands.start_runtime`, `qts.runtime`, `qts.data.adapters`, `qts.execution.adapters`, `qts.risk`, `qts.portfolio`, `qts.reporting`, and broker adapter/transport tests. |
| Allowed iteration points | Paper account/client IDs, fake/real paper transports, strategy set from promoted reviewed code, risk limits, kill-switch settings, adapter capability mappings, and soak/evidence output. |
| Forbidden shortcuts | Paper-only strategy behavior, direct broker calls from strategies, reusing live credentials or live risk profiles, market data and order execution sharing mutable adapter state, bypassing risk/order/account actors, or treating paper success as live approval. |
| No-future-data rule | Paper decisions must use only current feed/broker/account events available to the runtime at decision time. Reconciliation and reports may correct evidence after the fact, but they must not rewrite historical strategy decisions or actor state outside approved recovery paths. |
| Required verification | Fake-transport integration tests, paper/live adapter contract tests, risk and kill-switch tests, reconciliation tests, full-chain paper evidence, and paper soak evidence when claiming readiness for live use. |
| Exit/promotion criteria | Paper full-chain evidence, clean reconciliation, kill-switch/rollback evidence, and soak criteria pass for the exact promoted strategy/config. Passing paper evidence enters `FLOW-PROMOTION` for live review; it is not live approval by itself. |

## FLOW-LIVE

| Field | Rule |
| --- | --- |
| Canonical entrypoint | `start_runtime(StartRuntimeCommand(runtime_mode="live_observation" | "live", ...))` after `FLOW-PROMOTION` approval and live readiness checks. |
| Config owner | Live runtime config owns broker account, market-data and order-execution adapter sections, credentials/secret references, live risk profile, capital limits, order permission, kill switch, and observability/recovery settings. |
| Allowed implementation owners | `qts.application.commands.start_runtime`, `qts.runtime`, `qts.data.adapters`, `qts.execution.adapters`, `qts.risk`, `qts.portfolio`, `qts.reporting`, `qts.api` operations surfaces, and operations runbooks/checklists. |
| Allowed iteration points | Observation-only settings, live credentials/secret references, broker account/client IDs, broker capability mappings, production risk/capital limits, kill-switch policy, reconciliation/recovery settings, and rollout/rollback gates. |
| Forbidden shortcuts | Enabling live orders without promotion evidence, using paper credentials/accounts/risk profiles, strategy mode branches, broker reports mutating account state directly, market-data adapters submitting orders, or weakening risk/kill-switch checks for connectivity. |
| No-future-data rule | Live decisions may use only feed, broker, account, and operator events available at runtime. Backfilled broker corrections must be normalized through recovery/reconciliation and must not retroactively justify orders that lacked valid pre-trade state. |
| Required verification | `make check` before milestone/live enablement, live environment/config guardrails, fake-transport and live-boundary tests, reconciliation tests, observation evidence, paper-vs-live comparison, kill-switch drill, rollback review, and engineering/operations/risk signoff. |
| Exit/promotion criteria | Live observation is clean, account/risk/capital limits are approved, reconciliation has no unexplained drift, rollback is ready, and explicit signoff enables the exact build/config/account. Any critical drift returns to rollback or observation. |

## FLOW-PROMOTION

| Field | Rule |
| --- | --- |
| Canonical entrypoint | Human promotion review over recorded research, optimizer, backtest, paper, and operations evidence, using the production rollout/live readiness checklists and an exact build/config/account/capital-limit record. |
| Config owner | Promotion packet owns strategy/factor code version, config hashes, dataset/feed identities, risk/capital limits, target mode, account, evidence links, reviewers, and decision status. |
| Allowed implementation owners | Durable docs/checklists under architecture/operations/decision boundaries, runtime config owners, risk policy owners, strategy/factor code owners, and reporting/evidence writers. |
| Allowed iteration points | Review status, requested evidence, risk/capital proposal, config hash selection, target mode, rollout step, rollback condition, and signoff decision. |
| Forbidden shortcuts | Treating research acceptance, optimizer ranking, backtest PnL, or paper success as automatic promotion; promoting unreviewed generated code; changing runtime config after signoff without a new decision; or enabling live order submission from research/optimizer/report artifacts. |
| No-future-data rule | Promotion decisions may use only evidence that existed and was declared at review time. Later paper/live outcomes require a new review record and cannot be backdated into an earlier approval. |
| Required verification | Review checklist completion, required flow evidence manifests/hashes, `make check` for milestone/live readiness when code changed, paper/full-chain/soak evidence for live promotion, risk/operations approval, and documented rollback criteria. |
| Exit/promotion criteria | The packet records Go / No-Go. A Go decision authorizes only the exact reviewed build, config hash, account, strategy set, and capital limits; a No-Go returns work to the originating flow with explicit gaps. |

## FLOW-REPORTING

| Field | Rule |
| --- | --- |
| Canonical entrypoint | Report writers and CLIs such as `scripts/generate_backtest_report.py` consume completed manifests/artifacts; runtime/backtest writers finalize reports through `qts.reporting` owners. |
| Config owner | Report config, manifest schema, artifact writer config, output path, template selection, and report metadata are owned by `qts.reporting` and mode-specific artifact writer boundaries. |
| Allowed implementation owners | `qts.reporting`, backtest artifact writers, runtime event/report sinks, API read models for reports, and research report owners for research-only reports. |
| Allowed iteration points | Report templates, derived display metrics, artifact path/hash recording, manifest schema extensions, operator evidence summaries, and read-only API/report queries. |
| Forbidden shortcuts | Mutating runtime/account/order state from reports, recomputing strategy decisions from report code, using reports as promotion without `FLOW-PROMOTION`, hiding failed/rejected runs, or letting report-only metrics alter completed backtest/paper/live behavior. |
| No-future-data rule | Reports may aggregate only completed artifacts inside the declared run/evidence horizon. Report-only windows and post-run summaries must not feed back into the run that produced them. |
| Required verification | Unit tests for report contracts/schema, deterministic manifest/hash tests, integration tests for report generation when mode artifacts change, and review that report payloads remain read-only. |
| Exit/promotion criteria | Reports are deterministic, hashable, and linked to source artifacts/manifests. They may support research, optimizer, backtest, paper/live operation, or promotion evidence, but they are not a trading path. |

## VWAP Research Gate

New VWAP research has exactly one canonical workflow:

```bash
PYTHONPATH=backend/src uv run python scripts/run_research.py \
  --config configs/research/vwap.yaml \
  workflow configs/research/workflows/vwap_factor_search.yaml
```

Do not add, extend, or depend on VWAP ad hoc research runners under
`scripts/research/run_vwap_*.py`. Do not add or retain VWAP-specific optimizer
YAML under `configs/optimizer`; VWAP sweeps and validation gates belong in the
research workflow YAML above. If a branch still contains those legacy paths,
they are cleanup blockers, not accepted alternate entrypoints.
