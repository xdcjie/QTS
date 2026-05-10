"""Research backtest report artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from qts.core.ids import BacktestRunId


@dataclass(frozen=True, slots=True)
class EquityCurvePoint:
    """One timestamped equity observation."""

    time: datetime
    equity: Decimal


@dataclass(frozen=True, slots=True)
class TradeLedgerEntry:
    """Auditable row for a simulated fill."""

    order_id: str
    instrument_id: str
    side: str
    quantity: Decimal
    fill_price: Decimal
    commission: Decimal
    slippage: Decimal
    fill_time: datetime
    source_bar_time: datetime


@dataclass(frozen=True, slots=True)
class BacktestReport:
    """Stable research report containing inputs, outputs, metrics, and hashes."""

    run_id: BacktestRunId
    config_hash: str
    dataset_metadata: tuple[Any, ...]
    cost_model: dict[str, Any]
    processed_bars: int
    warmup_bars: int
    trading_bars: int
    orders: tuple[dict[str, Any], ...]
    fills: tuple[dict[str, Any], ...]
    trade_ledger: tuple[TradeLedgerEntry, ...]
    equity_curve: tuple[EquityCurvePoint, ...]
    metrics: dict[str, Any]
    report_hash: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "report_hash", _stable_hash(self._payload(include_hash=False)))

    def to_json(self) -> str:
        return json.dumps(
            self._payload(include_hash=True),
            default=_json_default,
            sort_keys=True,
            separators=(",", ":"),
        )

    def to_dict(self) -> dict[str, Any]:
        return self._payload(include_hash=True)

    def _payload(self, *, include_hash: bool) -> dict[str, Any]:
        payload = {
            "run_id": self.run_id.value,
            "config_hash": self.config_hash,
            "dataset_metadata": self.dataset_metadata,
            "cost_model": self.cost_model,
            "processed_bars": self.processed_bars,
            "warmup_bars": self.warmup_bars,
            "trading_bars": self.trading_bars,
            "orders": self.orders,
            "fills": self.fills,
            "trade_ledger": [
                {
                    "order_id": row.order_id,
                    "instrument_id": row.instrument_id,
                    "side": row.side,
                    "quantity": row.quantity,
                    "fill_price": row.fill_price,
                    "commission": row.commission,
                    "slippage": row.slippage,
                    "fill_time": row.fill_time,
                    "source_bar_time": row.source_bar_time,
                }
                for row in self.trade_ledger
            ],
            "equity_curve": [
                {"time": point.time, "equity": point.equity} for point in self.equity_curve
            ],
            "metrics": self.metrics,
        }
        if include_hash:
            payload["report_hash"] = self.report_hash
        return payload


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, default=_json_default, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(encoded.encode()).hexdigest()}"


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")


__all__ = ["BacktestReport", "EquityCurvePoint", "TradeLedgerEntry"]
