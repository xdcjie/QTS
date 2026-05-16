# QTS Final Platform Freeze M0-M6 Review Status Matrix

Source backlog: `docs/plan/qts_final_platform_freeze_review_and_tasks.md`

Scope: M0 + M1 + M2 + M3 + M4 + M5 + M6 (Final naming, readiness suites, live capital hard gate, IBKR failure/order reliability, complexity budget, and strategy/factor research handoff)

Baseline: 2026-05-16

原则：本轮不引入 legacy path，不保留兼容历史债，不补齐兼容别名。  
任何出现旧命名、旧导入路径、历史兼容分支的实现都作为阻塞项处理。

## Completion Rules

M0 is complete only when all three tasks have hard gates that can fail CI:

- dedicated implementation + tests exist, and tests fail when legacy/compat paths are restored;
- manifests/events expose the required v1 platform baseline fields in all supported modes;
- exception mechanism is explicit and has expiry check.

M1 is complete only when M1.1-M1.6 are migration-complete with zero legacy references outside one-time migration tests:

- classes/functions/modules in `backend/src/qts` contain no `LiveRuntimeConfig`, `PaperBrokerRuntimeConfig`,
  `LiveRuntimeEventSink`, `LiveOrderPermission`, `LiveReconciliation`, `LiveRecoveryDecision`, or runtime `RiskConfig` aliases that differ by boundary.
- mode-specific behavior is expressed by `RuntimeMode` and runtime profile/data values, not naming.

M2 is complete only when final readiness suites prove each supported non-live-capital mode is operational from current artifacts:

- backtest golden runs are deterministic and include dataset provenance plus config hash;
- paper simulated runtime exercises market data -> strategy -> intent -> risk -> order -> fill -> account -> sink -> manifest without constructing IBKR transports;
- IBKR paper broker acceptance evidence includes market-data anchor, submit/cancel evidence, and reconciliation evidence while rejecting live account codes;
- live observation acceptance proves broker connectivity and event/reconciliation evidence while real-money order submission stays impossible.

M3 is complete only when live capital remains disabled by default and real broker order submission is impossible unless every live-capital gate is true at the execution boundary:

- `runtime_mode == LIVE`
- `order_submission_permission == LIVE_ORDERS_ALLOWED`
- `startup_decision == ALLOW_LIVE`
- `operator_signoff.valid == true`
- `market_data_permission == LIVE`
- `market_data_freshness == FRESH`
- `reconciliation_status == CLEAN`
- `kill_switch == INACTIVE`
- `broker_account_kind == LIVE`
- `ibkr_account_code` starts with `DU` and does not start with `DUP`
- `ibkr_port == 4001` unless an explicit approved override is present
- kill-switch cancellation remains a safety action and is not blocked by live-order permission.

M4 is complete only when broker callbacks, reconnect recovery, and live-capable market-data risk gates are proven idempotent and fail-closed:

- duplicate IBKR callbacks are dropped without duplicate fills, duplicate order creation, or duplicate account mutation;
- out-of-order callbacks are quarantined until resolvable, never applied under the wrong account or internal order;
- commission updates can complete cost evidence without applying a second fill;
- reconnect always degrades runtime and effective order permission before reconciliation;
- reconnect only restores paper/live order submission after open orders, positions, cash, executions, and market-data subscriptions are refreshed and reconciliation is clean;
- delayed, frozen, delayed-frozen, unavailable, or stale market data rejects live-capable orders and emits runtime evidence.

M5 is complete only when complexity and inventory limits are enforceable CI gates, not review notes:

- `RuntimeSession` remains a facade with a fixed public method budget and no broker transport, account mutation, risk-rule, callback, or order-state ownership;
- runtime coordinator classes each have a keep/merge/delete decision in durable architecture docs, and kept coordinators carry state, policy, evidence, safety, boundary, or complexity responsibility;
- production class count is pinned to a freeze baseline, and new production classes require an unexpired platform-freeze exception;
- DTO / ValueObject classes exist only for cross-boundary contracts or domain value semantics, not one-field wrappers;
- current panorama/source inventory and architecture docs do not expose removed live aliases, old paths, or stale generated cache.

M6 is complete only when strategy and factor research can run through stable research contracts without touching runtime internals:

- `BacktestService.submit(...)` returns manifest/artifact paths, metrics, and artifact hashes from the manifest/report boundary;
- `BacktestService.submit_batch(...)` is deterministic for identical ordered inputs and does not expose runtime actors;
- factor code implements a versioned deterministic contract with explicit missing-data and universe-filtering semantics;
- every experiment manifest includes platform baseline version, strategy/factor/dataset versions, config hash, metrics, and addressable artifact hashes;
- research, strategy, and factor packages cannot import runtime actors, execution adapters, broker transports, or reconciliation internals.

## M0 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Platform final baseline has a single canonical declaration and manifest/event owner | `docs/architecture/platform_final_baseline_v1.md`, reporting runtime manifest builders | Keeping multiple ad-hoc baseline constants or writing baseline only in one mode | M0.1 dedicated tests for backtest/broker/runtime event baseline version presence |
| Freeze policy is enforced on package boundaries, not documented only | `qts.quality` guardrail and `tests/quality/test_platform_freeze.py` | Copy-pasting a doc note while allowing production class additions | New `PlatformFreezeRule` with `tests/quality/test_platform_freeze.py` and CI `make guardrails` |
| Strategy/factor research code only depends on stable SDK surface | `StrategySdkPublicSurfaceRule`, SDK rules tests | Adding more forbidden symbols via exceptions or backdoors | Extended SDK surface rule + explicit import-ban tests for strategy/factor packages |
| Runtime naming matches runtime semantics, not environment labels | `qts.runtime.config`, `qts.runtime.permissions`, `qts.runtime.sinks`, `qts.runtime.state_recovery` | Using `Live*` names for broker-capable behavior, including paper and live observation paths | Per-task tests that assert canonical names and a no-legacy scan guardrail that fails CI |
| Risk profile ownership is by boundary and not duplicated | `qts.risk.config` and `qts.runtime.config` references only by id/profile-ref | Two differently-owned `RiskConfig` concepts in runtime and risk modules | Config model tests that bind runtime to a risk profile ref with shared validation |

## M3 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Real-money order submission is forbidden unless all live-capital facts are simultaneously true immediately before broker execution | Execution boundary policy used by `ExecutionActor`, `BrokerExecutionAdapter`, and `IbkrOrderExecutionAdapter` | Checking only API, `RuntimeSession`, config flags, or startup status and trusting downstream code | M3.1 tests block every missing fact, including paper gateway/account facts |
| Live capital enablement requires dual-control signoff with scoped strategy/account/instrument/notional limits and expiry | `OperatorSignoff`, `LiveCapitalEnablementRequest`, `LiveCapitalEnablementDecision` under runtime-owned live-capital boundary | Treating `operator_signoff_id` or a single config/API flag as permission to submit live orders | M3.2 tests for missing approvers, expiry, scope mismatch, and evidence output |
| Expired or invalid signoff downgrades runtime to observation-only, never live orders | Startup decision/checklist and live-capital decision owner | Letting old evidence keep live orders enabled until process restart | Startup and execution tests prove expired signoff blocks new live orders |
| Kill switch blocks new orders while preserving safety cancels and requiring authorized deactivation | `RuntimeSafetyController` and kill-switch drill script | Blocking cancellations during a safety event or allowing low-privilege deactivation | M3.3 drill evidence and unit/integration tests for block/cancel/deactivate paths |
| Drill evidence is a prerequisite for live capital enablement | Live-capital readiness decision consumes `artifacts/drills/kill_switch/<run_id>/evidence.json` | Marking live capital ready from documentation or manual assertion only | `test_kill_switch_drill_evidence_required_for_live_capital` |

## M4 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| IBKR callback handling is idempotent across duplicate `orderStatus`, `execDetails`, `commissionReport`, and reconnect `openOrder` replay | `IbkrOrderExecutionAdapter`, `BrokerOrderMap`, callback quarantine, and execution report normalization | Applying callbacks directly to account/order state without idempotency keys or route/account checks | M4.1 duplicate/out-of-order callback tests |
| Unknown or account-mismatched broker callbacks are quarantined, not applied or silently dropped | IBKR adapter callback quarantine and broker-order mapping boundary | Creating internal orders from unknown broker callbacks or accepting callbacks from the wrong broker account | `test_open_order_unknown_internal_order_quarantined`; `test_callback_account_mismatch_quarantined` |
| Reconnect never resumes order submission until reconciliation is clean | `RuntimeBrokerLifecycleCoordinator`, `BrokerReconnectReconciliation`, `BrokerRuntimeReconciliation`, `RuntimeSafetyController` | Calling `recover()` or resuming order flow immediately after socket reconnect | M4.2 reconnect degradation/reconciliation tests |
| Reconnect refreshes market-data subscriptions and broker state before reconciliation | Runtime broker lifecycle / market-data coordinator boundary | Treating reconnect as a pure state transition without resubscription and broker snapshot refresh | `test_reconnect_resubscribes_market_data`; `test_reconnect_reconciles_open_orders_positions_cash` |
| Live-capable orders require live and fresh market data | `MarketDataPermissionRiskRule`, `MarketDataFreshnessRiskRule`, `RiskEngine`, `RuntimeMarketDataCoordinator` | Checking market-data permission only in UI/startup or letting stale/delayed bars reach live-capable orders | M4.3 permission/freshness runtime risk tests |

## M5 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| `RuntimeSession` is only a facade over lifecycle, market-data dispatch, broker lifecycle, safety, recovery, rollback, and event envelopes | `RuntimeSessionComplexityRule`, `docs/architecture/runtime_session_complexity.md`, runtime coordinators | Adding business decisions directly to `RuntimeSession` because the call site is convenient | `test_runtime_session_complexity_budget_passes`; `test_runtime_session_does_not_import_ibkr_transport`; `test_runtime_session_does_not_apply_account_mutation_directly` |
| Coordinator classes are retained only when they own state, policy, evidence, safety, external boundary, or complexity containment | `docs/architecture/runtime_coordinator_decisions.md`, `RuntimeCoordinatorDecisionRule` | Keeping thin pass-through classes without a documented keep reason | `test_every_runtime_coordinator_has_decision_record`; `test_deleted_coordinator_has_no_production_import`; `test_kept_coordinator_has_state_policy_or_evidence_responsibility` |
| Production class inventory cannot grow past the freeze baseline without explicit exception | `artifacts/quality/class_inventory_baseline.json`, `ClassInventoryBudgetRule`, platform freeze exceptions | Treating generated class count drift as harmless documentation churn | `test_class_inventory_does_not_exceed_platform_baseline_without_exception` |
| DTO / ValueObject classes must justify a real boundary or value-semantic role | `ClassInventoryBudgetRule`, module docstrings/class names, API/application/runtime boundary ownership | Adding one-field wrappers to satisfy shape preferences or naming symmetry | `test_single_field_dto_requires_boundary_justification`; `test_no_duplicate_dto_names_across_application_and_runtime` |
| Removed live aliases and old source paths cannot reappear in production, tests, or generated docs | `RemovedImportNoNewUsageRule`, source inventory generator, stale architecture text guard | Leaving old alias imports, old HTML inventory cache, or compatibility modules for reviewer convenience | `test_removed_live_alias_imports_fail`; `test_panorama_source_index_uses_current_paths_only`; `test_archived_docs_are_not_used_as_current_inventory` |

## M6 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Research backtest submission is an application service contract over manifests and artifacts | `BacktestService`, `BacktestRunResult`, backtest reporting manifest | Returning `BacktestEngine`, actors, runtime dependencies, or mutable internal objects to research code | `test_research_backtest_submit_returns_manifest_and_artifacts`; `test_research_batch_submit_is_deterministic`; `test_research_code_cannot_access_runtime_actor_internals` |
| Factor research has a versioned deterministic contract | `qts.factors` and `docs/research/factor_contract_v1.md` | Treating factors as ad-hoc callables without name/version, missing-data policy, or ranking convention | `test_factor_has_name_and_version`; `test_factor_is_deterministic`; `test_factor_handles_missing_data_explicitly`; `test_factor_package_has_no_runtime_execution_broker_imports` |
| Experiment output is reproducible and comparable by manifest, not runtime state | `qts.research` experiment manifest writer and `artifacts/research/<experiment_id>/` | Letting notebooks or strategies infer versions from process state or read runtime internals | `test_experiment_manifest_contains_strategy_factor_dataset_versions`; `test_experiment_manifest_contains_platform_baseline_version`; `test_same_experiment_input_produces_same_config_hash`; `test_experiment_artifacts_are_addressable_by_hash` |
| Final platform closure is a gate over M0-M6 evidence, not a verbal declaration | `docs/plan/qts_final_platform_freeze_review_status_matrix.md`, guardrails, readiness/golden/paper/quality tests | Marking platform frozen while any milestone lacks hard verification evidence | `make check`; M6 focused tests; generated panorama/source inventory freshness tests |

## Status Matrix

| Task | Status | Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M0.1 Define `QTS Platform Final Baseline v1` | Complete | `docs/architecture/platform_final_baseline_v1.md`; `qts.reporting.base`, `qts.reporting.backtest`, `qts.reporting.broker_runtime`, `qts.runtime.sinks.base`; `test_backtest_manifest_contains_platform_baseline_version`, `test_broker_runtime_manifest_contains_platform_baseline_version`, `test_runtime_event_contains_platform_baseline_version` | None | Validate three new tests in `make test-unit` scope |
| M0.2 Add platform freeze class/namespace hard gate | Complete | `qts.quality` `PlatformFreezeRule`; `docs/architecture/platform_freeze_exceptions.yaml`; `tests/quality/test_platform_freeze.py`; `test_guardrail_suite_includes_required_m0_hard_gate_rules` | None | Add a temporary exception must have explicit `expiry`; expired or missing exception must fail |
| M0.3 Freeze strategy/factor public API dependency surface | Complete | `StrategySdkPublicSurfaceRule` (includes `qts.reconciliation`); `docs/research/strategy_factor_api_v1.md`; `test_strategy_package_cannot_import_runtime_internals`, `test_strategy_package_cannot_import_broker_transports`, `test_factor_package_has_no_runtime_dependency`, `test_factor_package_has_no_runtime_execution_broker_imports` | None | Blocked if any new strategy/factor public symbols/imports are added outside `qts.strategy_sdk` and `qts.factors` |
| M1.1 Rename `LiveRuntimeConfig` to `BrokerRuntimeConfig` | Complete / Verified | `backend/src/qts/runtime/config/models.py` defines `BrokerRuntimeConfig`; `backend/src/qts/runtime/config/live.py` removed; guardrails reject the removed config import path and symbol | None | `tests/unit/scripts/test_verify_guardrails.py::test_guardrails_reject_removed_m1_runtime_naming_imports` rejects removed M1 imports |
| M1.2 Consolidate `PaperBrokerRuntimeConfig` | Complete / Verified | `backend/src/qts/runtime/config/paper.py` keeps only `PaperSimulatedRuntimeConfig`; paper broker uses `BrokerRuntimeConfig(mode=PAPER_BROKER)`; direct `BrokerRuntimeConfig(mode=PAPER_SIMULATED)` is rejected | None | `tests/unit/runtime/test_live_startup_guard.py::test_paper_runtime_configs_have_disjoint_semantics` |
| M1.3 Rename `LiveRuntimeEventSink` | Complete / Verified | `backend/src/qts/runtime/sinks/broker_runtime.py` defines `BrokerRuntimeEventSink`; `backend/src/qts/runtime/sinks/live.py` removed; persisted rows now include `event_hash` | None | `tests/unit/runtime/test_live_runtime_event_sink.py::test_live_runtime_event_sink_writes_stable_append_only_ndjson` plus removed-import guardrail |
| M1.4 Rename `LiveOrderPermission` | Complete / Verified | `backend/src/qts/runtime/permissions.py` defines `OrderSubmissionPermission`; startup decisions and manifests use `order_submission_permission` wording | None | Runtime startup/session tests assert observation, paper, and live permission behavior |
| M1.5 Rename `LiveReconciliation` / `LiveRecoveryDecision` | Complete / Verified | `backend/src/qts/runtime/broker_runtime_reconciliation.py`; `backend/src/qts/runtime/state_recovery.py` exports `RuntimeRecoveryDecision` and `RuntimeRecoveryDecisionStatus`; old module path removed | None | Reconciliation/state recovery tests plus removed-import guardrail |
| M1.6 Resolve `RiskConfig` duplicate concepts | Complete / Verified | Runtime backtest config class is `BacktestRiskConfig`; risk package retains `qts.risk.config.RiskConfig` ownership; runtime config exports `BacktestRiskConfig` only | None | Backtest config/input tests cover `BacktestRiskConfig`; architecture docs now distinguish runtime backtest risk from package risk config |
| M2.1 Backtest final golden / replay suite | Complete / Verified | `tests/replay/test_backtest_determinism.py`; `tests/replay/test_backtest_report_hash.py`; backtest manifest dataset provenance/config hash anchors; `make test-replay` | None | Same research config/data/strategy produce same report hash, normalized manifest hash, and normalized artifact hashes |
| M2.2 Paper simulated final smoke suite | Complete / Verified | `tests/integration/test_readiness_smoke_matrix.py`; `tests/integration/test_paper_runtime_full_chain.py`; paper simulated smoke exercises market data -> strategy -> risk -> order -> fill -> account -> event sink -> manifest | None | `readiness-smoke-local` includes `paper_simulated_market_data_to_fill` and emits manifest/event evidence |
| M2.3 IBKR paper broker acceptance suite | Complete / Verified from external evidence | `tests/anchor/test_readiness_smoke_matrix_external.py`; `tests/anchor/test_ibkr_gateway_paper_readiness.py`; `tests/integration/test_ibkr_gateway_full_chain_anchor.py`; `scripts/generate_external_readiness_smoke_evidence.py`; `make readiness-smoke-external`; paper broker local boundaries in `make check` | None for persisted external IBKR paper evidence; fresh Gateway market-data anchors still depend on IBKR session availability | `readiness-smoke-external` fails if complete `paper-full-chain-*` evidence, event rows, manifest path, or readiness smoke wrappers are missing |
| M2.4 Live observation acceptance suite | Complete / Environment-Gated | `tests/integration/test_readiness_smoke_matrix.py`; `tests/integration/test_ibkr_live_observation_anchor.py`; startup/session tests block real orders in observation mode | External live observation anchor is skipped unless `--live-observation-only` and config are explicitly provided | `live_observation_market_data_no_orders` local smoke plus external observation-only anchor before live observation production use |
| M3.1 Enforce live order gate closest to execution boundary | Complete / Verified | `LiveCapitalOrderDecision`; `ExecutionActor`; `BrokerExecutionAdapter`; `IbkrOrderExecutionAdapter`; `RuntimeSessionDependencies.live_capital_decision`; gateway/account checks are generic in runtime and broker-specific facts stay at adapter/config boundary | None | `test_live_order_blocked_without_live_order_permission`; `test_live_order_blocked_without_operator_signoff`; `test_live_order_blocked_when_reconciliation_not_clean`; `test_live_order_blocked_when_market_data_delayed`; `test_live_order_blocked_when_market_data_stale`; `test_live_order_blocked_when_kill_switch_active`; `test_live_order_blocked_when_account_code_is_dup`; `test_live_order_blocked_when_gateway_port_is_paper` |
| M3.2 Add operator signoff and dual-control | Complete / Verified | `OperatorSignoff`, `LiveCapitalEnablementRequest`, `LiveCapitalEnablementDecision`; `BrokerRuntimeStartupChecklist.from_config(..., live_capital_decision=...)`; `validate_live_startup(..., live_capital_request=...)`; `BrokerRuntimeReportWriter.write_manifest(..., live_capital_decision=...)`; runtime event `runtime.live_capital.signoff_decision` | None | `test_live_capital_requires_operator_and_risk_signoff`; `test_expired_signoff_blocks_live_orders`; `test_signoff_scope_blocks_unapproved_strategy`; `test_signoff_scope_blocks_unapproved_account`; `test_signoff_evidence_written_to_manifest_and_runtime_event` |
| M3.3 Require kill-switch drill before live capital | Complete / Verified | `scripts/drills/kill_switch_drill.py` writes `artifacts/drills/kill_switch/<run_id>/evidence.json`; `LiveCapitalReadinessDecision.from_kill_switch_drill_evidence(...)` consumes evidence | None | `test_kill_switch_blocks_new_orders`; `test_kill_switch_allows_safety_cancel`; `test_kill_switch_deactivation_requires_authorized_signoff`; `test_kill_switch_drill_evidence_required_for_live_capital` |
| M4.1 IBKR callback idempotency and out-of-order acceptance | Complete / Verified | `tests/unit/execution/test_ibkr_callback_idempotency.py`; `IbkrOrderExecutionAdapter`, `BrokerOrderMap`, callback quarantine, execution/commission normalization | None | `test_duplicate_order_status_is_idempotent`; `test_execution_before_open_order_is_quarantined_or_later_resolved`; `test_late_commission_updates_cost_without_duplicate_fill`; `test_duplicate_exec_id_applied_once`; `test_open_order_unknown_internal_order_quarantined`; `test_callback_account_mismatch_quarantined`; `test_reconnect_open_order_replay_is_idempotent` |
| M4.2 Reconnect requires reconciliation before orders resume | Complete / Verified | `tests/unit/runtime/test_reconnect_reconciliation_gate.py`; `RuntimeBrokerLifecycleCoordinator`; `BrokerReconnectReconciliation.resubscribe_market_data`; existing runtime/readiness reconnect tests | None | `test_disconnect_degrades_runtime_and_blocks_new_orders`; `test_reconnect_does_not_resume_orders_before_reconciliation`; `test_reconnect_resubscribes_market_data`; `test_reconnect_reconciles_open_orders_positions_cash`; `test_reconnect_with_drift_stays_degraded` |
| M4.3 Market-data permission/freshness final risk acceptance | Complete / Verified | `tests/unit/runtime/test_market_data_permission_freshness_acceptance.py`; `MarketDataPermissionRiskRule`, `MarketDataFreshnessRiskRule`, `RiskEngine`, runtime degraded/risk events | None | `test_live_market_data_permission_allows_order_when_fresh`; `test_delayed_market_data_rejects_live_order`; `test_delayed_frozen_market_data_rejects_live_order`; `test_frozen_market_data_rejects_live_order`; `test_unavailable_market_data_rejects_order`; `test_stale_market_data_rejects_order`; `test_market_data_rejection_emits_runtime_event_with_reason_code` |
| M5.1 RuntimeSession facade complexity budget | Complete / Verified | `RuntimeSessionComplexityRule`; `docs/architecture/runtime_session_complexity.md`; RuntimeSession forbidden IBKR transport/account mutation checks; public method budget currently within limit | None | `test_runtime_session_complexity_budget_passes`; `test_runtime_session_does_not_import_ibkr_transport`; `test_runtime_session_does_not_apply_account_mutation_directly` |
| M5.2 Coordinator keep / merge / delete audit | Complete / Verified | `docs/architecture/runtime_coordinator_decisions.md`; `RuntimeCoordinatorDecisionRule`; includes `BrokerRuntimeTopologyResolver`; deleted-coordinator import check | None | `test_every_runtime_coordinator_has_decision_record`; `test_deleted_coordinator_has_no_production_import`; `test_kept_coordinator_has_state_policy_or_evidence_responsibility` |
| M5.3 Class inventory and DTO / ValueObject budget | Complete / Verified | `artifacts/quality/class_inventory_baseline.json`; `ClassInventoryBudgetRule`; `SingleFieldDtoJustificationRule`; `DuplicateDtoNameRule`; focused quality tests | None | `test_class_inventory_does_not_exceed_platform_baseline_without_exception`; `test_single_field_dto_requires_boundary_justification`; `test_no_duplicate_dto_names_across_application_and_runtime` |
| M5.4 Remove old aliases, paths, and stale doc cache | Complete / Verified | `RemovedImportNoNewUsageRule`; `StaleArchitectureTextRule`; regenerated `project_panorama.html` and `backtest_live_parallel_sequence.html`; final alias/doc-cache tests | None | `test_removed_live_alias_imports_fail`; `test_panorama_source_index_uses_current_paths_only`; `test_archived_docs_are_not_used_as_current_inventory` |
| M6.1 Research run API | Complete / Verified | `BacktestService.submit`; `BacktestService.submit_batch`; `BacktestRunResultDTO`; `BacktestRunResultSchema`; manifest/artifact result projection | None | `test_research_backtest_submit_returns_manifest_and_artifacts`; `test_research_batch_submit_is_deterministic`; `test_research_code_cannot_access_runtime_actor_internals` |
| M6.2 Factor research contract | Complete / Verified | `docs/research/factor_contract_v1.md`; `qts.factors.Factor`, `FactorWindow`, `FactorResult`; deterministic/missing-data/ranking tests | None | `test_factor_has_name_and_version`; `test_factor_is_deterministic`; `test_factor_handles_missing_data_explicitly`; `test_factor_package_has_no_runtime_execution_broker_imports` |
| M6.3 Experiment manifest | Complete / Verified | `qts.research` experiment manifest writer; `artifacts/research/<experiment_id>/manifest.json`; artifact hash addressing | None | `test_experiment_manifest_contains_strategy_factor_dataset_versions`; `test_experiment_manifest_contains_platform_baseline_version`; `test_same_experiment_input_produces_same_config_hash`; `test_experiment_artifacts_are_addressable_by_hash` |
| Final platform closure | Complete / Verified | M0-M6 matrix, `make check`, `make test-replay`, `make test-reconciliation`, `make test-soak`, `readiness-smoke-local`, panorama/source inventory freshness, guardrails/readiness/golden/paper/quality gates | External broker/live observation anchors remain explicit environment gates and were not fabricated locally | `make check` plus M6 focused tests plus replay/reconciliation/soak/readiness-smoke-local |

## Parallel Execution Lanes

| Lane | Owner | Scope | Output |
| --- | --- | --- | --- |
| A | Main | M0/M1 matrix upkeep, evidence aggregation, final closure checklist | Matrix stays aligned to hard gates; no legacy compatibility debt |
| B | Worker 1 | M1.1 + M1.2 (runtime config renames and paper profile path) | Production code imports/signatures no longer use legacy live config naming |
| C | Worker 2 | M1.3 + M1.4 (event sink and order permission) | Canonical event sink and order permission naming and fields applied end-to-end |
| D | Worker 3 | M1.5 + M1.6 (recovery + risk config ownership) | Generic runtime recovery classes and single risk config ownership path enforced |
| E | Worker 4 | M3.1 (live order execution-boundary gate) | Real broker order submission cannot reach adapters unless all live-capital facts are true |
| F | Worker 5 | M3.2 (operator signoff and evidence) | Dual-control signoff model, expiry/scope enforcement, and manifest/runtime event evidence |
| G | Worker 6 | M3.3 (kill-switch drill and prerequisite evidence) | Drill script, evidence schema, and readiness gate proving kill switch behavior |
| H | Worker 7 | M4.1 (IBKR callback idempotency/out-of-order sequence) | Duplicate/out-of-order callback acceptance tests and adapter fixes |
| I | Worker 8 | M4.2 (reconnect reconciliation gate) | Disconnect/reconnect tests and runtime lifecycle fixes |
| J | Worker 9 | M4.3 (market-data permission/freshness risk acceptance) | Live-capable order risk tests and runtime evidence fixes |
| K | Worker 10 | M5.1 (RuntimeSession complexity facade gate) | Named tests and guardrail evidence proving facade budget and forbidden ownership checks |
| L | Worker 11 | M5.2 (coordinator decision audit) | `runtime_coordinator_decisions.md` and tests enforcing keep/merge/delete records |
| M | Worker 12 | M5.3 (class inventory and DTO budget) | Baseline artifact, class inventory guardrail, DTO/value-object tests |
| N | Worker 13 | M5.4 (removed aliases and stale docs) | Named removed-import/panorama/archive tests with no compatibility aliases |
| O | Worker 14 | M6.1 (research run API) | Stable `BacktestService` research result projection and deterministic batch tests |
| P | Worker 15 | M6.2 (factor research contract) | Versioned factor protocol/docs and deterministic/missing-data/import-boundary tests |
| Q | Worker 16 | M6.3 (experiment manifest) | Reproducible research experiment manifest writer and artifact hash tests |
| R | Main | Final platform closure | M0-M6 evidence aggregation, generated inventory refresh, full verification, and final status update |

## Current Execution Readiness

Current readiness for M0: 红线可达（verified）; Platform Final Baseline v1 evidence and freeze guardrails are covered by repository-wide verification.
Current readiness for M1: 红线可达（verified）; production legacy aliases and removed import paths are gone.
Current readiness for M2: 红线可达（verified / live observation remains environment-gated）; local backtest, paper simulated, and live observation no-order readiness evidence passed; external IBKR paper evidence is now validated by `make readiness-smoke-external`; external live observation anchors remain explicit environment gates.
Current readiness for M3: 红线可达（verified）; live-capital execution gating, dual-control signoff, and kill-switch drill evidence are implemented. Live capital remains disabled by default unless all M3 gates are simultaneously true.
Current readiness for M4: 红线可达（verified）; IBKR callback idempotency, reconnect reconciliation gating, and market-data permission/freshness acceptance have dedicated hard tests and repository-wide verification evidence.
Current readiness for M5: 红线可达（verified）; RuntimeSession facade budget, coordinator decisions, class inventory budget, DTO/value-object constraints, and stale alias/doc-cache gates have dedicated tests and repository-wide verification evidence.
Current readiness for M6: 红线可达（verified）; research run API, factor contract, and experiment manifest are implemented as research-facing boundaries only, with no runtime/broker compatibility aliases.
Current readiness for final platform closure: 红线可达（verified）; local final closure evidence passed. External broker/live observation anchors are still explicit environment gates, not locally fabricated evidence.

## Final Exit Conditions

| Exit Condition | Status | Evidence |
| --- | --- | --- |
| M0 Platform Final Baseline v1, manifest fields, and freeze guardrails | Complete / Verified | `make check`; `make guardrails`; platform baseline manifest/event tests |
| M1 naming freeze and runtime config convergence | Complete / Verified | Removed-import guardrails; runtime config/startup/session tests; `make check` |
| M2 backtest, paper simulated, IBKR paper broker, and live observation readiness suites | Complete / Verified for local + IBKR paper evidence; live observation Environment-Gated | `make test-replay`; `readiness-smoke-local`; `make readiness-smoke-external`; integration/anchor readiness tests; external live observation anchors remain explicit environment gates |
| M3 live capital hard gate and default-disabled live capital | Complete / Verified | Live capital execution/signoff/kill-switch tests; `make check` |
| M4 IBKR callback, reconnect, and market-data permission failure drills | Complete / Verified | Callback idempotency, reconnect reconciliation, and market-data permission/freshness tests; `make check` |
| M5 RuntimeSession, coordinator, class inventory, and DTO/value-object budgets | Complete / Verified | Complexity/class-inventory guardrails, source inventory tests, and `make guardrails` |
| M6 strategy/factor research API and experiment manifest | Complete / Verified | M6 focused tests; `qts.factors` contract; `qts.research` experiment manifest tests |
| CI includes guardrail, readiness, golden backtest, paper smoke, and quality budget | Complete / Verified | `make check`; `make test-replay`; `make test-reconciliation`; `make test-soak`; `readiness-smoke-local`; `make guardrails` |
| Latest architecture panorama has no stale paths or old aliases | Complete / Verified | Regenerated `project_panorama.html` and `docs/architecture/backtest_live_parallel_sequence.html`; panorama/source inventory tests |

## Verification Evidence

- `pytest tests/unit/runtime/test_live_capital_signoff.py tests/unit/runtime/test_live_capital_execution_gate.py tests/unit/execution/test_live_capital_adapter_gate.py tests/unit/scripts/test_kill_switch_drill.py -q` -> 18 passed.
- `make format` -> 502 files left unchanged.
- `make lint` -> passed.
- `make guardrails` -> Architecture guardrails passed.
- `make typecheck` -> Success: no issues found in 482 source files.
- `make check` -> format/lint/guardrails/typecheck passed; unit 808 passed; integration 77 passed, 4 skipped; anchor 39 passed, 2 skipped.
- `pytest tests/unit/execution/test_ibkr_callback_idempotency.py tests/unit/runtime/test_reconnect_reconciliation_gate.py tests/unit/runtime/test_market_data_permission_freshness_acceptance.py -q` -> 19 passed.
- `pytest tests/unit/runtime/test_runtime_session.py tests/integration/test_readiness_smoke_matrix.py -q` -> 39 passed.
- `pytest tests/quality/test_class_inventory_guardrails.py tests/unit/scripts/test_verify_guardrails.py tests/unit/test_project_panorama_html.py tests/unit/test_backtest_live_parallel_sequence_html.py -q` -> 92 passed.
- `pytest tests/unit/application tests/unit/factors tests/unit/research tests/integration/test_api_backtest_flow.py tests/unit/test_project_panorama_html.py tests/unit/test_backtest_live_parallel_sequence_html.py tests/quality/test_class_inventory_guardrails.py -q` -> 55 passed.
- `make format && make lint && make guardrails && make typecheck` -> format 511 files unchanged; lint passed; Architecture guardrails passed; mypy success on 491 source files.
- `make check` -> format/lint/guardrails/typecheck passed; unit 819 passed; integration 77 passed, 4 skipped; anchor 39 passed, 2 skipped.
- `make test-replay test-reconciliation test-soak readiness-smoke-local` -> replay 3 passed; reconciliation 1 passed; soak 4 passed, 1 skipped; local readiness smoke 9 passed.
- `make readiness-smoke-external` -> generated `readiness-smoke-paper_broker_gateway_market_data_anchor.json` and `readiness-smoke-paper_broker_submit_cancel_drill.json` from persisted complete `paper-full-chain-*` IBKR evidence; external readiness smoke validator 1 passed.
