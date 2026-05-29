"""Guardrail tests for the layer dependency rule (DR-012).

Lower layers (risk, data, portfolio, execution) must not import the runtime
layer. The runtime layer orchestrates actors and depends downward on these
layers; an upward import reintroduces circular-import risk and violates the
actor-model boundary documented in docs/architecture/dependency_rules.md.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from qts.quality.rules.layering import LayerDependencyRule

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
QTS_ROOT = REPO_ROOT / "backend" / "src" / "qts"


def _check_source(source: str, *, qts_relative: str) -> list[str]:
    tree = ast.parse(source)
    qts_relative_path = Path(qts_relative)
    violations = LayerDependencyRule().check(
        relative_path=Path("backend/src/qts") / qts_relative_path,
        qts_relative_path=qts_relative_path,
        tree=tree,
    )
    return [violation.code for violation in violations]


def test_rule_flags_risk_to_runtime_import() -> None:
    source = "from qts.runtime.actors.account_actor import AccountSnapshot\n"
    codes = _check_source(source, qts_relative="risk/risk_state.py")
    assert codes == ["LAYER_DEPENDENCY"]


def test_rule_flags_plain_runtime_import() -> None:
    source = "import qts.runtime.session\n"
    codes = _check_source(source, qts_relative="execution/foo.py")
    assert codes == ["LAYER_DEPENDENCY"]


@pytest.mark.parametrize("layer", ["risk", "data", "portfolio", "execution"])
def test_rule_flags_every_lower_layer(layer: str) -> None:
    source = "from qts.runtime.dependencies import RuntimeSessionDependencies\n"
    codes = _check_source(source, qts_relative=f"{layer}/module.py")
    assert codes == ["LAYER_DEPENDENCY"]


def test_rule_passes_when_runtime_import_absent() -> None:
    source = (
        "from qts.portfolio.account_snapshot import AccountSnapshot\n"
        "from qts.core.ids import InstrumentId\n"
    )
    assert _check_source(source, qts_relative="risk/risk_state.py") == []


def test_rule_ignores_type_checking_only_runtime_import() -> None:
    source = (
        "from __future__ import annotations\n"
        "from typing import TYPE_CHECKING\n"
        "if TYPE_CHECKING:\n"
        "    from qts.runtime.config import BacktestRuntimeConfig\n"
    )
    assert _check_source(source, qts_relative="data/sources/replay.py") == []


def test_rule_ignores_runtime_layer_self_import() -> None:
    source = "from qts.runtime.actors.account_actor import AccountSnapshot\n"
    assert _check_source(source, qts_relative="runtime/session.py") == []


def _iter_runtime_imports(layer: str) -> list[str]:
    """Return non-TYPE_CHECKING runtime imports under a layer in the real repo."""
    offenders: list[str] = []
    layer_root = QTS_ROOT / layer
    for path in sorted(layer_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        qts_relative_path = path.relative_to(QTS_ROOT)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations = LayerDependencyRule().check(
            relative_path=path.relative_to(REPO_ROOT),
            qts_relative_path=qts_relative_path,
            tree=tree,
        )
        offenders.extend(f"{qts_relative_path}:{v.line}: {v.message}" for v in violations)
    return offenders


def test_qts_risk_imports_no_runtime_in_real_repo() -> None:
    assert _iter_runtime_imports("risk") == []
