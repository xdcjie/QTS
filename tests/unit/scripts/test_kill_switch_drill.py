from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

from qts.runtime.live_capital import LiveCapitalReadinessDecision


def test_kill_switch_blocks_new_orders(tmp_path: Path) -> None:
    drill = _load_drill_module()

    evidence_path = drill.run_kill_switch_drill(
        output_root=tmp_path / "artifacts" / "drills" / "kill_switch",
        run_id="unit-kill-block",
    )

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert payload["steps"]["allowed_order"]["accepted"] is True
    assert payload["steps"]["new_order_after_kill_switch"]["accepted"] is False
    assert payload["steps"]["new_order_after_kill_switch"]["reason_code"] == "KILL_SWITCH_ACTIVE"
    assert payload["manifest"]["kill_switch_blocks_new_orders"] is True


def test_kill_switch_allows_safety_cancel(tmp_path: Path) -> None:
    drill = _load_drill_module()

    evidence_path = drill.run_kill_switch_drill(
        output_root=tmp_path / "artifacts" / "drills" / "kill_switch",
        run_id="unit-kill-cancel",
    )

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert payload["steps"]["safety_cancel"]["allowed"] is True
    assert payload["steps"]["safety_cancel"]["cancelled_order_ids"] == ["live-000001"]
    assert payload["manifest"]["kill_switch_allows_safety_cancel"] is True


def test_kill_switch_deactivation_requires_authorized_signoff(tmp_path: Path) -> None:
    drill = _load_drill_module()

    evidence_path = drill.run_kill_switch_drill(
        output_root=tmp_path / "artifacts" / "drills" / "kill_switch",
        run_id="unit-kill-deactivate",
    )

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert payload["steps"]["low_privilege_deactivate"]["accepted"] is False
    assert (
        payload["steps"]["low_privilege_deactivate"]["reason"]
        == "kill switch deactivate requires safety authorization"
    )
    assert payload["steps"]["authorized_deactivate"]["accepted"] is True
    assert payload["manifest"]["kill_switch_deactivation_requires_authorized_signoff"] is True


def test_kill_switch_drill_evidence_required_for_live_capital(tmp_path: Path) -> None:
    drill = _load_drill_module()
    missing_evidence_path = tmp_path / "artifacts" / "drills" / "kill_switch" / "missing.json"

    missing_decision = LiveCapitalReadinessDecision.from_kill_switch_drill_evidence(
        missing_evidence_path
    )
    assert missing_decision.ready is False
    assert missing_decision.reason_code == "KILL_SWITCH_DRILL_EVIDENCE_MISSING"

    evidence_path = drill.run_kill_switch_drill(
        output_root=tmp_path / "artifacts" / "drills" / "kill_switch",
        run_id="unit-live-capital-gate",
    )
    ready_decision = LiveCapitalReadinessDecision.from_kill_switch_drill_evidence(evidence_path)

    assert ready_decision.ready is True
    assert ready_decision.reason_code is None
    assert ready_decision.evidence_path == evidence_path


def _load_drill_module() -> ModuleType:
    module_path = Path("scripts/drills/kill_switch_drill.py")
    spec = importlib.util.spec_from_file_location("kill_switch_drill", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
