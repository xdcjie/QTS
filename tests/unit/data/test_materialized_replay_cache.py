from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from qts.core.ids import InstrumentId
from qts.data.sources.materialized_replay_cache import materialized_replay_inputs
from qts.data.sources.replay_market_data_source import ReplayMarketDataBundle
from qts.domain.market_data import Bar
from qts.registry.future_roll import FutureRollRegistry, FutureRollSelection
from qts.registry.instrument_registry import InstrumentRegistry


@dataclass(frozen=True)
class _PayloadOwner:
    payload: dict[str, object]

    def to_payload(self) -> dict[str, object]:
        return self.payload


@dataclass(frozen=True)
class _CacheConfig:
    start: datetime
    end: datetime
    timeframe: str
    roots: tuple[str, ...]
    symbols: tuple[str, ...]
    instrument_ids: dict[str, InstrumentId]
    market_data: _PayloadOwner
    roll_policy: _PayloadOwner


def test_materialized_replay_manifest_compacts_roll_history_to_cached_bars(
    tmp_path: Path,
) -> None:
    continuous_id = InstrumentId("CONTINUOUS_FUTURE.CME.GC")
    first_contract = InstrumentId("FUTURE.CME.GC.GCG0")
    second_contract = InstrumentId("FUTURE.CME.GC.GCH0")
    first_bar_end = datetime(2020, 1, 2, tzinfo=UTC)
    second_bar_end = datetime(2020, 1, 3, tzinfo=UTC)
    config = _cache_config(continuous_id=continuous_id, end=second_bar_end)
    registry = _roll_registry(
        continuous_id=continuous_id,
        first_contract=first_contract,
        second_contract=second_contract,
        start=first_bar_end - timedelta(minutes=12),
        count=12,
    )
    inputs = _replay_bundle(
        bars=(
            _bar(continuous_id, first_bar_end - timedelta(days=1), first_bar_end, "100"),
            _bar(continuous_id, second_bar_end - timedelta(days=1), second_bar_end, "101"),
        ),
        roll_registry=registry,
    )

    materialized_replay_inputs(
        config=config,
        catalog=object(),
        inputs=inputs,
        cache_dir=tmp_path,
    )

    manifest_path = next(tmp_path.glob("*.manifest.json"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    roll_selections = manifest["roll_selections"]
    assert len(roll_selections) == 1
    assert len(roll_selections) < len(registry.selection_history())

    restored_registry = _roll_registry_without_history(
        first_contract=first_contract,
        second_contract=second_contract,
    )
    restored = materialized_replay_inputs(
        config=config,
        catalog=object(),
        inputs=_replay_bundle(bars=(), roll_registry=restored_registry),
        cache_dir=tmp_path,
    )

    assert len(tuple(restored.bars)) == 2
    assert restored_registry.resolve_contract("GC", as_of=second_bar_end) == second_contract
    assert restored_registry.execution_price(
        continuous_id,
        second_contract,
        as_of=second_bar_end,
    ) == Decimal("111")


def _cache_config(*, continuous_id: InstrumentId, end: datetime) -> _CacheConfig:
    return _CacheConfig(
        start=datetime(2020, 1, 1, tzinfo=UTC),
        end=end,
        timeframe="1d",
        roots=("GC",),
        symbols=("GC",),
        instrument_ids={"GC": continuous_id},
        market_data=_PayloadOwner({"source": "fixture"}),
        roll_policy=_PayloadOwner({"enabled": True}),
    )


def _roll_registry(
    *,
    continuous_id: InstrumentId,
    first_contract: InstrumentId,
    second_contract: InstrumentId,
    start: datetime,
    count: int,
) -> FutureRollRegistry:
    registry = _roll_registry_without_history(
        first_contract=first_contract,
        second_contract=second_contract,
    )
    for index in range(count):
        as_of = start + timedelta(minutes=index)
        concrete = first_contract if index < count // 2 else second_contract
        registry.record_selection(
            FutureRollSelection(
                continuous_instrument_id=continuous_id,
                root_symbol="GC",
                as_of=as_of,
                concrete_instrument_id=concrete,
                source_symbol=concrete.value.rsplit(".", maxsplit=1)[-1],
                prices_by_instrument={
                    first_contract: Decimal("100") + Decimal(index),
                    second_contract: Decimal("100") + Decimal(index),
                },
            )
        )
    return registry


def _roll_registry_without_history(
    *,
    first_contract: InstrumentId,
    second_contract: InstrumentId,
) -> FutureRollRegistry:
    registry = FutureRollRegistry()
    registry.register_root(
        root_symbol="GC",
        exchange="CME",
        contracts=(first_contract, second_contract),
    )
    return registry


def _replay_bundle(
    *,
    bars: tuple[Bar, ...],
    roll_registry: FutureRollRegistry,
) -> ReplayMarketDataBundle:
    return ReplayMarketDataBundle(
        bars=iter(bars),
        dataset_stats={},
        exchange_timezone_by_instrument={},
        session_window_by_instrument={},
        instrument_registry=InstrumentRegistry(),
        dataset_metadata=(),
        contract_multipliers={},
        future_roll_registry=roll_registry,
    )


def _bar(
    instrument_id: InstrumentId,
    start: datetime,
    end: datetime,
    close: str,
) -> Bar:
    close_value = Decimal(close)
    return Bar(
        instrument_id=instrument_id,
        start_time=start,
        end_time=end,
        timeframe="1d",
        session_id=start.date().isoformat(),
        open=close_value,
        high=close_value,
        low=close_value,
        close=close_value,
        volume=Decimal("100"),
        is_complete=True,
    )
