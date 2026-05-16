from __future__ import annotations

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_guardrails_module() -> ModuleType:
    module_path = Path("scripts/verify_guardrails.py")
    spec = importlib.util.spec_from_file_location("verify_guardrails", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_GUARDRULES_MODULE = _load_guardrails_module()


def _suite_with_platform_freeze(repo_root: Path) -> Any:
    module = _GUARDRULES_MODULE
    return module.GuardrailSuite(rules=(module.PlatformFreezeRule(repo_root=repo_root),))


def _write(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def test_platform_freeze_rejects_unless_exception(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "docs/architecture/platform_freeze_exceptions.yaml",
        "exceptions: []\n",
    )
    _write(
        tmp_path,
        "backend/src/qts/runtime/frozen_candidate.py",
        "class FrozenRuntimeCandidate:\n    pass\n",
    )

    guardrails = _suite_with_platform_freeze(tmp_path)

    assert {violation.code for violation in guardrails.check(tmp_path)} == {"PLATFORM_FREEZE"}


def test_platform_freeze_allows_valid_future_exception(tmp_path: Path) -> None:
    module_name = "qts.runtime.frozen_candidate"
    class_name = "FrozenRuntimeCandidate"
    expiry = (date.today() + timedelta(days=30)).isoformat()
    _write(
        tmp_path,
        "docs/architecture/platform_freeze_exceptions.yaml",
        "exceptions:\n"
        f"  - class_name: {class_name}\n"
        f"    module: {module_name}\n"
        "    reason: temporary migration\n"
        "    owner: platform\n"
        f"    expiry: {expiry}\n",
    )
    _write(
        tmp_path,
        "backend/src/qts/runtime/frozen_candidate.py",
        f"class {class_name}:\n    pass\n",
    )

    guardrails = _suite_with_platform_freeze(tmp_path)

    assert guardrails.check(tmp_path) == []


def test_platform_freeze_rejects_expired_exception(tmp_path: Path) -> None:
    module_name = "qts.runtime.frozen_candidate"
    class_name = "FrozenRuntimeCandidate"
    expiry = (date.today() - timedelta(days=1)).isoformat()
    _write(
        tmp_path,
        "docs/architecture/platform_freeze_exceptions.yaml",
        "exceptions:\n"
        f"  - class_name: {class_name}\n"
        f"    module: {module_name}\n"
        "    reason: temporary migration\n"
        "    owner: platform\n"
        f"    expiry: {expiry}\n",
    )
    _write(
        tmp_path,
        "backend/src/qts/runtime/frozen_candidate.py",
        f"class {class_name}:\n    pass\n",
    )

    guardrails = _suite_with_platform_freeze(tmp_path)

    violations = guardrails.check(tmp_path)
    assert {violation.code for violation in violations} == {"PLATFORM_FREEZE"}
    assert any("expired" in violation.message for violation in violations)


def test_platform_freeze_does_not_apply_to_strategy_and_factors(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "docs/architecture/platform_freeze_exceptions.yaml",
        "exceptions: []\n",
    )
    _write(
        tmp_path,
        "backend/src/qts/strategy/frozen_candidate.py",
        "class StrategyPolicy:\n    pass\n",
    )
    _write(
        tmp_path,
        "backend/src/qts/factors/frozen_candidate.py",
        "class FactorPolicy:\n    pass\n",
    )

    guardrails = _suite_with_platform_freeze(tmp_path)
    assert guardrails.check(tmp_path) == []
