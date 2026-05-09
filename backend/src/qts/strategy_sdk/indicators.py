"""Strategy-facing indicator factory."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.indicators.price.sma import SMA
from qts.strategy_sdk.asset_ref import AssetRef


@dataclass(slots=True)
class AssetIndicator:
    """Indicator bound to a strategy asset reference."""

    asset: AssetRef
    indicator: SMA

    @property
    def ready(self) -> bool:
        return self.indicator.ready

    @property
    def value(self) -> Decimal | None:
        return self.indicator.value

    def update(self, price: Decimal) -> Decimal | None:
        return self.indicator.update(price)


@dataclass(slots=True)
class IndicatorFactory:
    """Factory for user-created indicators."""

    _created: list[AssetIndicator] = field(default_factory=list)

    def sma(self, asset: AssetRef, window: int) -> AssetIndicator:
        indicator = AssetIndicator(asset=asset, indicator=SMA(window=window))
        self._created.append(indicator)
        return indicator


__all__ = ["AssetIndicator", "IndicatorFactory"]
