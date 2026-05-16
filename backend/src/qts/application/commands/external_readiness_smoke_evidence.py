"""Generate external readiness smoke evidence from verified IBKR paper artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

DEFAULT_EVIDENCE_DIR = Path("evidence/ibkr")
_FULL_CHAIN_PREFIX = "paper-full-chain-"
_REQUIRED_FULL_CHAIN_FLAGS = (
    "market_data",
    "non_marketable_cancel",
    "strategy_order",
    "submitted_via_runtime_session",
    "reconciliation_clean",
    "account_config_matches_gateway",
)
_SMOKE_NAMES = (
    "paper_broker_gateway_market_data_anchor",
    "paper_broker_submit_cancel_drill",
)


def generate_external_readiness_smoke_evidence(
    *,
    evidence_dir: Path = DEFAULT_EVIDENCE_DIR,
) -> tuple[Path, ...]:
    """Write readiness smoke wrappers for the newest complete paper full-chain evidence."""

    full_chain_path, payload = _newest_complete_full_chain_evidence(evidence_dir)
    event_path = _event_path_for_full_chain(full_chain_path)
    events = _read_event_rows(event_path)
    manifest_path = _path_from_payload(payload, "report_manifest")
    if not manifest_path.exists():
        raise ValueError(f"full-chain report manifest does not exist: {manifest_path}")

    timestamp = full_chain_path.stem.removeprefix(_FULL_CHAIN_PREFIX)
    run_id = f"ibkr-paper-full-chain-{timestamp}"
    generated: list[Path] = []
    for smoke_name in _SMOKE_NAMES:
        smoke_payload = {
            "schema_version": 1,
            "smoke_name": smoke_name,
            "run_id": run_id,
            "correlation_id": _correlation_id_for(smoke_name, events, payload),
            "manifest_path": str(manifest_path),
            "artifacts": {
                "events": {
                    "path": str(event_path),
                    "rows": len(events),
                    "sha256": _sha256_path(event_path),
                }
            },
            "source_evidence_path": str(full_chain_path),
            "source_evidence_sha256": _sha256_path(full_chain_path),
            "generated_at": payload.get("generated_at"),
            "gateway": payload.get("gateway"),
        }
        output_path = evidence_dir / f"readiness-smoke-{smoke_name}.json"
        output_path.write_text(
            json.dumps(smoke_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        generated.append(output_path)
    return tuple(generated)


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=DEFAULT_EVIDENCE_DIR,
        help="Directory containing paper-full-chain IBKR evidence.",
    )
    args = parser.parse_args()
    generated = generate_external_readiness_smoke_evidence(evidence_dir=args.evidence_dir)
    for path in generated:
        print(path)


def _newest_complete_full_chain_evidence(evidence_dir: Path) -> tuple[Path, JsonObject]:
    candidates = sorted(evidence_dir.glob(f"{_FULL_CHAIN_PREFIX}*.json"), reverse=True)
    for path in candidates:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if _is_complete_full_chain_payload(payload):
            return path, payload
    raise ValueError(f"no complete paper full-chain evidence found in {evidence_dir}")


def _is_complete_full_chain_payload(payload: JsonObject) -> bool:
    return all(bool(payload.get(flag)) for flag in _REQUIRED_FULL_CHAIN_FLAGS)


def _event_path_for_full_chain(full_chain_path: Path) -> Path:
    timestamp = full_chain_path.stem.removeprefix(_FULL_CHAIN_PREFIX)
    event_path = full_chain_path.with_name(f"paper-full-chain-events-{timestamp}.ndjson")
    if not event_path.exists():
        raise ValueError(f"full-chain event artifact does not exist: {event_path}")
    if event_path.stat().st_size <= 0:
        raise ValueError(f"full-chain event artifact is empty: {event_path}")
    return event_path


def _read_event_rows(event_path: Path) -> tuple[JsonObject, ...]:
    rows = tuple(
        json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines() if line
    )
    if not rows:
        raise ValueError(f"full-chain event artifact has no rows: {event_path}")
    return rows


def _path_from_payload(payload: JsonObject, key: str) -> Path:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"full-chain evidence missing {key}")
    return Path(value)


def _correlation_id_for(
    smoke_name: str,
    events: Iterable[JsonObject],
    payload: JsonObject,
) -> str:
    if smoke_name == "paper_broker_gateway_market_data_anchor":
        event_hash = _first_event_hash(events, kind="runtime.market_data")
        if event_hash is not None:
            return event_hash
    if smoke_name == "paper_broker_submit_cancel_drill":
        event_hash = _first_event_hash(events, kind="runtime.order_submitted")
        if event_hash is not None:
            return event_hash
        runtime_orders = payload.get("runtime_orders")
        if isinstance(runtime_orders, list) and runtime_orders:
            order_id = runtime_orders[0].get("order_id")
            if isinstance(order_id, str) and order_id:
                return order_id
    raise ValueError(f"cannot derive correlation_id for {smoke_name}")


def _first_event_hash(events: Iterable[JsonObject], *, kind: str) -> str | None:
    for event in events:
        if event.get("kind") != kind:
            continue
        event_hash = event.get("event_hash")
        if isinstance(event_hash, str) and event_hash:
            return event_hash
    return None


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"
