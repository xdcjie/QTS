from __future__ import annotations

import argparse
import ast
import html
import re
from dataclasses import dataclass, field
from pathlib import Path

START_MARKER = "<!-- SOURCE_INVENTORY_START -->"
END_MARKER = "<!-- SOURCE_INVENTORY_END -->"
SOURCE_ROOTS = (Path("backend/src/qts"), Path("frontend/src"))
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".css", ".md"}
STALE_GENERATED_DOC_TOKENS = (
    "Boundary placeholder",
    "live-beta",
    "backend/src/qts/runtime/config.py",
    "LiveRuntimeSession",
    "fake or real boundary adapters",
)


@dataclass(frozen=True)
class SymbolInfo:
    kind: str
    name: str
    line: int
    owner: str
    role: str
    necessity: str


@dataclass(frozen=True)
class FileInfo:
    path: Path
    purpose: str
    classes: tuple[SymbolInfo, ...] = field(default_factory=tuple)
    functions: tuple[SymbolInfo, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ClassIndexInfo:
    path: Path
    source_path: str
    name: str
    line: int
    methods: tuple[tuple[str, int], ...]


def collect_inventory(repo_root: Path) -> tuple[FileInfo, ...]:
    files: list[FileInfo] = []
    for root in SOURCE_ROOTS:
        source_root = repo_root / root
        if not source_root.exists():
            continue
        for path in sorted(source_root.rglob("*")):
            if not _is_source_file(path):
                continue
            relative_path = path.relative_to(repo_root)
            if path.suffix == ".py":
                files.append(_collect_python_file(path, relative_path))
            elif path.suffix in {".ts", ".tsx"}:
                files.append(_collect_typescript_file(path, relative_path))
            else:
                files.append(
                    FileInfo(path=relative_path, purpose=_fallback_file_purpose(relative_path))
                )
    return tuple(files)


def collect_class_index(repo_root: Path) -> tuple[ClassIndexInfo, ...]:
    classes: list[ClassIndexInfo] = []
    source_root = repo_root / "backend/src/qts"
    if not source_root.exists():
        return ()
    for path in sorted(source_root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        relative_path = path.relative_to(repo_root)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(
                    ClassIndexInfo(
                        path=Path("qts") / path.relative_to(source_root),
                        source_path=relative_path.as_posix(),
                        name=node.name,
                        line=node.lineno,
                        methods=_core_methods(node),
                    )
                )
    return tuple(classes)


def render_current_class_locations_section(repo_root: Path) -> str:
    classes = collect_class_index(repo_root)
    by_path: dict[Path, list[ClassIndexInfo]] = {}
    for class_info in classes:
        by_path.setdefault(class_info.path, []).append(class_info)

    lines = [
        '        <details class="inventory-group">',
        "          <summary><span>自动同步补充 · current class locations</span>"
        f'<span class="badge shared">{len(classes)} classes</span></summary>',
        "          <ul>",
    ]
    for path, path_classes in by_path.items():
        class_fragments = [
            f"<code>{_esc(class_info.name)}</code> "
            f'<span class="location">{_esc(class_info.source_path)}:{class_info.line}</span>'
            for class_info in path_classes
        ]
        lines.append(
            f"          <li><code>{_esc(path.as_posix())}</code> -> "
            f"{', '.join(class_fragments)}</li>"
        )
    lines.extend(["          </ul>", "        </details>"])
    return "\n".join(lines)


def render_core_class_methods_section(repo_root: Path) -> str:
    classes = collect_class_index(repo_root)
    lines = [
        '        <details class="inventory-group">',
        "          <summary><span>自动同步补充 · core class methods</span>"
        f'<span class="badge shared">{len(classes)} classes</span></summary>',
        '          <ul class="method-index">',
    ]
    for class_info in classes:
        if class_info.methods:
            methods = ", ".join(
                f"<code>{_esc(method_name)}:{method_line}</code>"
                for method_name, method_line in class_info.methods
            )
        else:
            methods = '<span class="muted">no public/core methods</span>'
        lines.append(
            f"          <li><code>{_esc(class_info.name)}</code> "
            f'<span class="location">{_esc(class_info.source_path)}:{class_info.line}</span> '
            f"-> {methods}</li>"
        )
    lines.extend(["          </ul>", "        </details>"])
    return "\n".join(lines)


def render_source_inventory_section(repo_root: Path) -> str:
    inventory = collect_inventory(repo_root)
    class_count = sum(len(file.classes) for file in inventory)
    function_count = sum(len(file.functions) for file in inventory)
    backend_count = sum(1 for file in inventory if file.path.parts[:2] == ("backend", "src"))
    frontend_count = sum(1 for file in inventory if file.path.parts[:2] == ("frontend", "src"))

    lines = [
        START_MARKER,
        '<section id="source-inventory">',
        '  <div class="section-head">',
        "    <div>",
        '      <p class="eyebrow">Source Inventory</p>',
        "      <h2>src 文件、类、函数清单</h2>",
        '      <p class="section-note">',
        "        该区块由 <code>scripts/update_project_panorama_source_index.py</code> 从",
        "        <code>backend/src/qts</code> 和 <code>frontend/src</code> 生成；"
        "它是源码生成的单一实现清单。作用说明优先取 docstring，",
        "        无 docstring 时按名称、签名和所在边界推断，作为快速导航和评审入口；"
        "不得手写保留旧路径或历史架构名称。",
        "      </p>",
        "    </div>",
        '    <div class="inventory-stats" aria-label="source inventory summary">',
        f"      <span>{len(inventory)} files</span>",
        f"      <span>{class_count} classes</span>",
        f"      <span>{function_count} functions</span>",
        f"      <span>{backend_count} backend</span>",
        f"      <span>{frontend_count} frontend</span>",
        "    </div>",
        "  </div>",
        '  <div class="inventory-list">',
    ]
    for file_info in inventory:
        lines.extend(_render_file(file_info))
    lines.extend(["  </div>", "</section>", END_MARKER])
    return "\n".join(lines)


def update_html(repo_root: Path, html_path: Path) -> bool:
    path = repo_root / html_path
    original = path.read_text(encoding="utf-8")
    rendered = render_source_inventory_section(repo_root)
    replacement = (
        f"{START_MARKER}\n{rendered.split(chr(10), 1)[1].rsplit(chr(10), 1)[0]}\n{END_MARKER}"
    )
    if START_MARKER in original and END_MARKER in original:
        updated = re.sub(
            rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
            replacement,
            original,
            flags=re.S,
        )
    else:
        if '      <section id="files">' in original:
            updated = original.replace(
                '      <section id="files">',
                f'{replacement}\n\n      <section id="files">',
            )
        elif '      <p class="footnote">' in original:
            updated = original.replace(
                '      <p class="footnote">',
                f'{replacement}\n\n      <p class="footnote">',
            )
        else:
            raise ValueError(f"Could not find source inventory insertion point in {html_path}")
    if 'href="#source-inventory"' not in updated:
        updated = updated.replace(
            '<a href="#files">代码索引</a>',
            '<a href="#source-inventory">src 清单</a>\n        <a href="#files">代码索引</a>',
        )
    updated = _update_class_index_sections(repo_root, updated)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def find_stale_generated_doc_tokens(text: str) -> tuple[str, ...]:
    return tuple(token for token in STALE_GENERATED_DOC_TOKENS if token in text)


def _update_class_index_sections(repo_root: Path, text: str) -> str:
    if "自动同步补充 · current class locations" not in text:
        return text
    updated = re.sub(
        r'        <details class="inventory-group">\n'
        r"          <summary><span>自动同步补充 · current class locations</span>"
        r".*?</details>",
        render_current_class_locations_section(repo_root),
        text,
        flags=re.S,
    )
    return re.sub(
        r'        <details class="inventory-group">\n'
        r"          <summary><span>自动同步补充 · core class methods</span>"
        r".*?</details>",
        render_core_class_methods_section(repo_root),
        updated,
        flags=re.S,
    )


def _core_methods(node: ast.ClassDef) -> tuple[tuple[str, int], ...]:
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
    methods: list[tuple[str, int]] = []
    for child in node.body:
        if not isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if child.name.startswith("_") and child.name not in core_dunders:
            continue
        suffix = " property" if _has_property_decorator(child) else "()"
        prefix = "async " if isinstance(child, ast.AsyncFunctionDef) else ""
        methods.append((f"{prefix}{child.name}{suffix}", child.lineno))
    return tuple(methods)


def _has_property_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == "property":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "setter":
            return True
    return False


def _render_file(file_info: FileInfo) -> list[str]:
    class_count = len(file_info.classes)
    function_count = len(file_info.functions)
    lines = [
        '    <details class="inventory-file">',
        "      <summary>",
        f"        <code>{_esc(str(file_info.path))}</code>",
        '        <span class="inventory-counts">',
        f"          <span>{class_count} class{'es' if class_count != 1 else ''}</span>",
        f"          <span>{function_count} function{'s' if function_count != 1 else ''}</span>",
        "        </span>",
        "      </summary>",
        '      <div class="inventory-body">',
        f"        <p><strong>文件作用：</strong>{_esc(file_info.purpose)}</p>",
        "        <p><strong>必要性：</strong>作为该路径所属边界的源码或说明入口，"
        "让实现、评审和测试可以定位到唯一责任单元。</p>",
    ]
    if file_info.classes:
        lines.append('        <div class="inventory-subsection">')
        lines.append("          <h3>类</h3>")
        lines.append('          <table class="inventory-table">')
        lines.append(
            "            <thead><tr><th>类</th><th>位置</th>"
            "<th>作用</th><th>必要性</th></tr></thead>"
        )
        lines.append("            <tbody>")
        for cls in file_info.classes:
            lines.append(_render_symbol_row(cls))
        lines.append("            </tbody>")
        lines.append("          </table>")
        lines.append("        </div>")
    if file_info.functions:
        lines.append('        <div class="inventory-subsection">')
        lines.append("          <h3>函数 / 方法</h3>")
        lines.append('          <table class="inventory-table">')
        lines.append(
            "            <thead><tr><th>函数</th><th>位置</th>"
            "<th>作用</th><th>必要性</th></tr></thead>"
        )
        lines.append("            <tbody>")
        for function in file_info.functions:
            lines.append(_render_symbol_row(function))
        lines.append("            </tbody>")
        lines.append("          </table>")
        lines.append("        </div>")
    lines.extend(["      </div>", "    </details>"])
    return lines


def _render_symbol_row(symbol: SymbolInfo) -> str:
    return (
        "              <tr>"
        f"<td><code>{_esc(symbol.name)}</code></td>"
        f"<td>{_esc(symbol.owner)}:{symbol.line}</td>"
        f"<td>{_esc(symbol.role)}</td>"
        f"<td>{_esc(symbol.necessity)}</td>"
        "</tr>"
    )


def _collect_python_file(path: Path, relative_path: Path) -> FileInfo:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(relative_path))
    parent_by_id: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parent_by_id[id(child)] = parent

    classes: list[SymbolInfo] = []
    functions: list[SymbolInfo] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(_python_class_info(node, relative_path))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            owner = _python_owner(node, parent_by_id)
            functions.append(_python_function_info(node, owner))

    classes.sort(key=lambda item: (item.line, item.name))
    functions.sort(key=lambda item: (item.line, item.name))
    module_doc = ast.get_docstring(tree)
    return FileInfo(
        path=relative_path,
        purpose=_first_sentence(module_doc) or _fallback_file_purpose(relative_path),
        classes=tuple(classes),
        functions=tuple(functions),
    )


def _python_class_info(node: ast.ClassDef, relative_path: Path) -> SymbolInfo:
    bases = [_name_from_expr(base) for base in node.bases]
    role = _first_sentence(ast.get_docstring(node)) or _class_role(node.name, bases)
    return SymbolInfo(
        kind="class",
        name=node.name,
        line=node.lineno,
        owner=relative_path.stem,
        role=role,
        necessity=_class_necessity(node.name, bases),
    )


def _python_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef, owner: str) -> SymbolInfo:
    role = _first_sentence(ast.get_docstring(node)) or _function_role(node.name, owner)
    return SymbolInfo(
        kind="function",
        name=node.name,
        line=node.lineno,
        owner=owner,
        role=role,
        necessity=_function_necessity(node.name, owner),
    )


def _python_owner(
    node: ast.FunctionDef | ast.AsyncFunctionDef, parent_by_id: dict[int, ast.AST]
) -> str:
    owners: list[str] = []
    current: ast.AST | None = parent_by_id.get(id(node))
    while current is not None:
        if isinstance(current, ast.ClassDef):
            owners.append(current.name)
        elif isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
            owners.append(f"{current.name}.<locals>")
        current = parent_by_id.get(id(current))
    return ".".join(reversed(owners)) or "module"


def _collect_typescript_file(path: Path, relative_path: Path) -> FileInfo:
    lines = path.read_text(encoding="utf-8").splitlines()
    classes: list[SymbolInfo] = []
    functions: list[SymbolInfo] = []
    class_stack: list[tuple[str, int]] = []
    brace_depth = 0

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            brace_depth += _brace_delta(line)
            continue

        class_match = re.match(r"(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", stripped)
        if class_match:
            name = class_match.group(1)
            classes.append(
                SymbolInfo(
                    kind="class",
                    name=name,
                    line=index,
                    owner=relative_path.stem,
                    role=_class_role(name, []),
                    necessity=_class_necessity(name, []),
                )
            )
            class_stack.append((name, brace_depth + stripped.count("{") - stripped.count("}")))

        function_name = _typescript_function_name(stripped)
        if function_name:
            owner = class_stack[-1][0] if class_stack else "module"
            functions.append(
                SymbolInfo(
                    kind="function",
                    name=function_name,
                    line=index,
                    owner=owner,
                    role=_function_role(function_name, owner, relative_path),
                    necessity=_function_necessity(function_name, owner),
                )
            )

        brace_depth += _brace_delta(line)
        while class_stack and brace_depth < class_stack[-1][1]:
            class_stack.pop()

    return FileInfo(
        path=relative_path,
        purpose=_fallback_file_purpose(relative_path),
        classes=tuple(classes),
        functions=tuple(functions),
    )


def _typescript_function_name(stripped: str) -> str | None:
    patterns = [
        r"(?:export\s+)?(?:default\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(",
        r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^=]*\)|[A-Za-z_$][\w$]*)\s*=>",
        r"(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*[:\w\s<>,|.[\]?]*\{",
    ]
    for pattern in patterns:
        match = re.match(pattern, stripped)
        if match and match.group(1) not in {"if", "for", "while", "switch", "catch", "return"}:
            return match.group(1)
    return None


def _brace_delta(line: str) -> int:
    return line.count("{") - line.count("}")


def _is_source_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if "__pycache__" in path.parts:
        return False
    return path.suffix in SOURCE_SUFFIXES


def _first_sentence(text: str | None) -> str:
    if not text:
        return ""
    normalized = " ".join(text.strip().split())
    match = re.search(r"(.+?[.!?。！？])(?:\s|$)", normalized)
    return match.group(1) if match else normalized


def _fallback_file_purpose(path: Path) -> str:
    text = str(path)
    if path.name == "AGENTS.md":
        return "定义该目录下 Codex 工作规则和架构约束。"
    if path.suffix == ".css":
        return "定义前端控制台的全局样式、布局和组件视觉规则。"
    if "frontend/src/components" in text:
        return f"实现前端控制台的 {_readable_stem(path.stem)} 视图组件。"
    if "frontend/src/api" in text:
        return "封装前端到后端 API 的调用边界。"
    if "frontend/src/hooks" in text:
        return "封装前端可复用 React hook。"
    if path.name == "__init__.py":
        return "声明 Python 包边界并导出该包的稳定入口。"
    package = ".".join(path.with_suffix("").parts)
    return f"承载 {package} 边界内的实现、契约或适配逻辑。"


def _class_role(name: str, bases: list[str]) -> str:
    if name.endswith("Actor"):
        return "定义 actor 消息处理边界及其生命周期状态。"
    if name.endswith(("Config", "Settings")):
        return "集中配置输入、默认值和边界校验。"
    if name.endswith(("Request", "Response", "Event", "Command", "DTO", "Schema")):
        return "定义跨层传递的数据契约。"
    if name.endswith(("Error", "Exception")) or "Exception" in bases:
        return "定义可区分、可捕获的错误类型。"
    if "Protocol" in bases or name.endswith("Protocol"):
        return "定义实现可替换的接口契约。"
    return f"定义 {_readable_stem(name)} 概念及其相关状态或行为。"


def _class_necessity(name: str, bases: list[str]) -> str:
    if name.endswith("Actor"):
        return "保持 actor-owned state 只在消息边界内变化，避免跨 actor 直接调用业务方法。"
    if name.endswith(("Config", "Settings")):
        return "把配置解析和校验收口到拥有者，避免调用方复制装配规则。"
    if name.endswith(("Request", "Response", "Event", "Command", "DTO", "Schema")):
        return "提供稳定边界对象，避免 API、runtime 或 adapter 直接共享内部结构。"
    if "Protocol" in bases or name.endswith("Protocol"):
        return "隔离具体实现，支持 backtest、paper、live 或测试替身替换。"
    return "用显式类型封装该概念的责任，减少字典、散落参数和跨模块隐式约定。"


def _function_role(name: str, owner: str, path: Path | None = None) -> str:
    readable = _readable_stem(name)
    if path and "frontend/src/components" in str(path):
        return f"渲染或辅助渲染 {_readable_stem(path.stem)} 控制台视图。"
    if name in {"__init__", "constructor"}:
        return "初始化对象依赖、配置和内部状态。"
    if name == "__post_init__":
        return "完成 dataclass 构造后的派生字段、归一化或不变量校验。"
    if name.startswith("from_"):
        return f"从 {readable.removeprefix('from ')} 输入构造领域对象或边界对象。"
    if name.startswith("to_"):
        return f"把内部对象转换为 {readable.removeprefix('to ')} 表示。"
    if name.startswith(("validate", "assert", "ensure")):
        return "校验输入、状态或领域不变量。"
    if name.startswith(("resolve", "normalize", "map", "convert")):
        return "解析、归一化或映射跨边界数据。"
    if name.startswith(("handle", "on_", "apply")):
        return "处理消息、事件或状态变更。"
    if name.startswith(("start", "stop", "run", "close", "shutdown")):
        return "驱动生命周期或运行流程。"
    if name.startswith(("get", "list", "fetch", "load", "read")):
        return "读取或加载调用方需要的数据视图。"
    if name.startswith(("set", "update", "record", "append")):
        return "更新受控状态或记录事件。"
    if owner != "module":
        return f"实现 {owner} 的 {readable} 行为。"
    return f"提供模块级 {readable} 操作。"


def _function_necessity(name: str, owner: str) -> str:
    if name.startswith("_"):
        return "封装局部实现步骤，降低公共流程复杂度；保留时需符合项目私有 helper 边界规则。"
    if name in {"__init__", "__post_init__", "constructor"}:
        return "确保对象一创建就满足依赖、默认值和不变量要求。"
    if owner != "module":
        return "把行为放在拥有该状态或契约的类上，符合项目 OOP ownership 规则。"
    return "提供模块的显式调用入口，供测试、框架入口或相邻边界复用。"


def _name_from_expr(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _name_from_expr(node.value)
    return ast.unparse(node)


def _readable_stem(name: str) -> str:
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    words = words.replace("_", " ").replace("-", " ")
    return " ".join(words.lower().split())


def _esc(value: str) -> str:
    return html.escape(value, quote=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--html", type=Path, default=Path("project_panorama.html"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    html_path = repo_root / args.html
    original = html_path.read_text(encoding="utf-8")
    expected = render_source_inventory_section(repo_root)
    current_match = re.search(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        original,
        flags=re.S,
    )
    if args.check:
        stale_tokens = find_stale_generated_doc_tokens(original)
        if stale_tokens:
            joined = ", ".join(stale_tokens)
            print(f"{args.html} contains stale generated documentation token(s): {joined}")
            return 1
        if current_match is None or current_match.group(0) != expected:
            print(f"{args.html} source inventory is stale")
            return 1
        if "自动同步补充 · current class locations" in original and (
            render_current_class_locations_section(repo_root) not in original
            or render_core_class_methods_section(repo_root) not in original
        ):
            print(f"{args.html} class index is stale")
            return 1
        return 0
    changed = update_html(repo_root, args.html)
    status = "updated" if changed else "already current"
    print(f"{args.html} {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
