"""Application command to execute a paper IBKR order lifecycle evidence drill."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.config.ibkr import IbkrEnvironmentConfig, collect_validation_errors
from qts.core.ids import AccountId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import CancelIntent, ExecutionReport, OrderIntent, OrderSide
from qts.domain.risk import RiskDecision
from qts.execution.broker import BrokerOrderRequest, normalize_broker_execution_report
from qts.execution.order_manager import OrderManager
from qts.simulation.broker import SimulatedBrokerAdapter

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
    """Run a paper-only order-lifecycle drill and persist evidence."""

    if quantity <= Decimal("0"):
        raise ValueError("quantity must be positive")
    if limit_price <= Decimal("0"):
        raise ValueError("limit_price must be positive")

    config, parse_errors = _read_config(config_path)
    _validate_paper_only_ibkr_config(config, parse_errors)

    generated_at = datetime.now(UTC)
    order_id = OrderId(f"paper-drill-{generated_at.strftime('%Y%m%d%H%M%S')}")
    assert config is not None
    account_id = AccountId(config.order_execution.account_id)
    instrument = InstrumentId(instrument_id)
    order_side = OrderSide(side)

    manager = OrderManager()
    broker = SimulatedBrokerAdapter()
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
        client_order_id=f"client-{order_id.value}",
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
        "config": _summarize_config(config),
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
    """CLI entrypoint for paper order lifecycle evidence."""

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

    path = run_paper_order_lifecycle_drill(
        config_path=args.config,
        output_dir=args.output_dir,
        label=args.label,
        instrument_id=args.instrument_id,
        broker_symbol=args.broker_symbol,
        side=args.side,
        quantity=args.quantity,
        limit_price=args.limit_price,
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


def _validate_paper_only_ibkr_config(
    config: IbkrEnvironmentConfig | None,
    parse_errors: list[str],
) -> None:
    """Perform _validate_paper_only_ibkr_config."""
    errors: list[str] = []
    if parse_errors:
        errors.extend(parse_errors)
        raise ValueError("; ".join(errors))
    if config is None:
        errors.append("configuration is not readable")
        raise ValueError("; ".join(errors))

    if config.mode != "paper":
        errors.append("paper-only drill requires mode=paper")

    if not config.order_execution.account_id.upper().startswith("DU"):
        errors.append("paper-only drill requires a paper account id")

    errors.extend(collect_validation_errors(config))
    if errors:
        raise ValueError("; ".join(errors))


def _summarize_config(config: IbkrEnvironmentConfig) -> JsonObject:
    """Perform _summarize_config."""
    order_execution = config.order_execution
    return {
        "provider": "ibkr",
        "mode": config.mode,
        "account_id": order_execution.account_id,
        "order_execution": {
            "host": order_execution.host,
            "port": order_execution.port,
            "client_id": order_execution.client_id,
            "broker_id": order_execution.broker_id,
        },
    }


def _execution_report_evidence(report: ExecutionReport) -> JsonObject:
    """Perform _execution_report_evidence."""
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


def _evidence_filename(generated_at: datetime, label: str | None) -> str:
    """Perform _evidence_filename."""
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label) if label else "paper_order_lifecycle_drill"
    return f"{timestamp}_{safe_label}.json"


def _safe_label(label: str | None) -> str:
    """Perform _safe_label."""
    if not label:
        return "paper_order_lifecycle_drill"
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label.strip()).strip("-")
    return safe or "paper_order_lifecycle_drill"


__all__ = ["run_paper_order_lifecycle_drill", "main"]
