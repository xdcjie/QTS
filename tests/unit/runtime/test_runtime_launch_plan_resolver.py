"""Runtime launch-plan resolver tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from qts.runtime.launch_plan import RuntimeLaunchPlan, RuntimeLaunchPlanStore
from qts.runtime.mode import RuntimeMode


def _plan() -> RuntimeLaunchPlan:
    return RuntimeLaunchPlan(
        promotion_candidate_id="pc-test",
        target_mode=RuntimeMode.PAPER_SIMULATED.value,
        strategy_id="strategy-test",
        source_module="tests.source",
        target_module="tests.target",
        idea_id="idea-test",
        evidence_bundle_id="evidence-test",
        runtime={"runtime_mode": "paper_simulated", "runtime_instance_id": "rt-test"},
        operations={"rollback_plan": "rollback"},
    )


def test_runtime_launch_plan_store_resolves_by_config_ref_and_hash(tmp_path: Path) -> None:
    store = RuntimeLaunchPlanStore(tmp_path)
    written = store.write(_plan())

    resolved = store.resolve(written.config_ref, expected_hash=written.content_hash)

    assert resolved.content_hash == written.content_hash
    assert resolved.config_ref == written.config_ref
    assert resolved.path == written.path
    assert resolved.plan.promotion_candidate_id == "pc-test"


def test_runtime_launch_plan_store_rejects_hash_mismatch(tmp_path: Path) -> None:
    store = RuntimeLaunchPlanStore(tmp_path)
    written = store.write(_plan())

    with pytest.raises(ValueError, match="does not match expected_hash"):
        store.resolve(
            written.config_ref,
            expected_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )


def test_runtime_launch_plan_store_rejects_missing_plan(tmp_path: Path) -> None:
    store = RuntimeLaunchPlanStore(tmp_path)

    with pytest.raises(FileNotFoundError):
        store.resolve(
            "launch-plan://missing/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            expected_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
