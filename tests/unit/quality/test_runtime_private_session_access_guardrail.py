"""QTS-FINAL-012 guardrail: encapsulated RuntimeSession safety state stays private.

``RuntimePrivateAccessRule`` blocks modules other than the session owner and the
safety-port owner from poking the ``_kill_switch_active`` attribute, so the
kill switch is only reachable through ``RuntimeSafetySessionPort``.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.quality.rules import RuntimePrivateAccessRule


def _check(qts_relative: str, source: str) -> list[str]:
    tree = ast.parse(source)
    violations = RuntimePrivateAccessRule().check(
        relative_path=Path("backend/src/qts") / qts_relative,
        qts_relative_path=Path(qts_relative),
        tree=tree,
    )
    return [v.message for v in violations]


def test_flags_external_kill_switch_access() -> None:
    source = "def block(session):\n    return session._kill_switch_active\n"
    messages = _check("runtime/rollback.py", source)
    assert any("_kill_switch_active" in message for message in messages)


def test_flags_external_kill_switch_mutation() -> None:
    source = "def trip(session):\n    session._kill_switch_active = True\n"
    assert _check("runtime/safety_controller.py", source)


def test_allows_session_owner_module() -> None:
    source = "class S:\n    def __init__(self):\n        self._kill_switch_active = False\n"
    assert _check("runtime/session.py", source) == []


def test_allows_safety_port_owner_module() -> None:
    source = "def trip(state):\n    state._kill_switch_active = True\n"
    assert _check("runtime/safety_port.py", source) == []


def test_production_safety_modules_pass_the_rule() -> None:
    rule = RuntimePrivateAccessRule()
    for qts_relative in ("runtime/safety_controller.py", "runtime/rollback.py"):
        path = Path("backend/src/qts") / qts_relative
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations = rule.check(
            relative_path=path,
            qts_relative_path=Path(qts_relative),
            tree=tree,
        )
        assert violations == [], f"{qts_relative} should not access encapsulated session state"
