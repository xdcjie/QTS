# QTS Final Platform Freeze M0 Review Status Matrix

Source backlog: `docs/plan/qts_final_platform_freeze_review_and_tasks.md`

Scope: M0 only (Final platform freeze scope declaration)

Baseline: 2026-05-16

原则：本轮不引入 legacy path，不保留兼容历史债，不补齐兼容别名。  
任何出现旧命名、旧导入路径、历史兼容分支的实现都作为阻塞项处理。

## Completion Rules

M0 is complete only when all three tasks have hard gates that can fail CI:

- dedicated implementation + tests exist, and tests fail when legacy/compat paths are restored;
- manifests/events expose the required v1 platform baseline fields in all supported modes;
- exception mechanism is explicit and has expiry check.

## M0 Correctness Invariants

| Invariant | Correct owner / boundary | Forbidden shortcut | Required gate |
| --- | --- | --- | --- |
| Platform final baseline has a single canonical declaration and manifest/event owner | `docs/architecture/platform_final_baseline_v1.md`, reporting runtime manifest builders | Keeping multiple ad-hoc baseline constants or writing baseline only in one mode | M0.1 dedicated tests for backtest/broker/runtime event baseline version presence |
| Freeze policy is enforced on package boundaries, not documented only | `qts.quality` guardrail and `tests/quality/test_platform_freeze.py` | Copy-pasting a doc note while allowing production class additions | New `PlatformFreezeRule` with `tests/quality/test_platform_freeze.py` and CI `make guardrails` |
| Strategy/factor research code only depends on stable SDK surface | `StrategySdkPublicSurfaceRule`, SDK rules tests | Adding more forbidden symbols via exceptions or backdoors | Extended SDK surface rule + explicit import-ban tests for strategy/factor packages |

## Status Matrix

| Task | Status | Evidence Candidates | Blocking Gaps | First Red Gate |
| --- | --- | --- | --- | --- |
| M0.1 Define `QTS Platform Final Baseline v1` | Complete | `docs/architecture/platform_final_baseline_v1.md`; `qts.reporting.base`, `qts.reporting.backtest`, `qts.reporting.broker_runtime`, `qts.runtime.sinks.base`; `test_backtest_manifest_contains_platform_baseline_version`, `test_broker_runtime_manifest_contains_platform_baseline_version`, `test_runtime_event_contains_platform_baseline_version` | None | Validate three new tests in `make test-unit` scope |
| M0.2 Add platform freeze class/namespace hard gate | Complete | `qts.quality` `PlatformFreezeRule`; `docs/architecture/platform_freeze_exceptions.yaml`; `tests/quality/test_platform_freeze.py`; `test_guardrail_suite_includes_required_m0_hard_gate_rules` | None | Add a temporary exception must have explicit `expiry`; expired or missing exception must fail |
| M0.3 Freeze strategy/factor public API dependency surface | Complete | `StrategySdkPublicSurfaceRule` (includes `qts.reconciliation`); `docs/research/strategy_factor_api_v1.md`; `test_strategy_package_cannot_import_runtime_internals`, `test_strategy_package_cannot_import_broker_transports`, `test_factor_package_has_no_runtime_dependency`, `test_factor_package_has_no_runtime_execution_broker_imports` | None | Blocked if any new strategy/factor public symbols/imports are added outside `qts.strategy_sdk` and `qts.factors` |

## Parallel Execution Lanes

| Lane | Owner | Scope | Output |
| --- | --- | --- | --- |
| A | Main | M0 matrix maintenance, integration risk summary, final cross-check | Matrix updated with verifiable evidence; no legacy compatibility paths introduced |
| B | Worker 1 | M0.1 implementation tracking + manifest/event fields | Manifest schema diff, version constant usage, baseline-mode tests |
| C | Worker 2 | M0.2 guardrail rule + exception governance | `PlatformFreezeRule`, yaml exception contract, negative tests for missing expiry and missing permit |
| D | Worker 3 | M0.3 SDK surface tightening | `StrategySdkPublicSurfaceRule` expansion + strategy/factor import barrier tests |

## Current Execution Readiness

Current readiness for M0: 红线可达（ready）; remaining work is full-suite CI verification (`make check`) and no-backward-compatibility closure sign-off.
