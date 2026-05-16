from __future__ import annotations

import ast
import re
from pathlib import Path

from scripts.update_project_panorama_source_index import (
    END_MARKER,
    START_MARKER,
    render_source_inventory_section,
)


def _production_classes() -> dict[str, set[str]]:
    classes: dict[str, set[str]] = {}
    for path in sorted(Path("backend/src/qts").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.setdefault(node.name, set()).add(path.as_posix())
    return classes


def _core_class_methods() -> list[tuple[str, str, int, list[tuple[str, int]]]]:
    core_dunders = {
        "__init__",
        "__post_init__",
        "__call__",
        "__enter__",
        "__exit__",
        "__iter__",
        "__next__",
        "__len__",
        "__str__",
        "__repr__",
    }
    methods_by_class: list[tuple[str, str, int, list[tuple[str, int]]]] = []
    for path in sorted(Path("backend/src/qts").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            methods: list[tuple[str, int]] = []
            for child in node.body:
                if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if child.name.startswith("_") and child.name not in core_dunders:
                    continue
                suffix = " property" if _has_property_decorator(child) else "()"
                prefix = "async " if isinstance(child, ast.AsyncFunctionDef) else ""
                methods.append((f"{prefix}{child.name}{suffix}", child.lineno))
            methods_by_class.append((node.name, path.as_posix(), node.lineno, methods))
    return methods_by_class


def _has_property_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "property":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "setter":
            return True
    return False


def test_backtest_live_parallel_sequence_documents_all_production_classes() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    missing: list[str] = []
    for path in sorted(Path("backend/src/qts").rglob("*.py")):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                location = f"{path.as_posix()}:{node.lineno}"
                if node.name not in html or location not in html:
                    missing.append(f"{path}:{node.lineno}:{node.name}")

    assert not missing


def test_backtest_live_parallel_sequence_references_only_implemented_classes() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    class_names = set(_production_classes())
    implementation_text = html.split('aria-label="生产类全量索引"', maxsplit=1)[0]

    missing = sorted(
        {
            token
            for token in re.findall(r"<code>([A-Z][A-Za-z0-9_]+)</code>", implementation_text)
            if token not in class_names
        }
    )

    assert missing == []


def test_backtest_live_parallel_sequence_current_implementation_list_maps_classes_to_files() -> (
    None
):
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    classes = _production_classes()
    match = re.search(
        r'aria-label="当前实现清单".*?<ul>(.*?)</ul>',
        html,
        flags=re.DOTALL,
    )
    assert match is not None

    wrong_locations: list[str] = []
    for path, class_fragment in re.findall(
        r"<li><code>(qts/[^<]+\.py)</code> -> (.*?)</li>",
        match.group(1),
        flags=re.DOTALL,
    ):
        source_path = f"backend/src/{path}"
        for class_name in re.findall(r"<code>([A-Z][A-Za-z0-9_]+)</code>", class_fragment):
            if source_path not in classes.get(class_name, set()):
                wrong_locations.append(f"{class_name} listed under {source_path}")

    assert wrong_locations == []


def test_backtest_live_parallel_sequence_documents_core_methods_for_each_class() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"自动同步补充 · core class methods.*?<ul class=\"method-index\">(.*?)</ul>",
        html,
        flags=re.DOTALL,
    )
    assert match is not None
    method_index = match.group(1)

    missing: list[str] = []
    for class_name, path, class_lineno, methods in _core_class_methods():
        class_location = f"{path}:{class_lineno}"
        if class_name not in method_index or class_location not in method_index:
            missing.append(f"{path}:{class_lineno}:{class_name}")
            continue
        for method_name, method_lineno in methods:
            if f"{method_name}:{method_lineno}" not in method_index:
                missing.append(f"{path}:{method_lineno}:{class_name}.{method_name}")

    assert missing == []


def test_backtest_live_parallel_sequence_documents_core_call_chains() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r'aria-label="核心调用链路".*?<ol>(.*?)</ol>',
        html,
        flags=re.DOTALL,
    )
    assert match is not None
    call_chains = match.group(1)

    required_tokens = {
        "BacktestEngine",
        "ReplayMarketDataSource",
        "BacktestActorLoop",
        "RuntimeSession",
        "StreamingMarketDataSource",
        "MarketDataActor",
        "StrategyExecutionPipeline",
        "TargetIntentProcessor",
        "OrderManagerActor",
        "ExecutionActor",
        "AccountActor",
        "RuntimeCommandBus",
        "IbkrMarketDataAdapter",
        "IbkrOrderExecutionAdapter",
        "RuntimeTopologyBuilder",
    }

    missing = sorted(
        token for token in required_tokens if f"<code>{token}</code>" not in call_chains
    )
    assert missing == []


def test_backtest_live_parallel_sequence_source_inventory_is_current() -> None:
    html = Path("docs/architecture/backtest_live_parallel_sequence.html").read_text(
        encoding="utf-8"
    )
    start = html.index(START_MARKER)
    end = html.index(END_MARKER) + len(END_MARKER)

    assert html[start:end] == render_source_inventory_section(Path("."))
    assert "src 文件、类、函数清单" in html
    assert "backend/src/qts/runtime/actors/market_data_actor.py" in html
    assert "frontend/src/App.tsx" in html
