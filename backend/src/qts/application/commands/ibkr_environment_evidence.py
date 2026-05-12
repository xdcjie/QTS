"""Application command to collect IBKR environment evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from qts.config.ibkr import (
    IbkrEnvironmentConfig,
    collect_validation_errors,
)

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
    """Collect observe-only evidence and return the output path."""

    generated_at = datetime.now(UTC)
    config, parse_errors = _read_config(config_path)
    validation_errors = _merge_validation_errors(parse_errors, config)
    network_evidence = _collect_network_evidence(
        config, dry_run=dry_run, timeout_seconds=timeout_seconds
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
        "config": _summarize_config(config),
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
    """CLI entrypoint for IBKR environment evidence collection."""

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

    path = collect_environment_evidence(
        config_path=args.config,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        label=args.label,
        timeout_seconds=args.timeout_seconds,
    )
    print(path)


def _read_config(
    config_path: Path,
) -> tuple[IbkrEnvironmentConfig | None, list[str]]:
    """Perform _read_config."""
    try:
        return IbkrEnvironmentConfig.from_yaml(config_path), []
    except ValueError as exc:
        return None, [str(exc)]


def _summarize_config(config: IbkrEnvironmentConfig | None) -> JsonObject:
    """Perform _summarize_config."""
    if config is None:
        return {}

    market_data = config.market_data
    order_execution = config.order_execution
    secrets = config.secrets

    return {
        "provider": "ibkr",
        "mode": config.mode,
        "market_data": {
            "host": market_data.host,
            "port": market_data.port,
            "client_id": market_data.client_id,
            "source_id": market_data.source_id,
        },
        "order_execution": {
            "host": order_execution.host,
            "port": order_execution.port,
            "client_id": order_execution.client_id,
            "broker_id": order_execution.broker_id,
            "account_id": order_execution.account_id,
            "risk_profile": order_execution.risk_profile,
        },
        "secrets": {
            "username_env": _env_ref_status(secrets.username_env),
            "credential_env": {
                "is_set": bool(secrets.password_env and secrets.password_env in os.environ),
                "name_redacted": True,
            },
        },
    }


def _merge_validation_errors(
    parse_errors: list[str],
    config: IbkrEnvironmentConfig | None,
) -> list[str]:
    """Perform _merge_validation_errors."""
    if parse_errors:
        return parse_errors
    if config is None:
        return ["configuration is not readable"]
    return collect_validation_errors(config)


def _collect_network_evidence(
    config: IbkrEnvironmentConfig | None,
    *,
    dry_run: bool,
    timeout_seconds: float,
) -> JsonObject:
    """Perform _collect_network_evidence."""
    if config is None:
        return {
            "status": "skipped",
            "reason": "invalid_configuration",
            "market_data": {"attempted": False},
            "order_execution": {"attempted": False},
        }

    if dry_run:
        return {
            "status": "skipped",
            "reason": "dry_run",
            "market_data": {"attempted": False},
            "order_execution": {"attempted": False},
        }

    market_data = config.market_data
    order_execution = config.order_execution
    return {
        "status": "observed",
        "market_data": _tcp_probe(
            {
                "host": market_data.host,
                "port": market_data.port,
            },
            timeout_seconds,
        ),
        "order_execution": _tcp_probe(
            {
                "host": order_execution.host,
                "port": order_execution.port,
            },
            timeout_seconds,
        ),
    }


def _tcp_probe(connection: JsonObject, timeout_seconds: float) -> JsonObject:
    """Perform _tcp_probe."""
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
        with socket.create_connection((host, port), timeout=timeout_seconds) as sock:
            sock.close()
        result["connected"] = True
        result["error"] = None
    except OSError as exc:
        result["error"] = str(exc)
    return result


def _env_ref_status(name: str) -> JsonObject:
    """Perform _env_ref_status."""
    return {"name": name, "is_set": bool(name and name in os.environ)}


def _evidence_filename(generated_at: datetime, label: str | None) -> str:
    """Perform _evidence_filename."""
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label) if label else "environment_evidence"
    return f"{timestamp}_{safe_label}.json"


def _safe_label(label: str | None) -> str:
    """Perform _safe_label."""
    if not label:
        return "environment_evidence"
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label.strip()).strip("-")
    return safe or "environment_evidence"


__all__ = ["collect_environment_evidence", "main"]
