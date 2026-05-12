"""Instrument domain model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from qts.core.ids import InstrumentId
from qts.domain.instruments.contract_spec import ContractSpec
from qts.domain.instruments.derivative_spec import (
    DerivativeSpec,
    ExerciseStyle,
    FutureSpec,
    OptionRight,
    OptionSpec,
)


class AssetClass(StrEnum):
    """Supported instrument asset classes."""

    EQUITY = "equity"
    FUTURE = "future"
    OPTION = "option"


@dataclass(frozen=True, slots=True)
class Instrument:
    """Tradable instrument identified by a stable internal InstrumentId."""

    instrument_id: InstrumentId
    asset_class: AssetClass
    exchange: str
    currency: str
    contract_spec: ContractSpec
    derivative: DerivativeSpec | None = None
    tradable: bool = True

    def __post_init__(self) -> None:
        """Perform __post_init__."""
        if not self.exchange.strip():
            raise ValueError("exchange must not be empty")
        if not self.currency.strip():
            raise ValueError("currency must not be empty")
        if self.asset_class is AssetClass.EQUITY and self.derivative is not None:
            raise ValueError("equity instruments must not have derivative metadata")
        if self.asset_class is AssetClass.FUTURE and not isinstance(self.derivative, FutureSpec):
            raise ValueError("future instruments require FutureSpec")
        if self.asset_class is AssetClass.OPTION and not isinstance(self.derivative, OptionSpec):
            raise ValueError("option instruments require OptionSpec")


__all__ = [
    "AssetClass",
    "DerivativeSpec",
    "ExerciseStyle",
    "FutureSpec",
    "Instrument",
    "OptionRight",
    "OptionSpec",
]
