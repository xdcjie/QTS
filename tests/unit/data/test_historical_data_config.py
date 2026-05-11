from __future__ import annotations

from pathlib import Path

import pytest
from qts.data.historical.config import HistoricalDataConfig


def test_historical_data_config_accepts_legacy_store_level_source_timeframe(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "historical.local.yaml"
    config_path.write_text(
        """
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: historical
      bars_dir: data
      chains_dir: chains
      bars_file_template: "{root_lower}.csv"
      chain_file_template: "{root}.json"
      source_timeframe: 1m
      exchange_timezone: US/Eastern
      timezone_policy: source_utc_exchange_sessions
      normalization: raw
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
        SI:
          asset_class: future
          exchange: CME
""",
        encoding="utf-8",
    )

    config = HistoricalDataConfig.from_yaml(config_path)

    gc = config.resolve_dataset("research_futures", "GC")
    si = config.resolve_dataset("research_futures", "SI")
    assert gc.csv_path == Path("historical/data/gc.csv")
    assert gc.chain_path == Path("historical/chains/GC.json")
    assert si.csv_path == Path("historical/data/si.csv")
    assert si.chain_path == Path("historical/chains/SI.json")
    assert gc.source_timeframe == "1m"
    assert gc.exchange_timezone == "US/Eastern"
    assert config.catalog("research_futures").datasets["GC"].asset_class == "future"


def test_historical_data_config_maps_timeframe_and_schema_at_bar_file_level(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "historical.local.yaml"
    config_path.write_text(
        """
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: historical
      bars_dir: data
      chains_dir: chains
      bars_file_template: "{root_lower}.csv"
      chain_file_template: "{root}.json"
      defaults:
        schema: databento_ohlcv
        exchange_timezone: US/Eastern
        timezone_policy: source_utc_exchange_sessions
        normalization: raw
  schemas:
    databento_ohlcv:
      timestamp: ts_event
      symbol: symbol
      instrument_id: instrument_id
      open: open
      high: high
      low: low
      close: close
      volume: volume
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          chain_file: GC.json
          bars:
            - file: gc_1m.csv
              timeframe: 1m
            - file: gc_1d.csv
              timeframe: 1d
              schema: databento_ohlcv
        SI:
          asset_class: future
          exchange: CME
          chain_file: SI.json
          bars:
            - file: si_5s.csv
              timeframe: 5s
              schema: databento_ohlcv
""",
        encoding="utf-8",
    )

    config = HistoricalDataConfig.from_yaml(config_path)

    gc = config.resolve_dataset("research_futures", "GC", requested_timeframe="5m")
    si = config.resolve_dataset("research_futures", "SI", requested_timeframe="1m")
    assert gc.csv_path == Path("historical/data/gc_1m.csv")
    assert gc.chain_path == Path("historical/chains/GC.json")
    assert gc.source_timeframe == "1m"
    assert gc.schema_name == "databento_ohlcv"
    assert gc.csv_schema.timestamp == "ts_event"
    assert si.csv_path == Path("historical/data/si_5s.csv")
    assert si.source_timeframe == "5s"
    assert si.exchange_timezone == "US/Eastern"


def test_project_historical_data_example_resolves_gc_si_paths() -> None:
    config = HistoricalDataConfig.from_yaml(Path("configs/data/historical.local.yaml"))

    gc = config.resolve_dataset("research_futures", "GC")
    si = config.resolve_dataset("research_futures", "SI")
    assert gc.csv_path == Path("historical/data/gc.csv")
    assert gc.chain_path == Path("historical/chains/GC.json")
    assert si.csv_path == Path("historical/data/si.csv")
    assert si.chain_path == Path("historical/chains/SI.json")
    assert gc.source_timeframe == "1m"


def test_historical_data_config_accepts_legacy_dataset_file_overrides(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "historical.local.yaml"
    config_path.write_text(
        """
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: historical
      bars_dir: data
      chains_dir: chains
      bars_file_template: "{root_lower}.csv"
      chain_file_template: "{root}.json"
      source_timeframe: 1m
      exchange_timezone: US/Eastern
      timezone_policy: source_utc_exchange_sessions
      normalization: raw
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          bars_file: gc_1m.csv
          chain_file: GC_custom.json
          source_timeframe: 5s
          exchange_timezone: America/Chicago
""",
        encoding="utf-8",
    )

    config = HistoricalDataConfig.from_yaml(config_path)

    gc = config.resolve_dataset("research_futures", "GC")
    assert gc.csv_path == Path("historical/data/gc_1m.csv")
    assert gc.chain_path == Path("historical/chains/GC_custom.json")
    assert gc.source_timeframe == "5s"
    assert gc.exchange_timezone == "America/Chicago"


def test_historical_data_config_rejects_storage_paths_inside_dataset_entries(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "historical.local.yaml"
    config_path.write_text(
        """
historical_data:
  stores:
    local_csv:
      type: local_csv
      root_dir: historical
      bars_dir: data
      chains_dir: chains
  catalogs:
    research_futures:
      store: local_csv
      datasets:
        GC:
          asset_class: future
          exchange: CME
          data_dir: historical/data
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="storage paths belong to stores"):
        HistoricalDataConfig.from_yaml(config_path)
