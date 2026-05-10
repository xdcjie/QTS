#!/usr/bin/env python
"""Collect observe-only IBKR environment evidence.

The collector records configuration and environment readiness evidence. It never
creates an order request and never sends order, cancel, or replace instructions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

JsonObject = dict[str, Any]

COLLECTOR_NAME = "ibkr_collect_environment_evidence"
DEFAULT_OUTPUT_DIR = Path("evidence/ibkr")
DEFAULT_CONFIG_PATH = Path("configs/live.ibkr.example.yaml")


def collect_environment_evidence(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
    label: str | None = None,
    timeout_seconds: float = 2.0,
) -> Path:
    """Write a JSON evidence file and return its path."""

    generated_at = datetime.now(UTC)
    config_payload = _read_config(config_path)
    validation_errors = _validate_ibkr_config(config_payload)
    network_evidence = _collect_network_evidence(
        config_payload,
        dry_run=dry_run,
        timeout_seconds=timeout_seconds,
    )

    evidence: JsonObject = {
        "schema_version": 1,
        "collector": COLLECTOR_NAME,
        "generated_at": generated_at.isoformat(),
        "dry_run": dry_run,
        "observe_only": True,
        "orders_enabled": False,
        "order_actions_attempted": [],
        "network_connection_attempted": not dry_run,
        "config_path": str(config_path),
        "config": _summarize_config(config_payload),
        "validation": {
            "status": "pass" if not validation_errors else "fail",
            "errors": validation_errors,
        },
        "network": network_evidence,
        "safety_guards": [
            "observe_only",
            "orders_enabled_false",
            "no_order_api",
            "secrets_redacted",
            "market_data_and_order_execution_separated",
        ],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / _evidence_filename(generated_at, label)
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="IBKR config YAML to summarize.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON evidence files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write evidence without opening any network connection.",
    )
    parser.add_argument(
        "--label",
        help="Optional filename label for the evidence file.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=2.0,
        help="TCP connectivity timeout when not running with --dry-run.",
    )
    args = parser.parse_args()

    evidence_path = collect_environment_evidence(
        config_path=args.config,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        label=args.label,
        timeout_seconds=args.timeout_seconds,
    )
    print(evidence_path)


def _read_config(config_path: Path) -> JsonObject:
    with config_path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return payload


def _summarize_config(config_payload: JsonObject) -> JsonObject:
    connections = _mapping(config_payload.get("connections"))
    market_data = _mapping(connections.get("market_data"))
    order_connection = _mapping(connections.get("order_execution"))
    order_execution = _mapping(config_payload.get("order_execution"))
    secrets = _mapping(config_payload.get("secrets"))

    username_env = str(secrets.get("username_env", ""))
    credential_env = str(secrets.get("password_env", ""))

    return {
        "mode": config_payload.get("mode"),
        "provider": config_payload.get("provider"),
        "market_data": {
            "host": market_data.get("host"),
            "port": market_data.get("port"),
            "client_id": market_data.get("client_id"),
            "source_id": market_data.get("source_id"),
        },
        "order_execution": {
            "host": order_connection.get("host"),
            "port": order_connection.get("port"),
            "client_id": order_connection.get("client_id"),
            "broker_id": order_connection.get("broker_id"),
            "account_id": order_execution.get("account_id"),
            "risk_profile": order_execution.get("risk_profile"),
        },
        "secrets": {
            "username_env": _env_ref_status(username_env),
            "credential_env": {
                "is_set": bool(credential_env and credential_env in os.environ),
                "name_redacted": True,
            },
        },
    }


def _validate_ibkr_config(config_payload: JsonObject) -> list[str]:
    errors: list[str] = []
    connections = _mapping(config_payload.get("connections"))
    market_data = _mapping(connections.get("market_data"))
    order_connection = _mapping(connections.get("order_execution"))
    order_execution = _mapping(config_payload.get("order_execution"))
    secrets = _mapping(config_payload.get("secrets"))

    if config_payload.get("provider") != "ibkr":
        errors.append("provider must be ibkr")
    if config_payload.get("mode") not in {"paper", "live"}:
        errors.append("mode must be paper or live")

    _validate_connection("market_data", market_data, errors)
    _validate_connection("order_execution", order_connection, errors)

    if market_data.get("client_id") == order_connection.get("client_id"):
        errors.append("market data and order execution client_id must be distinct")

    account_id = str(order_execution.get("account_id", ""))
    risk_profile = str(order_execution.get("risk_profile", ""))
    if not account_id.strip():
        errors.append("order_execution.account_id must not be empty")
    if not risk_profile.strip():
        errors.append("order_execution.risk_profile must not be empty")

    username_env = str(secrets.get("username_env", ""))
    credential_env = str(secrets.get("password_env", ""))
    if not username_env.strip():
        errors.append("secrets.username_env must not be empty")
    if not credential_env.strip():
        errors.append("credential secret env must not be empty")

    if config_payload.get("mode") == "live":
        if account_id.upper().startswith("DU"):
            errors.append("live mode cannot use a paper account")
        if "paper" in risk_profile.lower():
            errors.append("live mode cannot use a paper risk profile")
        if "PAPER" in username_env.upper() or "PAPER" in credential_env.upper():
            errors.append("live mode cannot use paper secret references")

    return errors


def _validate_connection(name: str, payload: JsonObject, errors: list[str]) -> None:
    host = str(payload.get("host", ""))
    port = payload.get("port")
    client_id = payload.get("client_id")

    if not host.strip():
        errors.append(f"{name}.host must not be empty")
    if not isinstance(port, int) or port <= 0:
        errors.append(f"{name}.port must be a positive integer")
    if not isinstance(client_id, int) or client_id <= 0:
        errors.append(f"{name}.client_id must be a positive integer")


def _collect_network_evidence(
    config_payload: JsonObject,
    *,
    dry_run: bool,
    timeout_seconds: float,
) -> JsonObject:
    if dry_run:
        return {
            "status": "skipped",
            "reason": "dry_run",
            "market_data": {"attempted": False},
            "order_execution": {"attempted": False},
        }

    connections = _mapping(config_payload.get("connections"))
    return {
        "status": "observed",
        "market_data": _tcp_probe(_mapping(connections.get("market_data")), timeout_seconds),
        "order_execution": _tcp_probe(
            _mapping(connections.get("order_execution")),
            timeout_seconds,
        ),
    }


def _tcp_probe(connection: JsonObject, timeout_seconds: float) -> JsonObject:
    host = str(connection.get("host", ""))
    port = connection.get("port")
    result: JsonObject = {
        "attempted": True,
        "host": host,
        "port": port,
        "connected": False,
    }

    if not host or not isinstance(port, int):
        result["error"] = "missing_host_or_port"
        return result

    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            result["connected"] = True
    except OSError as exc:
        result["error"] = exc.__class__.__name__
    return result


def _env_ref_status(env_name: str) -> JsonObject:
    return {
        "name": env_name,
        "is_set": bool(env_name and env_name in os.environ),
    }


def _mapping(value: Any) -> JsonObject:
    if isinstance(value, dict):
        return value
    return {}


def _evidence_filename(generated_at: datetime, label: str | None) -> str:
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label) if label else "environment"
    return f"{timestamp}_{safe_label}.json"


def _safe_label(label: str | None) -> str:
    if not label:
        return "environment"
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label.strip()).strip("-")
    return safe or "environment"


if __name__ == "__main__":
    main()
