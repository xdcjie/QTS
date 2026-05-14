from __future__ import annotations

import json
from pathlib import Path

from qts.application.commands.ibkr_environment_evidence import collect_environment_evidence


def test_dry_run_writes_observe_only_evidence_without_network(tmp_path: Path) -> None:
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


def test_collector_command_module_exposes_no_order_placement_api() -> None:
    import qts.application.commands.ibkr_environment_evidence as collector

    forbidden_fragments = ("place_order", "submit_order", "cancel_order", "replace_order")

    public_names = [name for name in dir(collector) if not name.startswith("_")]
    assert not any(
        fragment in name.lower() for fragment in forbidden_fragments for name in public_names
    )


def test_evidence_records_separate_gateway_targets_and_secret_statuses(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "paper.ibkr.local.yaml"
    config_path.write_text(
        """
mode: paper
provider: ibkr
observe_only: true

connections:
  market_data:
    host: 127.0.0.1
    port: 4002
    client_id: 101
    source_id: ibkr-paper-md
  order_execution:
    host: 127.0.0.1
    port: 4002
    client_id: 201
    broker_id: IBKR

order_execution:
  account_id: DU1234567
  risk_profile: paper-default

secrets:
  username_env: IBKR_PAPER_USERNAME
  password_env: IBKR_PAPER_PASSWORD
""",
        encoding="utf-8",
    )

    evidence_path = collect_environment_evidence(
        config_path=config_path,
        output_dir=tmp_path / "evidence",
        dry_run=True,
        label="paper-gateway-4002",
    )

    payload = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert payload["observe_only"] is True
    assert payload["orders_enabled"] is False
    assert payload["config"]["mode"] == "paper"
    assert payload["config"]["observe_only"] is True
    assert payload["config"]["account_classification"] == "paper"
    assert payload["config"]["gateway_targets"] == {
        "market_data": {
            "host": "127.0.0.1",
            "port": 4002,
            "client_id": 101,
        },
        "order_execution": {
            "host": "127.0.0.1",
            "port": 4002,
            "client_id": 201,
        },
    }
    assert payload["network"]["market_data"]["attempted"] is False
    assert payload["network"]["order_execution"]["attempted"] is False
    assert payload["config"]["secrets"]["credential_env"]["name_redacted"] is True
    assert "IBKR_PAPER_PASSWORD" not in json.dumps(payload)
