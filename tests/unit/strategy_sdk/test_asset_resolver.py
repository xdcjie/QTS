"""Unit tests for strategy asset resolution collaborator."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from qts.core.ids import InstrumentId
from qts.domain.instruments import OptionRight
from qts.strategy_sdk import AssetRef
from qts.strategy_sdk.asset_resolver import OptionContractRef, StrategyAssetResolver


class _FakeInstrumentRegistry:
    def __init__(self) -> None:
        self._map = {"AAPL": InstrumentId("EQUITY.US.NASDAQ.AAPL")}

    def resolve(self, user_symbol: str) -> InstrumentId:
        return self._map[user_symbol]


class _FakeFutureResolver:
    def resolve_contract(self, root_symbol: str, *, offset: int = 0) -> InstrumentId:
        return InstrumentId(f"FUTURE.CME.{root_symbol}.{offset:04d}")


class _FakeOptionRef:
    def __init__(self, instrument_id: InstrumentId) -> None:
        self.instrument_id = instrument_id


class _FakeOptionResolver:
    def find(
        self,
        *,
        underlying: InstrumentId,
        expiry: date | None = None,
        strike: Decimal | None = None,
        right: OptionRight | None = None,
    ) -> list[OptionContractRef]:
        if underlying.value == "EQUITY.US.NASDAQ.AAPL" and expiry == date(2026, 6, 19):
            return [_FakeOptionRef(InstrumentId("OPTION.US.AAPL.20260619.C.200"))]
        return []


def test_asset_resolver_resolves_symbol() -> None:
    resolver = StrategyAssetResolver(instrument_registry=_FakeInstrumentRegistry())
    asset = resolver.resolve_symbol("AAPL")
    assert asset == AssetRef(InstrumentId("EQUITY.US.NASDAQ.AAPL"), "AAPL")


def test_asset_resolver_resolves_front_future() -> None:
    resolver = StrategyAssetResolver(future_chain_registry=_FakeFutureResolver())
    asset = resolver.resolve_future("ES")
    assert asset == AssetRef(
        InstrumentId("FUTURE.CME.ES.0000"),
        "ES",
        metadata={"contract": "front"},
    )
    assert asset.metadata["contract"] == "front"


def test_asset_resolver_resolves_option_reference() -> None:
    resolver = StrategyAssetResolver(option_chain_registry=_FakeOptionResolver())
    asset = resolver.resolve_option(
        underlying=InstrumentId("EQUITY.US.NASDAQ.AAPL"),
        expiry=date(2026, 6, 19),
        strike=Decimal("200"),
        right=OptionRight.CALL,
    )
    assert asset.instrument_id == InstrumentId("OPTION.US.AAPL.20260619.C.200")
