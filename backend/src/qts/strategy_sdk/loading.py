"""Strategy class loading by config-encoded class path.

Owns the dynamic-import concern (``importlib`` / ``sys`` / file-spec loading)
that turns a ``module:Class`` or ``module.Class`` path into an instantiated
``Strategy``. Kept config-agnostic (it takes a class path + params, not a
config object) so it can live in the Strategy SDK without depending on runtime
config types.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

from qts.strategy_sdk.strategy import Strategy


class StrategyLoader:
    """Load and instantiate user ``Strategy`` classes from config-encoded paths."""

    def load(self, strategy_class: str, params: Mapping[str, Any]) -> Strategy:
        """Load a Strategy by its config-encoded class path and instantiate it.

        Accepts both ``module.path:ClassName`` and ``module.path.ClassName``
        spellings. Raises ``ValueError`` for a malformed path or a missing
        class, and ``TypeError`` when the named symbol is not a ``Strategy``
        subclass.
        """
        module_name, separator, class_name = strategy_class.partition(":")
        if not separator:
            module_name, _, class_name = strategy_class.rpartition(".")
        if not module_name or not class_name:
            raise ValueError("strategy_class must be 'module:Class' or 'module.Class'")
        module = self._import_strategy_module(module_name)
        strategy_type = self._strategy_type_from_module(module, class_name)
        return strategy_type(**dict(params))

    @staticmethod
    def _import_strategy_module(module_name: str) -> ModuleType:
        try:
            return importlib.import_module(module_name)
        except ModuleNotFoundError:
            module_path = Path(*module_name.split(".")).with_suffix(".py")
            if not module_path.exists():
                raise
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                raise
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception:
                sys.modules.pop(module_name, None)
                raise
            return module

    @staticmethod
    def _strategy_type_from_module(module: ModuleType, class_name: str) -> type[Strategy]:
        strategy_type = vars(module).get(class_name)
        if strategy_type is None:
            raise ValueError(
                f"strategy class '{class_name}' not found in module '{module.__name__}'"
            )
        if not isinstance(strategy_type, type):
            raise TypeError(f"{class_name} in module '{module.__name__}' is not a class")
        if not issubclass(strategy_type, Strategy):
            raise TypeError(
                f"{class_name} in module '{module.__name__}' must subclass "
                "qts.strategy_sdk.Strategy"
            )
        return strategy_type


__all__ = ["StrategyLoader"]
