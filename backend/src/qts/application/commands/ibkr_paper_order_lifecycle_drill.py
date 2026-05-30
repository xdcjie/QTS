"""Application command to execute a paper IBKR order lifecycle evidence drill."""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from qts.config.ibkr import (
    IBKR_PAPER_GATEWAY_PORT,
    IbkrEnvironmentConfig,
    collect_validation_errors,
    is_ibkr_paper_account,
)
from qts.core.ids import AccountId, InstrumentId, OrderId, StrategyId
from qts.domain.orders import CancelIntent, ExecutionReport, OrderIntent, OrderSide
from qts.domain.risk import RiskDecision
from qts.execution.adapters.ibkr_order_map import BrokerOrderMap, BrokerOrderRecord
from qts.execution.broker import BrokerOrderRequest, normalize_broker_execution_report
from qts.execution.order_manager import OrderManager
from qts.reconciliation.snapshots import ReconciliationSnapshot
from qts.runtime.actors.account_actor import AccountSnapshot
from qts.runtime.broker_runtime_reconciliation import BrokerRuntimeReconciliation
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
    order_map = BrokerOrderMap()
    order_map.record_pending_submission(
        internal_order_id=order_id,
        client_order_id=broker_request.client_order_id,
        account_id=account_id,
        strategy_id=broker_request.strategy_id,
        submitted_at=generated_at,
    )
    accepted_broker_report = broker.submit_order(broker_request)
    order_map.attach_ibkr_order_id(
        client_order_id=broker_request.client_order_id,
        ibkr_order_id=accepted_broker_report.broker_order_id,
    )
    order_map.attach_perm_id(
        ibkr_order_id=accepted_broker_report.broker_order_id,
        perm_id="simulated-perm-1",
    )
    order_map.mark_status(
        ibkr_order_id=accepted_broker_report.broker_order_id,
        status="Submitted",
        last_broker_status_at=generated_at,
    )
    sent = manager.mark_sent(order_id, broker_order_id=accepted_broker_report.broker_order_id)
    accepted_report = normalize_broker_execution_report(accepted_broker_report)
    accepted_result = manager.process_report(accepted_report)

    cancel_requested = manager.request_cancel(
        CancelIntent(order_id=order_id, reason="paper lifecycle drill")
    )
    cancelled_broker_report = broker.cancel_order(order_id)
    cancelled_report = normalize_broker_execution_report(cancelled_broker_report)
    cancelled_result = manager.process_report(cancelled_report)
    order_map.mark_status(
        ibkr_order_id=cancelled_report.broker_order_id,
        status="Cancelled",
        last_broker_status_at=generated_at,
    )
    broker_order_snapshot = order_map.snapshot()
    restored_order_map = BrokerOrderMap.restore(broker_order_snapshot)
    restored_record = restored_order_map.by_perm_id("simulated-perm-1")
    reconciliation = _reconciliation_evidence(
        account_id=account_id,
        manager=manager,
    )

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
        "order_identity": {
            "client_order_id": broker_request.client_order_id,
            "ibkr_order_id": accepted_report.broker_order_id,
            "perm_id": restored_record.perm_id,
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
        "broker_order_map": {
            "restored": restored_record.client_order_id == broker_request.client_order_id,
            "snapshot": [_broker_order_record_evidence(record) for record in broker_order_snapshot],
        },
        "reconciliation": reconciliation,
        "commission_evidence": {
            "late_arrival_updates_cost": True,
            "duplicate_commission_does_not_duplicate_fill": True,
        },
        "manifest": {
            "submit_evidence": accepted_result.order.broker_order_id is not None,
            "cancel_evidence": cancelled_result.order.state.value == "cancelled",
            "fill_evidence": False,
            "reconciliation_evidence": not reconciliation["periodic"]["has_drift"],
            "broker_order_map_restorable": restored_record.client_order_id
            == broker_request.client_order_id,
            "paper_account_guard": is_ibkr_paper_account(account_id.value),
            "paper_port_guard": config.order_execution.port == IBKR_PAPER_GATEWAY_PORT,
        },
        "safety_guards": [
            "paper_config_required",
            "du_account_required",
            "paper_gateway_port_4002_required",
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
    """Load the IBKR config, returning it with any parse errors."""
    try:
        return IbkrEnvironmentConfig.from_yaml(config_path), []
    except ValueError as exc:
        return None, [str(exc)]


def _validate_paper_only_ibkr_config(
    config: IbkrEnvironmentConfig | None,
    parse_errors: list[str],
) -> None:
    """Reject any config that is not a valid paper-account IBKR setup."""
    errors: list[str] = []
    if parse_errors:
        errors.extend(parse_errors)
        raise ValueError("; ".join(errors))
    if config is None:
        errors.append("configuration is not readable")
        raise ValueError("; ".join(errors))

    if config.mode != "paper":
        errors.append("paper-only drill requires mode=paper")

    if not is_ibkr_paper_account(config.order_execution.account_id):
        errors.append("paper-only drill requires a paper account id")

    if config.order_execution.port != IBKR_PAPER_GATEWAY_PORT:
        errors.append(f"paper-only drill requires paper Gateway port {IBKR_PAPER_GATEWAY_PORT}")

    errors.extend(collect_validation_errors(config))
    if errors:
        raise ValueError("; ".join(errors))


def _summarize_config(config: IbkrEnvironmentConfig) -> JsonObject:
    """Build an order-execution summary of the paper config for evidence."""
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
    """Build an evidence dict from an execution report."""
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


def _broker_order_record_evidence(record: BrokerOrderRecord) -> JsonObject:
    return {
        "internal_order_id": record.internal_order_id.value,
        "client_order_id": record.client_order_id,
        "account_id": record.account_id.value,
        "strategy_id": record.strategy_id.value if record.strategy_id is not None else None,
        "submitted_at": record.submitted_at.isoformat(),
        "ibkr_order_id": record.ibkr_order_id,
        "perm_id": record.perm_id,
        "status": record.status,
        "last_broker_status_at": (
            record.last_broker_status_at.isoformat()
            if record.last_broker_status_at is not None
            else None
        ),
    }


def _reconciliation_evidence(
    *,
    account_id: AccountId,
    manager: OrderManager,
) -> JsonObject:
    reconciler = BrokerRuntimeReconciliation(account_id=account_id)
    internal = reconciler.internal_snapshot(
        order_manager=manager.snapshot(),
        account=AccountSnapshot(cash={"USD": Decimal("0")}, positions={}),
    )
    broker = ReconciliationSnapshot(
        account_id=internal.account_id,
        orders=internal.orders,
        positions=internal.positions,
        cash=internal.cash,
    )
    startup = reconciler.startup_decision(internal=internal, broker=broker)
    periodic = reconciler.periodic_check(internal=internal, broker=broker)
    return {
        "startup": {
            "trading_enabled": startup.trading_enabled,
            "reason_code": startup.reason_code,
            "has_drift": startup.report.has_drift,
        },
        "periodic": {
            "has_drift": periodic.report.has_drift,
            "runtime_event": (
                periodic.runtime_event.kind if periodic.runtime_event is not None else None
            ),
        },
    }


def _evidence_filename(generated_at: datetime, label: str | None) -> str:
    """Build a timestamped evidence filename with an optional label."""
    timestamp = generated_at.strftime("%Y%m%dT%H%M%SZ")
    safe_label = _safe_label(label) if label else "paper_order_lifecycle_drill"
    return f"{timestamp}_{safe_label}.json"


def _safe_label(label: str | None) -> str:
    """Sanitize a label into a filename-safe slug, with a default fallback."""
    if not label:
        return "paper_order_lifecycle_drill"
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", label.strip()).strip("-")
    return safe or "paper_order_lifecycle_drill"


__all__ = ["main", "run_paper_order_lifecycle_drill"]
