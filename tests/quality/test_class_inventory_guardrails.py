from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_guardrails_module() -> ModuleType:
    module_path = Path("scripts/verify_guardrails.py")
    spec = importlib.util.spec_from_file_location("verify_guardrails", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_GUARDRAILS = _load_guardrails_module()


def _write(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def _write_baseline(
    root: Path,
    *,
    production_class_count: int,
    production_classes: list[str] | None = None,
    single_field_boundary_justifications: dict[str, str] | None = None,
) -> None:
    path = root / "artifacts/quality/class_inventory_baseline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "production_class_count": production_class_count,
                "production_classes": production_classes or [],
                "single_field_boundary_justifications": (
                    single_field_boundary_justifications or {}
                ),
            }
        ),
        encoding="utf-8",
    )


def _suite_codes(root: Path, *rules: object) -> set[str]:
    suite = _GUARDRAILS.GuardrailSuite(rules=tuple(rules))
    return {violation.code for violation in suite.check(root)}


def test_class_inventory_does_not_exceed_platform_baseline_without_exception(
    tmp_path: Path,
) -> None:
    _write_baseline(
        tmp_path,
        production_class_count=0,
        production_classes=[],
    )
    _write(
        tmp_path,
        "backend/src/qts/application/new_service.py",
        "class NewService:\n    pass\n",
    )

    assert _suite_codes(
        tmp_path,
        _GUARDRAILS.ClassInventoryBudgetRule(repo_root=tmp_path),
    ) == {"CLASS_INVENTORY_BUDGET"}


def test_single_field_dto_requires_boundary_justification(tmp_path: Path) -> None:
    _write_baseline(
        tmp_path,
        production_class_count=1,
        production_classes=["qts.application.dto.new_command.NewCommandDTO"],
    )
    _write(
        tmp_path,
        "backend/src/qts/application/dto/new_command.py",
        "from dataclasses import dataclass\n\n"
        "@dataclass(frozen=True)\n"
        "class NewCommandDTO:\n"
        "    command_id: str\n",
    )

    assert _suite_codes(
        tmp_path,
        _GUARDRAILS.SingleFieldDtoJustificationRule(repo_root=tmp_path),
    ) == {"SINGLE_FIELD_DTO_JUSTIFICATION"}


def test_no_duplicate_dto_names_across_application_and_runtime(tmp_path: Path) -> None:
    _write_baseline(
        tmp_path,
        production_class_count=2,
        production_classes=[
            "qts.application.dto.status.StatusDTO",
            "qts.runtime.status.StatusDTO",
        ],
    )
    _write(
        tmp_path,
        "backend/src/qts/application/dto/status.py",
        "class StatusDTO:\n    pass\n",
    )
    _write(
        tmp_path,
        "backend/src/qts/runtime/status.py",
        "class StatusDTO:\n    pass\n",
    )

    assert _suite_codes(
        tmp_path,
        _GUARDRAILS.DuplicateDtoNameRule(),
    ) == {"DUPLICATE_DTO_NAME"}
