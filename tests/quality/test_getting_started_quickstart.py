"""Anchor: docs/GETTING_STARTED.md is the canonical onboarding entrypoint.

Domain fact: OPT-66 ships a ≤5-minute new-user path. The doc must
exist, reference the hello-world strategy by its fully-qualified
import path, and explain at minimum: install, write a strategy, run
a backtest, where to read more. Without these gates the doc rots
silently.

Owner: ``docs/GETTING_STARTED.md`` (durable onboarding doc) +
``examples/strategies/hello_world.py`` (the strategy it references).

Forbidden shortcut: documenting a strategy that does not exist, or
swapping the example out without updating the doc.
"""

from __future__ import annotations

from pathlib import Path

DOC = Path("docs/GETTING_STARTED.md")
HELLO_WORLD_MODULE = "examples.strategies.hello_world"


def test_getting_started_doc_exists() -> None:
    assert DOC.exists(), f"missing onboarding doc at {DOC}"


def test_getting_started_doc_references_hello_world_strategy() -> None:
    body = DOC.read_text(encoding="utf-8")
    assert HELLO_WORLD_MODULE in body, (
        f"GETTING_STARTED.md must mention the {HELLO_WORLD_MODULE} import path"
    )


def test_getting_started_doc_covers_required_sections() -> None:
    body = DOC.read_text(encoding="utf-8").lower()
    for required in ("install", "strategy", "backtest", "next"):
        assert required in body, f"GETTING_STARTED.md missing section keyword: {required!r}"


def test_hello_world_strategy_module_importable() -> None:
    import importlib

    module = importlib.import_module(HELLO_WORLD_MODULE)
    assert hasattr(module, "HelloWorldStrategy"), (
        f"{HELLO_WORLD_MODULE} must export HelloWorldStrategy class"
    )
