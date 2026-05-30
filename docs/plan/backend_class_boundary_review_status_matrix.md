# Backend Class Boundary Review Status Matrix

Source backlog: CBO-02 / CBO-07 backend class boundary review.

Scope: production backend classes with broad ownership names or high line counts.

## Completion Rules

A row is complete only when its owner, risk, decision, target, evidence, and status
identify a concrete class-boundary outcome. Passing existing tests alone is not enough.

- production classes over 300 lines must appear in this matrix.
- production classes over 500 lines must record a split or retain decision and evidence.
- broad suffix classes ending in `Service`, `Coordinator`, `Manager`, `Builder`, `Source`, or `Adapter` must state ownership in the first docstring line.
- `make guardrails` is the enforcement gate for matrix coverage and broad-suffix docstring ownership.

## Status Matrix

| Class | Current lines | Owner | Risk | Decision | Target | Evidence | Status |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| IbkrOrderExecutionAdapter | 242 | Execution adapters | High | Retain | Keep as broker execution adapter facade over callback normalization and transport boundaries. | `tests/unit/execution/test_ibkr_callback_idempotency.py`; `docs/architecture/module_boundaries.md` | Complete |
| CallerPresenceRule | 324 | Quality guardrails | Medium | Retain | Keep the §11 caller-presence gate cohesive: baseline load, deferral parsing, re-export-aware caller indexing, owner-use detection, and auto-exemptions are one rule. | `tests/unit/scripts/test_verify_guardrails.py`; `tests/unit/quality/test_caller_presence_owner_use.py` | Complete |
| RuntimeMarketDataCoordinator | 530 | Runtime market data | High | Retain with split target | Keep as coordinator while market-data risk and source event routing remain cohesive; split if subscription recovery or risk context grows further. | `tests/unit/runtime/test_market_data_permission_freshness_acceptance.py`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| BacktestActorLoop | 805 | Backtest runtime loop | High | Retain with split target | Keep replay/event loop ownership; move artifact or input assembly if it reappears. | `BacktestActorLoopCohesionRule`; `tests/unit/scripts/test_verify_guardrails.py` | Complete |
| OperationsService | 245 | Application services | Medium | Retain | Keep operator API orchestration here while runtime internals stay behind application boundaries. | `tests/unit/application`; `backend/src/qts/application/services/operations.py` | Complete |
| BacktestEngine | 349 | Backtest engine | High | Retain | Engine orchestrates the actor loop over prepared replay inputs; risk/margin policy (`BacktestRiskPolicyFactory`), dataset manifest/provenance (`BacktestDatasetManifestBuilder`), runtime-topology manifest (`BacktestRuntimeTopologyManifestBuilder`), artifact emission (`BacktestArtifactService`), and runtime-actor public surface are extracted (QTS-FINAL-002). Engine no longer imports `qts.reporting.backtest`, `qts.runtime.sinks`, `qts.runtime.actors` (runtime), `qts.runtime.topology`, or `qts.risk.rule_registry`. Remaining extraction: engine assembler (`__init__` dependency construction) toward the thin-orchestrator target. | `BacktestEngineCohesionRule`; `PublicSurfaceRule`; `tests/unit/scripts/test_verify_guardrails.py` | Complete |
| RuntimeSession | 397 | Runtime facade | High | Retain | Keep as facade over lifecycle, market-data, broker lifecycle, safety, recovery, rollback, and event envelopes. | `RuntimeSessionComplexityRule`; `docs/architecture/runtime_session_complexity.md` | Complete |
| ReplayMarketDataSource | 22 | Data sources | Medium | Retain | Keep as replay bundle construction entrypoint while subscription replay behavior stays in source-owned classes. | `tests/unit/data/test_replay_market_data_source.py`; `docs/architecture/naming.md` | Complete |
| IbkrTwsMarketDataTransport | 359 | Data transports | High | Retain | Keep external TWS market-data connection and callback ingress out of adapters and runtime actors. | `TransportCanonicalPathRule`; `TransportAdapterImportRule`; `docs/architecture/naming.md` | Complete |
| IbkrTwsOrderExecutionTransport | 306 | Execution transports | High | Retain | Keep external TWS order connection and callback ingress out of execution adapters and runtime actors. | `TransportCanonicalPathRule`; `TransportAdapterImportRule`; `docs/architecture/naming.md` | Complete |
| ReplayMarketDataBundleBuilder | 346 | Data sources | Medium | Retain | Keep replay-ready market data, registry, and provenance assembly behind the replay bundle boundary. | `tests/unit/data/test_replay_market_data_source.py`; `docs/architecture/module_boundaries.md` | Complete |
| IbkrCallbackNormalizer | 533 | Execution adapters | High | Retain with split target | Keep callback idempotency and normalization centralized; split only when independent callback families need separate public owners. | `tests/unit/execution/test_ibkr_callback_idempotency.py`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| BrokerRuntimeTopologyResolver | 314 | Runtime topology | Medium | Retain | Keep runtime topology resolution behind a single resolver boundary rather than leaking actor wiring to services. | `tests/unit/runtime`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| BrokerRuntimeStartupChecklist | 330 | Runtime startup | High | Retain | Keep startup readiness facts and live-capital gate evidence in one startup checklist boundary. | `tests/unit/runtime/test_live_startup_guard.py`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| TargetIntentProcessor | 320 | Runtime intent processing | High | Retain | Keep target-intent translation cohesive: it owns risk-state assembly (equity, margin, intraday PnL, signed delta), order planning, risk checks, and order submission for one account. Split fill/risk-state assembly only if it grows further. | `tests/unit/runtime/test_target_intent_processor_margin.py`; `tests/unit/backtest/test_backtest_intent_processor.py` | Complete |
| NoLookaheadValidationRunner | 410 | Research validation | High | Retain | Keep no-lookahead timing validation (feature/label/window/protocol checks and artifact payload) behind one runner boundary that the gauntlet consumes. | `tests/unit/research/test_no_lookahead_validation_runner.py` | Complete |
| ResearchSession | 762 | Research facade | Medium | Retain with split target | Keep as notebook/script facade over research book, discovery, candidate review, experiment recording, and shared backtest pipeline; move candidate/review behavior into `qts.research.factor_candidate` and `FactorSpecStore` as it grows. | `tests/unit/research/test_research_session.py`; `tests/integration/test_research_session_facade.py`; `docs/research/research_session_v1.md` | Complete |
| ResearchWorkflowRunner | 1528 | Research workflow orchestration | Medium | Retain with split target | Keep as gate-based workflow orchestrator over `ResearchSession` public APIs while report rendering, optimizer validation, factor evaluation, and persistence stay in their own owners; split step handlers if another executable-evidence step is added. | `tests/unit/research/test_research_workflow.py`; `tests/integration/test_run_research_cli.py`; `docs/research/research_session_v1.md` | Complete |
| PromotionPacketV2 | 647 | Research promotion packet | High | Retain with split target | Keep as the machine-checkable promotion packet validator while live-grade artifact refs, metrics schema, data quality, reproducibility, evidence policy, and audit append remain one atomic validation contract; split reusable artifact-ref validation if another promotion packet version needs it. | `tests/unit/research/test_promotion_packet.py`; `tests/unit/research/test_run_research_promotion_cli.py`; `docs/architecture/system_flows.md` | Complete |
| ResearchArtifactGraphBuilder | 395 | Research artifact graph | High | Retain with split target | Keep artifact relationship normalization in the graph builder while node/edge validation stays in `ResearchArtifactGraph`; split section-specific payload resolvers if another graph schema version adds independent owners. | `tests/unit/research/test_artifact_graph.py`; `tests/unit/research/test_artifact_graph_builder.py`; `docs/architecture/system_flows.md` | Complete |
| ResearchExperimentRunner | 1414 | Research experiment artifacts | High | Retain with split target | Keep deterministic ManifestV2 trial artifact production and the validation-rerun orchestration (deterministic-replay / walk-forward / failure-window / cost-stress backtests) in the runner while queue state, selector decisions, landscape analytics, and campaign lifecycle remain outside this class. The promotion-grade validation-artifact *writer* (payload builders + no-lookahead timing derivation + content-addressed wrappers) was extracted to `ValidationArtifactWriter` (H1, 2026-05-30); the runner now delegates to it. Split further per-artifact writers if another executable-evidence artifact is added. | `tests/unit/research/orchestrator/test_experiment_runner.py`; `tests/unit/research/orchestrator/test_validation_artifact_writer.py`; `tests/integration/research/test_autonomous_research_engine_gc_si.py`; `docs/architecture/system_flows.md` | Complete |
| ValidationArtifactWriter | 664 | Research experiment artifacts | High | Retain with split target | Writes the seven promotion-grade survivor validation artifacts (walk-forward, failure-window, cost-stress, correlation, capacity, deterministic-replay, no-lookahead) as content-addressed wrapper JSON for a succeeded trial; counterpart to `ValidationArtifactReader`. Extracted from `ResearchExperimentRunner` (H1) as the cohesive validation-artifact *producer*. The shared manifest-reading primitives (`manifest_decimal`, `manifest_artifact_row_count`, `write_stable_json`) are module-level single-source-of-truth functions the runner also uses, so hash-determining logic is never duplicated. Split per-artifact builders only if an independent artifact schema needs its own owner. | `tests/unit/research/orchestrator/test_validation_artifact_writer.py`; `tests/unit/research/orchestrator/test_no_lookahead_forward_transform.py`; `tests/integration/research/test_autonomous_rejects_lookahead_factor.py` | Complete |
| AutonomousResearchEngine | 2429 | Research campaign orchestration | High | Retain with split target | Keep bounded research-only campaign orchestration here while campaign config, experiment artifacts, selector gates, landscape analytics, promotion packets, audit log, and artifact graph stay in their owning modules; split campaign artifact projection if engine adds another lifecycle phase. | `tests/integration/research/test_autonomous_research_engine_gc_si.py`; `tests/integration/research/test_gc_si_autonomous_acceptance.py`; `tests/unit/research/test_run_research_campaign_cli.py`; `docs/architecture/system_flows.md` | Complete |

## Verification Plan

- `PYTHONPATH=backend/src uv run pytest tests/unit/scripts/test_verify_guardrails.py tests/unit/docs/test_backend_class_boundary_review_status_matrix.py -q`
- `make guardrails`
- `uv run mypy backend tests`

## Verification Log

Initial RED gate:

- New guardrail tests failed before implementation because `CLASS_BOUNDARY_MATRIX` and `CLASS_OWNERSHIP_DOCSTRING` were not emitted.
- New docs matrix tests failed before this file existed.

Implementation evidence is recorded by the verification commands run after this matrix is updated.
