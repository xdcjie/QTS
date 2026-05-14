from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    run_paper_order_lifecycle_drill,
)


def test_paper_drill_records_limit_order_cancel_and_execution_reports(
    tmp_path: Path,
) -> None:
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
    output_dir = tmp_path / "evidence" / "ibkr"

    with pytest.raises(ValueError, match="paper-only"):
        run_paper_order_lifecycle_drill(
            config_path=Path("configs/live.ibkr.example.yaml"),
            output_dir=output_dir,
        )

    assert not output_dir.exists()
