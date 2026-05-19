"""IBKR order request mapping."""

from __future__ import annotations

from decimal import Decimal

from qts.core.ids import StrategyId
from qts.domain.orders import OrderIntent, OrderType, TimeInForce
from qts.execution.broker import BrokerCapabilities
from qts.execution.transports.ibkr_tws_order_execution_transport import (
    IbkrOrderContractSpec,
    IbkrOrderRequest,
)
from qts.registry.broker_symbol_mapping import BrokerSymbolMapping


class IbkrOrderRequestMapper:
    """Owns validation and mapping from internal order intents to IBKR requests."""

    def __init__(
        self,
        *,
        account_id: str,
        symbol_mapping: BrokerSymbolMapping,
        capabilities: BrokerCapabilities,
    ) -> None:
        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        self._account_id = account_id
        self._symbol_mapping = symbol_mapping
        self._capabilities = capabilities

    def to_order_request(
        self,
        intent: OrderIntent,
        *,
        client_order_id: str,
        strategy_id: StrategyId | None = None,
        order_type: OrderType | None = None,
        time_in_force: TimeInForce | None = None,
        limit_price: Decimal | None = None,
        asset_class: str = "equity",
        opens_short: bool = False,
        contract: IbkrOrderContractSpec | None = None,
        outside_regular_trading_hours: bool = False,
        what_if: bool = False,
    ) -> IbkrOrderRequest:
        """Map an approved internal order intent into an IBKR request."""

        if not client_order_id.strip():
            raise ValueError("client_order_id must not be empty")
        spec = intent.order_spec
        resolved_order_type = order_type or spec.order_type
        resolved_time_in_force = time_in_force or spec.time_in_force
        resolved_limit_price = limit_price if limit_price is not None else spec.limit_price
        self._validate_order_request(
            intent,
            order_type=resolved_order_type,
            time_in_force=resolved_time_in_force,
            limit_price=resolved_limit_price,
            asset_class=asset_class,
            opens_short=opens_short,
        )
        return IbkrOrderRequest(
            internal_order_id=intent.order_id,
            client_order_id=client_order_id,
            internal_account_id=intent.account_id,
            strategy_id=strategy_id,
            account_id=self._account_id,
            broker_symbol=self._symbol_mapping.to_broker_symbol(intent.instrument_id),
            side=intent.side.value,
            quantity=intent.quantity,
            order_type=resolved_order_type,
            time_in_force=resolved_time_in_force,
            limit_price=resolved_limit_price,
            bracket_legs=None if spec.bracket is None else spec.bracket.legs,
            contract=contract,
            outside_regular_trading_hours=outside_regular_trading_hours,
            what_if=what_if,
        )

    def _validate_order_request(
        self,
        intent: OrderIntent,
        *,
        order_type: OrderType,
        time_in_force: TimeInForce,
        limit_price: Decimal | None,
        asset_class: str,
        opens_short: bool,
    ) -> None:
        if not self._capabilities.supports_order_type(order_type):
            raise ValueError(f"order type is not supported: {order_type.value}")
        if not self._capabilities.supports_tif(time_in_force):
            raise ValueError(f"time in force is not supported: {time_in_force.value}")
        if not self._capabilities.supports_asset_class(asset_class):
            raise ValueError(f"asset class is not supported: {asset_class}")
        if order_type is OrderType.LIMIT and limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if order_type not in {OrderType.LIMIT, OrderType.BRACKET} and limit_price is not None:
            raise ValueError("limit_price is only valid for limit orders")
        if (
            not self._capabilities.supports_fractional
            and intent.quantity != intent.quantity.to_integral_value()
        ):
            raise ValueError("fractional quantity is not supported")
        self._capabilities.validate_order_quantity(intent.quantity)
        if opens_short and not self._capabilities.supports_short:
            raise ValueError("short orders are not supported")


__all__ = ["IbkrOrderRequestMapper"]
