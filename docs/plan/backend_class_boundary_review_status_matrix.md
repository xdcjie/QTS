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
| RuntimeMarketDataCoordinator | 530 | Runtime market data | High | Retain with split target | Keep as coordinator while market-data risk and source event routing remain cohesive; split if subscription recovery or risk context grows further. | `tests/unit/runtime/test_market_data_permission_freshness_acceptance.py`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| BacktestActorLoop | 515 | Backtest runtime loop | High | Retain with split target | Keep replay/event loop ownership; move artifact or input assembly if it reappears. | `BacktestActorLoopCohesionRule`; `tests/unit/scripts/test_verify_guardrails.py` | Complete |
| OperationsService | 245 | Application services | Medium | Retain | Keep operator API orchestration here while runtime internals stay behind application boundaries. | `tests/unit/application`; `backend/src/qts/application/services/operations.py` | Complete |
| BacktestEngine | 421 | Backtest engine | High | Retain | Keep engine orchestration over actor loop and prepared replay inputs; reject historical input assembly in the engine. | `BacktestEngineCohesionRule`; `tests/unit/scripts/test_verify_guardrails.py` | Complete |
| RuntimeSession | 397 | Runtime facade | High | Retain | Keep as facade over lifecycle, market-data, broker lifecycle, safety, recovery, rollback, and event envelopes. | `RuntimeSessionComplexityRule`; `docs/architecture/runtime_session_complexity.md` | Complete |
| ReplayMarketDataSource | 22 | Data sources | Medium | Retain | Keep as replay bundle construction entrypoint while subscription replay behavior stays in source-owned classes. | `tests/unit/data/test_replay_market_data_source.py`; `docs/architecture/naming.md` | Complete |
| IbkrTwsMarketDataTransport | 359 | Data transports | High | Retain | Keep external TWS market-data connection and callback ingress out of adapters and runtime actors. | `TransportCanonicalPathRule`; `TransportAdapterImportRule`; `docs/architecture/naming.md` | Complete |
| IbkrTwsOrderExecutionTransport | 306 | Execution transports | High | Retain | Keep external TWS order connection and callback ingress out of execution adapters and runtime actors. | `TransportCanonicalPathRule`; `TransportAdapterImportRule`; `docs/architecture/naming.md` | Complete |
| ReplayMarketDataBundleBuilder | 346 | Data sources | Medium | Retain | Keep replay-ready market data, registry, and provenance assembly behind the replay bundle boundary. | `tests/unit/data/test_replay_market_data_source.py`; `docs/architecture/module_boundaries.md` | Complete |
| IbkrCallbackNormalizer | 533 | Execution adapters | High | Retain with split target | Keep callback idempotency and normalization centralized; split only when independent callback families need separate public owners. | `tests/unit/execution/test_ibkr_callback_idempotency.py`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| BrokerRuntimeTopologyResolver | 314 | Runtime topology | Medium | Retain | Keep runtime topology resolution behind a single resolver boundary rather than leaking actor wiring to services. | `tests/unit/runtime`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| BrokerRuntimeStartupChecklist | 330 | Runtime startup | High | Retain | Keep startup readiness facts and live-capital gate evidence in one startup checklist boundary. | `tests/unit/runtime/test_live_startup_guard.py`; `docs/architecture/runtime_coordinator_decisions.md` | Complete |
| ResearchSession | 366 | Research facade | Medium | Retain with split target | Keep as notebook/script facade over research book, discovery, candidate review, experiment recording, and shared backtest pipeline; move candidate/review behavior into `qts.research.factor_candidate` and `FactorSpecStore` as it grows. | `tests/unit/research/test_research_session.py`; `tests/integration/test_research_session_facade.py`; `docs/research/research_session_v1.md` | Complete |
| ResearchWorkflowRunner | 430 | Research workflow orchestration | Medium | Retain with split target | Keep as gate-based workflow orchestrator over `ResearchSession` public APIs while report rendering, optimizer validation, factor evaluation, and persistence stay in their own owners; split step handlers if another executable-evidence step is added. | `tests/unit/research/test_research_workflow.py`; `tests/integration/test_run_research_cli.py`; `docs/research/research_session_v1.md` | Complete |
| PromotionPacketV2 | 360 | Research promotion packet | High | Retain with split target | Keep as the machine-checkable promotion packet validator while live-grade artifact refs, metrics schema, data quality, reproducibility, evidence policy, and audit append remain one atomic validation contract; split reusable artifact-ref validation if another promotion packet version needs it. | `tests/unit/research/test_promotion_packet.py`; `tests/unit/research/test_run_research_promotion_cli.py`; `docs/architecture/system_flows.md` | Complete |

## Verification Plan

- `PYTHONPATH=backend/src uv run pytest tests/unit/scripts/test_verify_guardrails.py tests/unit/docs/test_backend_class_boundary_review_status_matrix.py -q`
- `make guardrails`
- `uv run mypy backend tests`

## Verification Log

Initial RED gate:

- New guardrail tests failed before implementation because `CLASS_BOUNDARY_MATRIX` and `CLASS_OWNERSHIP_DOCSTRING` were not emitted.
- New docs matrix tests failed before this file existed.

Implementation evidence is recorded by the verification commands run after this matrix is updated.
