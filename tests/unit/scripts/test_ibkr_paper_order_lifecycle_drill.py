from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from qts.application.commands.ibkr_paper_order_lifecycle_drill import (
    DEFAULT_CONFIG_PATH,
    run_paper_order_lifecycle_drill,
)


def test_paper_drill_records_limit_order_cancel_and_execution_reports(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "evidence" / "ibkr"
    config_path = _write_paper_config(tmp_path / "paper-gateway.yaml")

    evidence_path = run_paper_order_lifecycle_drill(
        config_path=config_path,
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
    assert payload["config"]["account_id"] == "DUP1234567"
    assert payload["config"]["order_execution"]["port"] == 4002
    assert payload["order"]["order_type"] == "limit"
    assert payload["order"]["limit_price"] == "190.25"
    assert payload["order"]["quantity"] == "1"
    assert payload["order_identity"]["client_order_id"].startswith("client-")
    assert payload["order_identity"]["ibkr_order_id"] == "simulated-1"
    assert payload["order_identity"]["perm_id"] == "simulated-perm-1"
    assert payload["broker_order_map"]["restored"] is True
    assert payload["broker_order_map"]["snapshot"][0]["perm_id"] == "simulated-perm-1"
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
    assert payload["reconciliation"]["startup"]["trading_enabled"] is True
    assert payload["reconciliation"]["periodic"]["has_drift"] is False
    assert payload["commission_evidence"] == {
        "late_arrival_updates_cost": True,
        "duplicate_commission_does_not_duplicate_fill": True,
    }
    assert payload["manifest"]["submit_evidence"] is True
    assert payload["manifest"]["cancel_evidence"] is True
    assert payload["manifest"]["reconciliation_evidence"] is True


def test_drill_rejects_live_config_without_writing_evidence(tmp_path: Path) -> None:
    output_dir = tmp_path / "evidence" / "ibkr"

    with pytest.raises(ValueError, match="paper-only"):
        run_paper_order_lifecycle_drill(
            config_path=Path("configs/live.ibkr.example.yaml"),
            output_dir=output_dir,
        )

    assert not output_dir.exists()


def test_default_paper_drill_config_targets_paper_gateway(tmp_path: Path) -> None:
    evidence_path = run_paper_order_lifecycle_drill(
        config_path=DEFAULT_CONFIG_PATH,
        output_dir=tmp_path / "evidence",
        label="default-config",
    )

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert payload["config"]["order_execution"]["port"] == 4002
    assert payload["manifest"]["paper_port_guard"] is True


def test_drill_rejects_live_port_even_when_account_is_paper(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "paper-live-port.yaml"
    config_path.write_text(
        """
provider: ibkr
mode: paper
transport: official
connections:
  market_data:
    host: 127.0.0.1
    port: 4002
    client_id: 101
  order_execution:
    host: 127.0.0.1
    port: 4001
    client_id: 201
order_execution:
  account_id: DUP1234567
  risk_profile: paper-default
secrets:
  username_env: IBKR_PAPER_USERNAME
  password_env: IBKR_PAPER_PASSWORD
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / "evidence" / "ibkr"

    with pytest.raises(ValueError, match="paper Gateway port 4002"):
        run_paper_order_lifecycle_drill(
            config_path=config_path,
            output_dir=output_dir,
        )

    assert not output_dir.exists()


def test_drill_rejects_live_account_even_on_paper_port(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "paper-live-account.yaml"
    config_path.write_text(
        """
provider: ibkr
mode: paper
transport: official
connections:
  market_data:
    host: 127.0.0.1
    port: 4002
    client_id: 101
  order_execution:
    host: 127.0.0.1
    port: 4002
    client_id: 201
order_execution:
  account_id: DU1234567
  risk_profile: paper-default
secrets:
  username_env: IBKR_PAPER_USERNAME
  password_env: IBKR_PAPER_PASSWORD
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / "evidence" / "ibkr"

    with pytest.raises(ValueError, match="paper account id"):
        run_paper_order_lifecycle_drill(
            config_path=config_path,
            output_dir=output_dir,
        )

    assert not output_dir.exists()


def _write_paper_config(path: Path) -> Path:
    path.write_text(
        """
provider: ibkr
mode: paper
transport: official
connections:
  market_data:
    host: 127.0.0.1
    port: 4002
    client_id: 101
  order_execution:
    host: 127.0.0.1
    port: 4002
    client_id: 201
order_execution:
  account_id: DUP1234567
  risk_profile: paper-default
secrets:
  username_env: IBKR_PAPER_USERNAME
  password_env: IBKR_PAPER_PASSWORD
""",
        encoding="utf-8",
    )
    return path
