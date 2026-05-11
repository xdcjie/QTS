from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast


def _load_guardrails_module() -> ModuleType:
    module_path = Path("scripts/verify_guardrails.py")
    spec = importlib.util.spec_from_file_location("verify_guardrails", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


run_guardrails = cast(Any, _load_guardrails_module().run_guardrails)


def _write(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _codes(root: Path) -> set[str]:
    return {violation.code for violation in run_guardrails(root)}


def test_guardrails_reject_domain_imports_from_runtime(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/domain/bad.py",
        "from qts.runtime.actor import Actor\n",
    )

    assert _codes(root) == {"IMPORT_BOUNDARY"}


def test_guardrails_reject_strategy_sdk_imports_from_execution(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/strategy_sdk/bad.py",
        "from qts.execution.order_manager import OrderManager\n",
    )

    assert _codes(root) == {"IMPORT_BOUNDARY"}


def test_guardrails_reject_market_data_and_execution_adapter_coupling(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/adapters/bad.py",
        "from qts.execution.order_manager import OrderManager\n",
    )
    _write(
        root,
        "backend/src/qts/execution/adapters/bad.py",
        "from qts.data.adapters.ibkr_market_data import IbkrMarketDataAdapter\n",
    )

    assert _codes(root) == {"ADAPTER_BOUNDARY"}


def test_guardrails_reject_product_specific_identifiers_in_core_implementation(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/bad.py",
        "GC_SESSION_OPEN = '18:00'\n\ndef gc_session_id_for_timestamp():\n    return None\n",
    )

    assert _codes(root) == {"PRODUCT_SPECIFIC_IMPLEMENTATION"}


def test_guardrails_reject_product_symbol_branching_in_core_implementation(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/bad.py",
        "def session_for(root: str) -> str:\n"
        "    if root == 'GC':\n"
        "        return 'special'\n"
        "    return 'generic'\n",
    )

    assert _codes(root) == {"PRODUCT_SPECIFIC_IMPLEMENTATION"}


def test_guardrails_reject_broker_specific_identifiers_outside_boundaries(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/runtime/bad.py",
        "IBKR_GATEWAY_NAME = 'ibkr-paper'\n",
    )

    assert _codes(root) == {"BROKER_SPECIFIC_IMPLEMENTATION"}


def test_guardrails_reject_anchor_helpers_in_backend_source(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/anchor_helper.py",
        "class SessionRollAnchorRow:\n"
        "    pass\n\n"
        "def session_roll_anchor_payload() -> dict[str, object]:\n"
        "    return {}\n",
    )

    assert _codes(root) == {"TEST_SUPPORT_IN_PRODUCTION"}


def test_guardrails_reject_shared_roll_resolution_in_historical_boundary(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/data/historical/session_roll.py",
        "def session_roll_resolution() -> None:\n    return None\n",
    )

    assert _codes(root) == {"SHARED_CAPABILITY_IN_SOURCE_BOUNDARY"}


def test_guardrails_reject_shared_session_resolution_in_backtest_boundary(
    tmp_path: Path,
) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/backtest/session_resolution.py",
        "def session_resolution() -> None:\n    return None\n",
    )

    assert _codes(root) == {"SHARED_CAPABILITY_IN_SOURCE_BOUNDARY"}


def test_guardrails_allow_product_facts_in_registry_providers(tmp_path: Path) -> None:
    root = tmp_path
    _write(
        root,
        "backend/src/qts/registry/providers/comex_gold_calendar_provider.py",
        "GC_SESSION_OPEN = '18:00'\n"
        "class ComexGoldCalendarProvider:\n"
        "    calendar_id = 'COMEX.GC'\n",
    )

    assert run_guardrails(root) == []


def test_guardrails_pass_current_repository() -> None:
    assert run_guardrails(Path(".")) == []
