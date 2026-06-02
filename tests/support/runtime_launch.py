"""Test support for final-state runtime launch plans."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qts.runtime.launch_plan import RuntimeLaunchPlan, RuntimeLaunchPlanStore
from qts.runtime.mode import RuntimeMode


@dataclass(frozen=True, slots=True)
class RuntimeLaunchFixture:
    """Materialized launch-plan evidence for start-runtime tests."""

    runtime_instance_id: str
    config_ref: str
    launch_plan_hash: str
    store: RuntimeLaunchPlanStore


def runtime_launch_fixture(
    tmp_path: Path,
    *,
    runtime_mode: RuntimeMode | str = RuntimeMode.PAPER_SIMULATED,
    runtime_instance_id: str = "runtime-test-1",
    candidate_id: str = "candidate-test",
) -> RuntimeLaunchFixture:
    """Materialize a minimal final-state launch plan for tests."""

    mode = RuntimeMode.from_value(runtime_mode)
    store = RuntimeLaunchPlanStore(tmp_path / "launch-plans")
    resolution = store.write(
        RuntimeLaunchPlan(
            promotion_candidate_id=candidate_id,
            target_mode=mode.value,
            strategy_id="strategy-test",
            source_module="tests.source_strategy",
            target_module="tests.target_strategy",
            idea_id="idea-test",
            evidence_bundle_id="evidence-test",
            runtime={
                "runtime_mode": mode.value,
                "runtime_instance_id": runtime_instance_id,
                "account_id": "acct-test",
                "capital_limit": "100000",
                "risk_profile_id": "risk-test",
            },
            operations={
                "rollback_plan": "test rollback",
                "monitoring_plan": "test monitoring",
            },
        )
    )
    return RuntimeLaunchFixture(
        runtime_instance_id=runtime_instance_id,
        config_ref=resolution.config_ref,
        launch_plan_hash=resolution.content_hash,
        store=store,
    )


__all__ = ["RuntimeLaunchFixture", "runtime_launch_fixture"]
