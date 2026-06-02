"""Final-readiness gate for subsystem deferral ownership evidence."""

from __future__ import annotations

from pathlib import Path

from qts.quality.final_readiness import FinalReadinessRuleSet


def test_subsystem_deferrals_require_owner_use(tmp_path: Path) -> None:
    _write_minimal_repo(tmp_path)
    _write(
        tmp_path / "docs/plan/wiring_deferrals.md",
        """
```
qts.example.Component  expires=2027-08-30  target=subsystem
```
""",
    )

    violations = FinalReadinessRuleSet().check(tmp_path)

    assert {violation.code for violation in violations} >= {"FINAL_SUBSYSTEM_DEFERRAL_UNOWNED"}


def _write_minimal_repo(root: Path) -> None:
    _write(
        root / "backend/src/qts/application/commands/start_runtime.py",
        """
def start_runtime(command, session_registry):
    launch_plan_hash = command.launch_plan_hash
    RuntimeLaunchPlanStore = object
    RuntimeSessionKey = object
    session_registry.register(RuntimeSessionKey)
    if self.status == "started" and self.session is None:
        pass
    return launch_plan_hash
""",
    )
    _write(root / "backend/src/qts/api/routes/operations.py", "")
    _write(
        root / "backend/src/qts/research/orchestrator/validation_artifact_writer.py",
        "class ValidationArtifactWriter:\n    pass\n",
    )
    _write(root / "backend/src/qts/runtime/example.py", "")
    _write(root / "backend/src/qts/execution/example.py", "")
    _write(root / "backend/src/qts/risk/example.py", "")
    _write(root / "backend/src/qts/portfolio/example.py", "")
    _write(root / "docs/architecture/broker_adapters.md", "Canonical IBKR stack\n")
    _write(root / "docs/architecture/replay_data_flow.md", "Canonical replay flow\n")
    _write(root / "docs/architecture/reporting_boundary.md", "Machine artifacts\n")
    for violation in FinalReadinessRuleSet()._required_final_tests(root):
        _write(root / violation.path, "# required test\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip(), encoding="utf-8")
