#!/usr/bin/env python
"""Run a paper-only IBKR order lifecycle drill.

The drill uses the internal fake broker boundary and records order lifecycle
evidence for a limit order. It has no live-mode option and refuses live config.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from qts.core.ids import AccountId, BrokerId, InstrumentId, OrderId, StrategyId
from qts.domain.risk import RiskDecision
from qts.execution.broker import (
    BrokerOrderRequest,
    FakeBrokerAdapter,
    normalize_broker_execution_report,
)
from qts.execution.order_manager import CancelIntent, OrderIntent, OrderManager, OrderSide

JsonObject = dict[str, Any]

COLLECTOR_NAME = "ibkr_paper_order_lifecycle_drill"
DEFAULT_CONFIG_PATH = Path("configs/paper.ibkr.example.yaml")
DEFAULT_OUTPUT_DIR = Path("evidence/ibkr")


def run_paper_order_lifecycle_drill(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    label: str | None = None,
    instrument_id: str = "EQUITY.US.NASDAQ.AAPL",
    broker_symbol: str = "AAPL",
    side: str = "buy",
    quantity: Decimal = Decimal("1"),
    limit_price: Decimal = Decimal("1"),
) -> Path:
    """Run a paper-only limit-order lifecycle drill and write JSON evidence."""

    if quantity <= Decimal("0"):
        raise ValueError("quantity must be positive")
    if limit_price <= Decimal("0"):
        raise ValueError("limit_price must be positive")

    config_payload = _read_config(config_path)
    _validate_paper_only_ibkr_config(config_payload)

    generated_at = datetime.now(UTC)
    order_id = OrderId(f"paper-drill-{generated_at.strftime('%Y%m%d%H%M%S')}")
    account_id = AccountId(_account_id(config_payload))
    instrument = InstrumentId(instrument_id)
    order_side = OrderSide(side)

    manager = OrderManager()
    broker = FakeBrokerAdapter(broker_id=BrokerId("IBKR-PAPER"))
    intent = OrderIntent(
        order_id=order_id,
        instrument_id=instrument,
        side=order_side,
        quantity=quantity,
    )

    created = manager.create_order(
        intent,
        risk_decision=RiskDecision.approve(rule_id="paper_order_lifecycle_drill"),
    )
    broker_request = BrokerOrderRequest(
        order_id=order_id,
        account_id=account_id,
        strategy_id=StrategyId("paper-order-lifecycle-drill"),
        instrument_id=instrument,
        side=order_side,
        quantity=quantity,
    )
    accepted_broker_report = broker.submit_order(broker_request)
    sent = manager.mark_sent(order_id, broker_order_id=accepted_broker_report.broker_order_id)
    accepted_report = normalize_broker_execution_report(accepted_broker_report)
    accepted_result = manager.process_report(accepted_report)

    cancel_requested = manager.request_cancel(
        CancelIntent(order_id=order_id, reason="paper lifecycle drill")
    )
    cancelled_broker_report = broker.cancel_order(order_id)
    cancelled_report = normalize_broker_execution_report(cancelled_broker_report)
    cancelled_result = manager.process_report(cancelled_report)

    evidence: JsonObject = {
        "schema_version": 1,
        "collector": COLLECTOR_NAME,
        "generated_at": generated_at.isoformat(),
        "paper_only": True,
        "live_orders_enabled": False,
        "config_path": str(config_path),
        "config": _summarize_config(config_payload),
        "supported_order_types": ["limit"],
        "order": {
            "order_id": order_id.value,
            "instrument_id": instrument.value,
            "broker_symbol": broker_symbol,
            "side": order_side.value,
            "quantity": str(quantity),
            "order_type": "limit",
            "limit_price": str(limit_price),
            "time_in_force": "day",
            "account_id": account_id.value,
        },
        "order_status": {
            "created": created.state.value,
            "sent": sent.state.value,
            "accepted": accepted_result.order.state.value,
        },
        "cancel_status": {
            "requested": cancel_requested.state.value,
            "confirmed": cancelled_result.order.state.value,
        },
        "execution_reports": [
            _execution_report_evidence(accepted_report),
            _execution_report_evidence(cancelled_report),
        ],
        "safety_guards": [
            "paper_config_required",
            "live_orders_enabled_false",
            "limit_orders_only",
            "fake_broker_boundary",
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
        help="Paper IBKR config YAML.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON evidence files.",
    )
    parser.add_argument("--label", help="Optional filename label for the evidence file.")
    parser.add_argument(
        "--instrument-id",
        default="EQUITY.US.NASDAQ.AAPL",
        help="Internal instrument id to use for the paper drill.",
    )
    parser.add_argument(
        "--broker-symbol",
        default="AAPL",
        help="Broker symbol to record in paper evidence.",
    )
    parser.add_argument("--side", choices=[item.value for item in OrderSide], default="buy")
    parser.add_argument("--quantity", type=Decimal, default=Decimal("1"))
    parser.add_argument("--limit-price", type=Decimal, default=Decimal("1"))
    args = parser.parse_args()

    evidence_path = run_paper_order_lifecycle_drill(
        config_path=args.config,
        output_dir=args.output_dir,
        label=args.label,
        instrument_id=args.instrument_id,
        broker_symbol=args.broker_symbol,
        side=args.side,
        quantity=args.quantity,
        limit_price=args.limit_price,
    )
    print(evidence_path)


def _read_config(config_path: Path) -> JsonObject:
    with config_path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping")
    return payload


def _validate_paper_only_ibkr_config(config_payload: JsonObject) -> None:
    errors: list[str] = []
    if config_payload.get("provider") != "ibkr":
        errors.append("provider must be ibkr")
    if config_payload.get("mode") != "paper":
        errors.append("paper-only drill requires mode=paper")
    if not _account_id(config_payload).upper().startswith("DU"):
        errors.append("paper-only drill requires a paper account id")

    connections = _mapping(config_payload.get("connections"))
    market_data = _mapping(connections.get("market_data"))
    order_execution = _mapping(connections.get("order_execution"))
    if market_data.get("client_id") == order_execution.get("client_id"):
        errors.append("market data and order execution client_id must be distinct")

    if errors:
        raise ValueError("; ".join(errors))


def _summarize_config(config_payload: JsonObject) -> JsonObject:
    connections = _mapping(config_payload.get("connections"))
    order_connection = _mapping(connections.get("order_execution"))
    return {
        "provider": config_payload.get("provider"),
        "mode": config_payload.get("mode"),
        "account_id": _account_id(config_payload),
        "order_execution": {
            "host": order_connection.get("host"),
            "port": order_connection.get("port"),
            "client_id": order_connection.get("client_id"),
            "broker_id": order_connection.get("broker_id"),
        },
    }


def _execution_report_evidence(report: object) -> JsonObject:
    from qts.execution.order_manager import ExecutionReport

    if not isinstance(report, ExecutionReport):
        raise TypeError("report must be an ExecutionReport")
    return {
        "report_id": report.report_id,
        "broker_order_id": report.broker_order_id,
        "status": report.status.value,
        "filled_quantity": str(report.filled_quantity),
        "fill_price": str(report.fill_price) if report.fill_price is not None else None,
        "fill_id": report.fill_id,
    }


def _account_id(config_payload: JsonObject) -> str:
    return str(_mapping(config_payload.get("order_execution")).get("account_id", ""))


def _mapping(value: Any) -> JsonObject:
    if isinstance(value, dict):
        return value
    return {}


def _evidence_filename(generated_at: datetime, label: str | None) -> str:
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label) if label else "paper_order_lifecycle_drill"
    return f"{timestamp}_{safe_label}.json"


def _safe_label(label: str | None) -> str:
    if not label:
        return "paper_order_lifecycle_drill"
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label.strip()).strip("-")
    return safe or "paper_order_lifecycle_drill"


if __name__ == "__main__":
    main()
