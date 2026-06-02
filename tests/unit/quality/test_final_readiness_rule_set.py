"""Final-readiness rule-set tests."""

from __future__ import annotations

from pathlib import Path

from qts.quality.final_readiness import FinalReadinessRuleSet
from qts.quality.guardrails import GuardrailViolation


def test_final_readiness_rule_set_accepts_minimal_clean_repo(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)

    assert FinalReadinessRuleSet().check(tmp_path) == []


def test_final_readiness_rejects_production_wiring_deferral(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)
    _write(
        tmp_path / "docs/plan/wiring_deferrals.md",
        """
```
qts.example.Example  expires=2026-08-30  target=production
```
""",
    )

    codes = _codes(FinalReadinessRuleSet().check(tmp_path))
    assert "FINAL_PRODUCTION_WIRING_DEFERRAL" in codes


def test_final_readiness_rejects_validation_writer_verdict_formula(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)
    _write(
        tmp_path / "backend/src/qts/research/orchestrator/validation_artifact_writer.py",
        """
class ValidationArtifactWriter:
    def _walk_forward_validation_payload(self):
        accepted = True
        return {"consistent": accepted, "test_windows": [{"accepted": accepted}]}
""",
    )

    codes = _codes(FinalReadinessRuleSet().check(tmp_path))
    assert "FINAL_VALIDATION_WRITER_VERDICT" in codes


def test_final_readiness_rejects_unbounded_actor_ask(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)
    _write(
        tmp_path / "backend/src/qts/runtime/example.py",
        """
def f(ref, query):
    return ref.ask(query, ask_timeout=None)
""",
    )

    codes = _codes(FinalReadinessRuleSet().check(tmp_path))
    assert "FINAL_ACTOR_ASK_UNBOUNDED" in codes


def test_final_readiness_rejects_backtest_named_shared_cost_model(tmp_path: Path) -> None:
    _write_clean_repo(tmp_path)
    _write(
        tmp_path / "backend/src/qts/application/service.py",
        """
from qts.runtime.config import BacktestCostModel
""",
    )

    codes = _codes(FinalReadinessRuleSet().check(tmp_path))
    assert "FINAL_BACKTEST_NAMED_SHARED_COST_MODEL" in codes


def _write_clean_repo(root: Path) -> None:
    _write(
        root / "docs/plan/wiring_deferrals.md",
        """
```
qts.example.Library  expires=2027-08-30  target=library
```
""",
    )
    _write(
        root / "backend/src/qts/application/commands/start_runtime.py",
        """
class RuntimeStartResult:
    def __post_init__(self):
        if self.status == "started" and self.session is None:
            raise ValueError("started requires a RuntimeSession")

def start_runtime(session_registry, command):
    RuntimeLaunchPlanStore = object
    launch_plan_hash = command.launch_plan_hash
    RuntimeSessionKey = object
    session_registry.register(RuntimeSessionKey)
    return launch_plan_hash
""",
    )
    _write(
        root / "backend/src/qts/api/routes/operations.py",
        """
class RuntimeCommandResultResponseSchema:
    pass

@router.post("/runtime/pause", response_model=RuntimeCommandResultResponseSchema)
def pause_runtime():
    pass
""",
    )
    _write(
        root / "backend/src/qts/research/orchestrator/validation_artifact_writer.py",
        """
class ValidationArtifactWriter:
    def _walk_forward_validation_payload(self):
        return WalkForwardValidationArtifact().payload()
""",
    )
    _write(root / "backend/src/qts/runtime/example.py", "def f():\n    return None\n")
    _write(root / "backend/src/qts/execution/example.py", "def f():\n    return None\n")
    _write(root / "backend/src/qts/risk/example.py", "def f():\n    return None\n")
    _write(root / "backend/src/qts/portfolio/example.py", "def f():\n    return None\n")
    for required in (
        "tests/integration/test_catalog_futures_margin_enforced.py",
        "tests/integration/test_operator_command_targets_registered_runtime.py",
        "tests/integration/test_operations_unbound_lifecycle_returns_rejected.py",
        "tests/integration/test_promotion_to_paper_runtime_config.py",
        "tests/anchor/test_runtime_start_requires_launch_plan_hash.py",
        "tests/anchor/test_multi_account_final_readiness_gate.py",
        "tests/unit/research/orchestrator/test_walk_forward_validation_artifact.py",
        "tests/unit/quality/test_final_readiness_rule_set.py",
    ):
        _write(root / required, "# required final-readiness test\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8")


def _codes(violations: list[GuardrailViolation]) -> set[str]:
    return {str(violation.code) for violation in violations}
