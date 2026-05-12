from __future__ import annotations

from pathlib import Path

import pytest
from qts.data.historical.config_loader import HistoricalDataConfigLoader


def test_config_loader_loads_payload(tmp_path: Path) -> None:
    payload = {
        "historical_data": {
            "stores": {
                "local_csv": {
                    "type": "local_csv",
                    "root_dir": "historical",
                    "bars_dir": "data",
                    "chains_dir": "chains",
                    "bars_file_template": "{root_lower}.csv",
                    "chain_file_template": "{root}.json",
                    "source_timeframe": "1m",
                    "exchange_timezone": "US/Eastern",
                    "timezone_policy": "source_utc_exchange_sessions",
                    "normalization": "raw",
                }
            },
            "catalogs": {
                "research_futures": {
                    "store": "local_csv",
                    "datasets": {
                        "GC": {
                            "asset_class": "future",
                            "exchange": "CME",
                        }
                    },
                }
            },
            "schemas": {},
        }
    }

    config = HistoricalDataConfigLoader.from_payload(payload)
    dataset = config.resolve_dataset("research_futures", "GC")

    assert dataset.csv_path == Path("historical/data/gc.csv")
    assert dataset.chain_path == Path("historical/chains/GC.json")
    assert dataset.source_timeframe == "1m"
    assert dataset.exchange_timezone == "US/Eastern"
    assert config.catalog("research_futures").datasets["GC"].asset_class == "future"


def test_config_loader_from_payload_rejects_non_mapping_payload() -> None:
    with pytest.raises(ValueError, match="historical_data must be a mapping"):
        HistoricalDataConfigLoader.from_payload([])


def test_config_loader_from_path_supports_yaml_file(tmp_path: Path) -> None:
    path = tmp_path / "historical.local.yaml"
    path.write_text(
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
        SI:
          asset_class: future
          exchange: CME
""",
        encoding="utf-8",
    )

    config = HistoricalDataConfigLoader.from_path(path)
    dataset = config.resolve_dataset("research_futures", "SI")

    assert dataset.csv_path == Path("historical/data/si.csv")
    assert dataset.source_timeframe is None
