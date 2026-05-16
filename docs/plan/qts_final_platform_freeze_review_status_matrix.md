# QTS Final Platform Freeze M1 Review Status Matrix

Source backlog: `docs/plan/qts_final_platform_freeze_review_and_tasks.md`

Scope: M0 + M1 (Final naming and runtime-config convergence)

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

## M0 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Platform final baseline has a single canonical declaration and manifest/event owner | `docs/architecture/platform_final_baseline_v1.md`, reporting runtime manifest builders | Keeping multiple ad-hoc baseline constants or writing baseline only in one mode | M0.1 dedicated tests for backtest/broker/runtime event baseline version presence |
| Freeze policy is enforced on package boundaries, not documented only | `qts.quality` guardrail and `tests/quality/test_platform_freeze.py` | Copy-pasting a doc note while allowing production class additions | New `PlatformFreezeRule` with `tests/quality/test_platform_freeze.py` and CI `make guardrails` |
| Strategy/factor research code only depends on stable SDK surface | `StrategySdkPublicSurfaceRule`, SDK rules tests | Adding more forbidden symbols via exceptions or backdoors | Extended SDK surface rule + explicit import-ban tests for strategy/factor packages |
| Runtime naming matches runtime semantics, not environment labels | `qts.runtime.config`, `qts.runtime.permissions`, `qts.runtime.sinks`, `qts.runtime.state_recovery` | Using `Live*` names for broker-capable behavior, including paper and live observation paths | Per-task tests that assert canonical names and a no-legacy scan guardrail that fails CI |
| Risk profile ownership is by boundary and not duplicated | `qts.risk.config` and `qts.runtime.config` references only by id/profile-ref | Two differently-owned `RiskConfig` concepts in runtime and risk modules | Config model tests that bind runtime to a risk profile ref with shared validation |

## Status Matrix

| Task | Status | Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M0.1 Define `QTS Platform Final Baseline v1` | Complete | `docs/architecture/platform_final_baseline_v1.md`; `qts.reporting.base`, `qts.reporting.backtest`, `qts.reporting.broker_runtime`, `qts.runtime.sinks.base`; `test_backtest_manifest_contains_platform_baseline_version`, `test_broker_runtime_manifest_contains_platform_baseline_version`, `test_runtime_event_contains_platform_baseline_version` | None | Validate three new tests in `make test-unit` scope |
| M0.2 Add platform freeze class/namespace hard gate | Complete | `qts.quality` `PlatformFreezeRule`; `docs/architecture/platform_freeze_exceptions.yaml`; `tests/quality/test_platform_freeze.py`; `test_guardrail_suite_includes_required_m0_hard_gate_rules` | None | Add a temporary exception must have explicit `expiry`; expired or missing exception must fail |
| M0.3 Freeze strategy/factor public API dependency surface | Complete | `StrategySdkPublicSurfaceRule` (includes `qts.reconciliation`); `docs/research/strategy_factor_api_v1.md`; `test_strategy_package_cannot_import_runtime_internals`, `test_strategy_package_cannot_import_broker_transports`, `test_factor_package_has_no_runtime_dependency`, `test_factor_package_has_no_runtime_execution_broker_imports` | None | Blocked if any new strategy/factor public symbols/imports are added outside `qts.strategy_sdk` and `qts.factors` |
| M1.1 Rename `LiveRuntimeConfig` to `BrokerRuntimeConfig` | Not Started / Blocked | `backend/src/qts/runtime/config/models.py`; `backend/src/qts/runtime/broker_startup.py`; `backend/src/qts/runtime/topology.py`; `backend/src/qts/runtime/config/live.py` still reference `LiveRuntimeConfig` | Legacy naming still referenced in production and test code; no migration + deprecation strategy yet | First red gate: add CI test that rejects imports/references of `qts.runtime.config.LiveRuntimeConfig` outside explicit migration tests (currently none) |
| M1.2 Consolidate `PaperBrokerRuntimeConfig` | Not Started / Blocked | `backend/src/qts/runtime/config/paper.py` defines `PaperBrokerRuntimeConfig`; `backend/src/qts/runtime/config/__init__.py` exports it | Paper broker still has独立完整 config class instead of `BrokerRuntimeConfig(mode=PAPER_BROKER)` profile path | First red gate: class removed or renamed as profile-only object; tests must show paper broker config path uses broker-runtime config |
| M1.3 Rename `LiveRuntimeEventSink` | Not Started / Blocked | `backend/src/qts/runtime/sinks/live.py` still defines/class-exports `LiveRuntimeEventSink`; `backend/src/qts/runtime/sinks/__init__.py` re-exports it | File/path and symbol naming still live-specific; tests and integration still depend on legacy import path | First red gate: add guardrail test asserting no production import from `qts.runtime.sinks.live.LiveRuntimeEventSink` and enforce new sink symbol in source |
| M1.4 Rename `LiveOrderPermission` | Not Started / Blocked | `backend/src/qts/runtime/permissions.py` defines `LiveOrderPermission`; startup/permission tests still import it | Permission model naming still live-specific in runtime gates and manifests | First red gate: rename and migrate tests to `OrderSubmissionPermission`, plus gate test for `order_submission_permission` serialized field |
| M1.5 Rename `LiveReconciliation` / `LiveRecoveryDecision` | Not Started / Blocked | `backend/src/qts/runtime/live_reconciliation.py`, `backend/src/qts/runtime/state_recovery.py` use legacy class names; `backend/src/qts/runtime/durability.py`, startup/recovery call sites consume them | Recovery/reconciliation path still tied to legacy symbols across modules | First red gate: migration of runtime recovery call chain to `BrokerRuntimeReconciliation` and `RuntimeRecoveryDecision` with redacted legacy references removed |
| M1.6 Resolve `RiskConfig` duplicate concepts | Not Started / Blocked | `backend/src/qts/runtime/config/models.py` defines `RiskConfig`; `backend/src/qts/risk/config.py` also defines `RiskConfig` and runtime imports local one directly | Same name for different boundaries remains unresolved; ambiguity of ownership and evolution policy unresolved | First red gate: enforce single ownership model (`RiskProfileConfig` + profile ref in runtime) and remove boundary-conflicting duplicate concept naming |

## Parallel Execution Lanes

| Lane | Owner | Scope | Output |
| --- | --- | --- | --- |
| A | Main | M0/M1 matrix upkeep, evidence aggregation, final closure checklist | Matrix stays aligned to hard gates; no legacy compatibility debt |
| B | Worker 1 | M1.1 + M1.2 (runtime config renames and paper profile path) | Production code imports/signatures no longer use legacy live config naming |
| C | Worker 2 | M1.3 + M1.4 (event sink and order permission) | Canonical event sink and order permission naming and fields applied end-to-end |
| D | Worker 3 | M1.5 + M1.6 (recovery + risk config ownership) | Generic runtime recovery classes and single risk config ownership path enforced |

## Current Execution Readiness

Current readiness for M0: 红线可达（ready）; remaining work is full-suite CI verification (`make check`) and no-backward-compatibility closure sign-off.  
Current readiness for M1: 红线未达（blocked）; legacy names still in production and tests, so no-compatibility debt policy is not yet satisfied.
