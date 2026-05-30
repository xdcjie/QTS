"""QTS-FINAL-013: BacktestPipeline.from_yaml loads via the config loader.

The pipeline must obtain its config from ``BacktestConfigLoader.from_path``
rather than a config-dataclass ``from_yaml`` (which no longer exists), and the
config dataclasses expose only payload constructors.
"""

from __future__ import annotations

from pathlib import Path

from qts.runtime.config import BacktestRuntimeConfig, BacktestStrategyConfig
from qts.runtime.config_loader import BacktestConfigLoader


def test_config_dataclasses_have_no_from_yaml() -> None:
    assert not hasattr(BacktestRuntimeConfig, "from_yaml")
    assert not hasattr(BacktestStrategyConfig, "from_yaml")
    # Payload constructors remain the public construction surface.
    assert hasattr(BacktestRuntimeConfig, "from_payload") or hasattr(
        BacktestRuntimeConfig, "to_payload"
    )
    assert hasattr(BacktestStrategyConfig, "from_payload")


def test_loader_exposes_path_constructors() -> None:
    assert hasattr(BacktestConfigLoader, "from_path")
    assert hasattr(BacktestConfigLoader, "strategy_from_path")


def test_pipeline_from_yaml_uses_loader(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from qts.backtest.pipeline import BacktestPipeline

    captured: dict[str, Path] = {}
    sentinel = object()

    def _fake_from_path(path: Path) -> object:
        captured["path"] = path
        return sentinel

    # Patch the loader class itself (the same object pipeline imports), so the
    # test proves the pipeline routes through BacktestConfigLoader.from_path.
    monkeypatch.setattr(BacktestConfigLoader, "from_path", staticmethod(_fake_from_path))
    config_path = tmp_path / "backtest.yaml"
    config_path.write_text("roots: [GC]\n", encoding="utf-8")

    pipeline = BacktestPipeline.from_yaml(config_path)

    assert captured["path"] == config_path
    assert pipeline.config is sentinel
