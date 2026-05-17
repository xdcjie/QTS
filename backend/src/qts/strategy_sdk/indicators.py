"""Strategy-facing indicator factory."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TypeAlias

from qts.domain.market_data import Bar
from qts.indicators.price.ema import EMA
from qts.indicators.price.sma import SMA
from qts.indicators.technical import (
    ADX,
    MACD,
    RSI,
    AccumulationDistribution,
    AverageTrueRange,
    BollingerBands,
    BollingerBandsValue,
    ChaikinMoneyFlow,
    CommodityChannelIndex,
    DirectionalMovementValue,
    DonchianChannel,
    DonchianChannelValue,
    HistoricalVolatility,
    KeltnerChannel,
    KeltnerChannelValue,
    MACDValue,
    MoneyFlowIndex,
    OnBalanceVolume,
    RateOfChange,
    SessionVWAP,
    StandardDeviation,
    StochasticOscillator,
    StochasticOscillatorValue,
    VolumeRatio,
    WilliamsR,
)
from qts.strategy_sdk.asset_ref import AssetRef

IndicatorValue: TypeAlias = (
    Decimal
    | BollingerBandsValue
    | DirectionalMovementValue
    | DonchianChannelValue
    | KeltnerChannelValue
    | MACDValue
    | StochasticOscillatorValue
)


@dataclass(slots=True)
class AssetIndicator:
    """Indicator bound to a strategy asset reference."""

    asset: AssetRef
    indicator: object
    _ready: Callable[[], bool] = field(repr=False)
    _value: Callable[[], IndicatorValue | None] = field(repr=False)
    _bar_update: Callable[[Bar], IndicatorValue | None] = field(repr=False)
    _price_update: Callable[[Decimal], IndicatorValue | None] | None = field(
        default=None, repr=False
    )

    @property
    def ready(self) -> bool:
        """Perform ready."""
        return self._ready()

    @property
    def value(self) -> IndicatorValue | None:
        """Perform value."""
        return self._value()

    def update(self, price: Decimal) -> IndicatorValue | None:
        """Perform update."""
        if self._price_update is None:
            raise TypeError("indicator does not support direct price updates")
        return self._price_update(price)

    def update_from_bar(self, bar: Bar) -> IndicatorValue | None:
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

    def bollinger_bands(
        self, asset: AssetRef, window: int, standard_deviations: Decimal = Decimal("2")
    ) -> AssetIndicator:
        """Create Bollinger Bands for close prices."""
        return self._bind_price_indicator(
            asset,
            BollingerBands(window=window, standard_deviations=standard_deviations),
        )

    def macd(
        self, asset: AssetRef, fast_window: int, slow_window: int, signal_window: int
    ) -> AssetIndicator:
        """Create MACD for close prices."""
        return self._bind_price_indicator(
            asset,
            MACD(
                fast_window=fast_window,
                slow_window=slow_window,
                signal_window=signal_window,
            ),
        )

    def rate_of_change(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create rate of change for close prices."""
        return self._bind_price_indicator(asset, RateOfChange(window=window))

    def adx(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create ADX for OHLC bars."""
        indicator = ADX(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def keltner_channel(
        self,
        asset: AssetRef,
        window: int,
        multiplier: Decimal = Decimal("2"),
    ) -> AssetIndicator:
        """Create Keltner Channel for OHLC bars."""
        indicator = KeltnerChannel(window=window, multiplier=multiplier)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def donchian_channel(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create Donchian Channel for OHLC bars."""
        indicator = DonchianChannel(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def stochastic(
        self,
        asset: AssetRef,
        window: int,
        signal_window: int = 3,
    ) -> AssetIndicator:
        """Create stochastic oscillator for OHLC bars."""
        indicator = StochasticOscillator(window=window, signal_window=signal_window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def cci(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create Commodity Channel Index for OHLC bars."""
        indicator = CommodityChannelIndex(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def williams_r(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create Williams %R for OHLC bars."""
        indicator = WilliamsR(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def standard_deviation(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create rolling standard deviation for close prices."""
        return self._bind_price_indicator(asset, StandardDeviation(window=window))

    def historical_volatility(
        self,
        asset: AssetRef,
        window: int,
        periods_per_year: Decimal = Decimal("252"),
    ) -> AssetIndicator:
        """Create annualized historical volatility for close prices."""
        return self._bind_price_indicator(
            asset,
            HistoricalVolatility(window=window, periods_per_year=periods_per_year),
        )

    def on_balance_volume(self, asset: AssetRef) -> AssetIndicator:
        """Create On-Balance Volume for OHLCV bars."""
        indicator = OnBalanceVolume()
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def money_flow_index(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create Money Flow Index for OHLCV bars."""
        indicator = MoneyFlowIndex(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def accumulation_distribution(self, asset: AssetRef) -> AssetIndicator:
        """Create Accumulation/Distribution Line for OHLCV bars."""
        indicator = AccumulationDistribution()
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def chaikin_money_flow(self, asset: AssetRef, window: int) -> AssetIndicator:
        """Create Chaikin Money Flow for OHLCV bars."""
        indicator = ChaikinMoneyFlow(window=window)
        return self._bind_bar_indicator(asset, indicator.update_bar, indicator)

    def update_from_bar(self, bar: Bar) -> None:
        """Perform update_from_bar."""
        for item in self._created:
            if item.asset.instrument_id == bar.instrument_id:
                item.update_from_bar(bar)

    def _bind_price_indicator(
        self,
        asset: AssetRef,
        indicator: SMA
        | EMA
        | RSI
        | BollingerBands
        | MACD
        | RateOfChange
        | StandardDeviation
        | HistoricalVolatility,
    ) -> AssetIndicator:
        """Bind a close-price indicator to an asset."""

        def update_from_bar(bar: Bar) -> IndicatorValue | None:
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
        update_from_bar: Callable[[Bar], IndicatorValue | None],
        indicator: AverageTrueRange
        | SessionVWAP
        | ADX
        | KeltnerChannel
        | DonchianChannel
        | StochasticOscillator
        | CommodityChannelIndex
        | WilliamsR
        | OnBalanceVolume
        | MoneyFlowIndex
        | AccumulationDistribution
        | ChaikinMoneyFlow,
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

        def update_from_bar(bar: Bar) -> IndicatorValue | None:
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


__all__ = ["AssetIndicator", "IndicatorFactory", "IndicatorValue"]
