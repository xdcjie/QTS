"""Instrument and roll-resolution helpers for backtest execution."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.execution_timing import ExecutionTimingModel
from qts.domain.instruments import AssetClass, ContractSpec, Instrument, SettlementType
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry
from qts.registry.instrument_registry import InstrumentRegistry
from qts.strategy_sdk import TargetIntent


class BacktestInstrumentContext:
    """Resolve backtest instrument IDs, roll targets, and instrument metadata."""

    def __init__(
        self,
        *,
        future_roll_registry: FutureRollRegistry | None = None,
        instrument_registry: InstrumentRegistry | None = None,
        registry_bars: Sequence[Bar] | None = None,
        contract_multipliers: Mapping[InstrumentId, Decimal] | None = None,
        execution_timing: ExecutionTimingModel | None = None,
    ) -> None:
        """Initialize the context from roll/instrument registries, registry bars, and timing."""
        self._future_roll_registry = future_roll_registry
        self._provided_registry = instrument_registry
        self._registry_bars = tuple(registry_bars or ())
        self._related_contracts_by_continuous: dict[InstrumentId, frozenset[InstrumentId]] = {}
        self._contract_multipliers = dict(contract_multipliers or {})
        self._execution_timing = execution_timing or ExecutionTimingModel()

    @property
    def execution_timing(self) -> ExecutionTimingModel:
        """Return the fill-timing model that prices decisions for this context."""
        return self._execution_timing

    def instrument_registry(self) -> InstrumentRegistry:
        """Return the provided registry or build one from the streamed registry bars."""
        if self._provided_registry is not None:
            return self._provided_registry
        if not self._registry_bars:
            raise RuntimeError(
                "instrument_registry is required when backtest bars are streamed "
                "from a one-pass iterable"
            )

        registry = InstrumentRegistry()
        seen: set[InstrumentId] = set()
        for bar in self._registry_bars:
            if bar.instrument_id in seen:
                continue
            seen.add(bar.instrument_id)
            registry.register(
                self._symbol_for(bar.instrument_id),
                Instrument(
                    instrument_id=bar.instrument_id,
                    asset_class=AssetClass.EQUITY,
                    exchange=self._exchange_for(bar.instrument_id),
                    currency="USD",
                    contract_spec=ContractSpec(
                        tick_size=Decimal("0.01"),
                        lot_size=Decimal("1"),
                        multiplier=self._contract_multipliers.get(bar.instrument_id, Decimal("1")),
                        settlement=SettlementType.CASH,
                        calendar_id="BACKTEST",
                    ),
                ),
            )
        return registry

    def order_instrument_for_intent(self, intent: TargetIntent, *, bar: Bar) -> InstrumentId:
        """Resolve the intent's asset to a concrete tradable contract, rolling if continuous."""
        if self.is_continuous(intent.asset.instrument_id):
            if self._future_roll_registry is None:
                raise RuntimeError("future roll registry is required for continuous contracts")
            return self._future_roll_registry.resolve_contract(
                intent.asset.instrument_id,
                as_of=bar.end_time,
            )
        return intent.asset.instrument_id

    def market_price_for_intent(
        self,
        intent: TargetIntent,
        *,
        instrument_id: InstrumentId,
        bar: Bar,
    ) -> Decimal:
        """Return the execution price for the resolved contract, using roll prices if continuous."""
        if self.is_continuous(intent.asset.instrument_id):
            if self._future_roll_registry is None:
                raise RuntimeError("future roll registry is required for continuous contracts")
            return self._future_roll_registry.execution_price(
                intent.asset.instrument_id,
                instrument_id,
                as_of=bar.end_time,
            )
        return self._execution_timing.price_for_execution_bar(bar)

    def update_rolling_prices(
        self, bar: Bar, *, latest_prices: dict[InstrumentId, Decimal]
    ) -> None:
        """Record the resolved contract's roll-adjusted price for a continuous-future bar."""
        if self._future_roll_registry is None:
            return
        if not self.is_continuous(bar.instrument_id):
            return
        try:
            instrument_id = self._future_roll_registry.resolve_contract(
                bar.instrument_id,
                as_of=bar.end_time,
            )
            latest_prices[instrument_id] = self._future_roll_registry.execution_price(
                bar.instrument_id,
                instrument_id,
                as_of=bar.end_time,
            )
        except KeyError:
            return

    def related_contracts_for(
        self, continuous_instrument_id: InstrumentId
    ) -> frozenset[InstrumentId]:
        """Return the cached set of concrete contracts behind a continuous instrument."""
        if not self.is_continuous(continuous_instrument_id):
            raise RuntimeError("future roll registry is not configured for this instrument")

        if self._future_roll_registry is None:
            raise RuntimeError("future roll registry is required")

        related_contracts = self._related_contracts_by_continuous.get(continuous_instrument_id)
        if related_contracts is None:
            related_contracts = frozenset(
                self._future_roll_registry.related_contracts(continuous_instrument_id)
            )
            self._related_contracts_by_continuous[continuous_instrument_id] = related_contracts
        return related_contracts

    def is_continuous(self, instrument_id: InstrumentId) -> bool:
        """Return whether the instrument is a continuous future tracked by the roll registry."""
        return self._future_roll_registry is not None and self._future_roll_registry.is_continuous(
            instrument_id
        )

    @staticmethod
    def _symbol_for(instrument_id: InstrumentId) -> str:
        """Return the trailing symbol segment of the instrument id."""
        return instrument_id.value.rsplit(".", maxsplit=1)[-1]

    @staticmethod
    def _exchange_for(instrument_id: InstrumentId) -> str:
        """Return the exchange segment of the instrument id, defaulting to BACKTEST."""
        parts = instrument_id.value.split(".")
        if len(parts) >= 2:
            return parts[1]
        return "BACKTEST"


__all__ = ["BacktestInstrumentContext"]
