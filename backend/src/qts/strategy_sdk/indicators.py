"""Strategy-facing indicator factory."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from qts.domain.market_data import Bar
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

    def update_from_bar(self, bar: Bar) -> None:
        for item in self._created:
            if item.asset.instrument_id == bar.instrument_id:
                item.update(bar.close)


__all__ = ["AssetIndicator", "IndicatorFactory"]
