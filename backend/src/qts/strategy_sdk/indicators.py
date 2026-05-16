"""Strategy-facing indicator factory."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal

from qts.domain.market_data import Bar
from qts.indicators.price.ema import EMA
from qts.indicators.price.sma import SMA
from qts.indicators.technical import RSI, AverageTrueRange, SessionVWAP, VolumeRatio
from qts.strategy_sdk.asset_ref import AssetRef


@dataclass(slots=True)
class AssetIndicator:
    """Indicator bound to a strategy asset reference."""

    asset: AssetRef
    indicator: object
    _ready: Callable[[], bool] = field(repr=False)
    _value: Callable[[], Decimal | None] = field(repr=False)
    _bar_update: Callable[[Bar], Decimal | None] = field(repr=False)
    _price_update: Callable[[Decimal], Decimal | None] | None = field(default=None, repr=False)

    @property
    def ready(self) -> bool:
        """Perform ready."""
        return self._ready()

    @property
    def value(self) -> Decimal | None:
        """Perform value."""
        return self._value()

    def update(self, price: Decimal) -> Decimal | None:
        """Perform update."""
        if self._price_update is None:
            raise TypeError("indicator does not support direct price updates")
        return self._price_update(price)

    def update_from_bar(self, bar: Bar) -> Decimal | None:
        """Update the bound indicator from a completed strategy-facing bar."""
        return self._bar_update(bar)


@dataclass(slots=True)
class IndicatorFactory:
    """Factory for user-created indicators."""

    _created: list[AssetIndicator] = field(default_factory=list)

    def sma(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Perform sma."""
        return self._bind_price_indicator(asset, SMA(window=window))

    def ema(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create an exponential moving average indicator for close prices."""
        return self._bind_price_indicator(asset, EMA(window=window))

    def atr(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create an average true range indicator for OHLC bars."""
        indicator = AverageTrueRange(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def rsi(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create a relative strength index indicator for close prices."""
        return self._bind_price_indicator(asset, RSI(window=window))

    def session_vwap(self, asset: AssetRef) -> AssetIndicator:
        """Create a session VWAP indicator that resets on bar session changes."""
        indicator = SessionVWAP()
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def volume_ratio(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create a current-volume to rolling-average-volume ratio indicator."""
        indicator = VolumeRatio(window=window)
        return self._bind_volume_indicator(asset, indicator)

    def update_from_bar(self, bar: Bar) -> None:
        """Perform update_from_bar."""
        for item in self._created:
            if item.asset.instrument_id == bar.instrument_id:
                item.update_from_bar(bar)

    def _bind_price_indicator(self, asset: AssetRef, indicator: SMA | EMA | RSI) -> AssetIndicator:
        """Bind a close-price indicator to an asset."""

        def update_from_bar(bar: Bar) -> Decimal | None:
            return indicator.update(bar.close)

        bound = AssetIndicator(
            asset=asset,
            indicator=indicator,
            _ready=lambda: indicator.ready,
            _value=lambda: indicator.value,
            _bar_update=update_from_bar,
            _price_update=indicator.update,
        )
        self._created.append(bound)
        return bound

    def _bind_bar_indicator(
        self,
        asset: AssetRef,
        update_from_bar: Callable[[Bar], Decimal | None],
        indicator: AverageTrueRange | SessionVWAP,
    ) -> AssetIndicator:
        """Bind a full-bar indicator to an asset."""
        bound = AssetIndicator(
            asset=asset,
            indicator=indicator,
            _ready=lambda: indicator.ready,
            _value=lambda: indicator.value,
            _bar_update=update_from_bar,
        )
        self._created.append(bound)
        return bound

    def _bind_volume_indicator(self, asset: AssetRef, indicator: VolumeRatio) -> AssetIndicator:
        """Bind a volume indicator to an asset."""

        def update_from_bar(bar: Bar) -> Decimal | None:
            return indicator.update(bar.volume)

        bound = AssetIndicator(
            asset=asset,
            indicator=indicator,
            _ready=lambda: indicator.ready,
            _value=lambda: indicator.value,
            _bar_update=update_from_bar,
            _price_update=indicator.update,
        )
        self._created.append(bound)
        return bound


__all__ = ["AssetIndicator", "IndicatorFactory"]
