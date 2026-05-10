from __future__ import annotations

import importlib.util
import json
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest


def _load_drill_module() -> ModuleType:
    module_path = Path("scripts/ibkr_paper_order_lifecycle_drill.py")
    spec = importlib.util.spec_from_file_location("ibkr_paper_order_lifecycle_drill", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paper_drill_records_limit_order_cancel_and_execution_reports(
    tmp_path: Path,
) -> None:
    drill = _load_drill_module()
    run_paper_order_lifecycle_drill = cast(Any, drill).run_paper_order_lifecycle_drill

    output_dir = tmp_path / "evidence" / "ibkr"

    evidence_path = run_paper_order_lifecycle_drill(
        config_path=Path("configs/paper.ibkr.example.yaml"),
        output_dir=output_dir,
        label="unit-test",
        instrument_id="EQUITY.US.NASDAQ.AAPL",
        broker_symbol="AAPL",
        quantity=Decimal("1"),
        limit_price=Decimal("190.25"),
    )

    assert evidence_path.parent == output_dir
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    assert payload["collector"] == "ibkr_paper_order_lifecycle_drill"
    assert payload["paper_only"] is True
    assert payload["live_orders_enabled"] is False
    assert payload["config"]["provider"] == "ibkr"
    assert payload["config"]["mode"] == "paper"
    assert payload["config"]["account_id"] == "DU1234567"
    assert payload["order"]["order_type"] == "limit"
    assert payload["order"]["limit_price"] == "190.25"
    assert payload["order"]["quantity"] == "1"
    assert payload["supported_order_types"] == ["limit"]
    assert payload["order_status"] == {
        "created": "created",
        "sent": "sent",
        "accepted": "accepted",
    }
    assert payload["cancel_status"] == {
        "requested": "cancel_requested",
        "confirmed": "cancelled",
    }
    assert [report["status"] for report in payload["execution_reports"]] == [
        "accepted",
        "cancelled",
    ]
    assert all(report["filled_quantity"] == "0" for report in payload["execution_reports"])


def test_drill_rejects_live_config_without_writing_evidence(tmp_path: Path) -> None:
    drill = _load_drill_module()
    run_paper_order_lifecycle_drill = cast(Any, drill).run_paper_order_lifecycle_drill
    output_dir = tmp_path / "evidence" / "ibkr"

    with pytest.raises(ValueError, match="paper-only"):
        run_paper_order_lifecycle_drill(
            config_path=Path("configs/live.ibkr.example.yaml"),
            output_dir=output_dir,
        )

    assert not output_dir.exists()
