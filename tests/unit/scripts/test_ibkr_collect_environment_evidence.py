from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, cast


def _load_collector_module() -> ModuleType:
    module_path = Path("scripts/ibkr_collect_environment_evidence.py")
    spec = importlib.util.spec_from_file_location("ibkr_collect_environment_evidence", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_dry_run_writes_observe_only_evidence_without_network(tmp_path: Path) -> None:
    collector = _load_collector_module()
    collect_environment_evidence = cast(Any, collector).collect_environment_evidence

    output_dir = tmp_path / "evidence" / "ibkr"

    evidence_path = collect_environment_evidence(
        config_path=Path("configs/live.ibkr.example.yaml"),
        output_dir=output_dir,
        dry_run=True,
        label="unit-test",
    )

    assert evidence_path.parent == output_dir
    assert evidence_path.name.endswith(".json")

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["collector"] == "ibkr_collect_environment_evidence"
    assert payload["dry_run"] is True
    assert payload["observe_only"] is True
    assert payload["orders_enabled"] is False
    assert payload["network_connection_attempted"] is False
    assert payload["order_actions_attempted"] == []
    assert payload["config"]["provider"] == "ibkr"
    assert payload["config"]["mode"] == "live"
    assert payload["config"]["market_data"]["client_id"] == 111
    assert payload["config"]["order_execution"]["client_id"] == 211
    assert payload["config"]["secrets"]["username_env"] == {
        "name": "IBKR_LIVE_USERNAME",
        "is_set": False,
    }
    assert "password" not in json.dumps(payload).lower()


def test_collector_module_exposes_no_order_placement_api() -> None:
    collector = _load_collector_module()

    forbidden_fragments = ("place_order", "submit_order", "cancel_order", "replace_order")

    public_names = [name for name in dir(collector) if not name.startswith("_")]
    assert not any(
        fragment in name.lower() for fragment in forbidden_fragments for name in public_names
    )
