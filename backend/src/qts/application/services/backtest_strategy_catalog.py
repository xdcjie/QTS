"""Backtest strategy option catalog sourced from runtime config files."""

from __future__ import annotations

from pathlib import Path

from qts.application.dto import BacktestStrategyOptionDTO
from qts.runtime.config import BacktestRuntimeConfig
from qts.runtime.config_loader import BacktestConfigLoader


class BacktestStrategyCatalog:
    """Expose runnable backtest configurations as strategy options."""

    def __init__(self, *, config_dir: Path = Path("configs")) -> None:
        """Initialize the catalog rooted at the given config directory."""
        self._config_dir = config_dir

    def list_options(self) -> tuple[BacktestStrategyOptionDTO, ...]:
        """List valid backtest configs in deterministic label order."""
        if not self._config_dir.exists():
            return ()
        options = [
            option
            for path in sorted(self._config_dir.glob("backtest*.yaml"))
            if (option := self._option_from_path(path)) is not None
        ]
        return tuple(sorted(options, key=lambda option: option.label))

    def _option_from_path(self, path: Path) -> BacktestStrategyOptionDTO | None:
        """Parse one config file into a UI/API strategy option."""
        try:
            config = BacktestConfigLoader.from_path(path)
        except (KeyError, OSError, TypeError, ValueError):
            return None
        label = self._label_for_config(path, config)
        return BacktestStrategyOptionDTO(label=label, config_path=str(path))

    @staticmethod
    def _label_for_config(path: Path, config: BacktestRuntimeConfig) -> str:
        """Return the operator-facing label for one backtest config."""
        if config.strategy is not None and config.strategy.strategy_id is not None:
            return config.strategy.strategy_id
        if config.strategy_config_path is not None:
            return config.strategy_config_path.stem
        return path.stem


__all__ = ["BacktestStrategyCatalog"]
