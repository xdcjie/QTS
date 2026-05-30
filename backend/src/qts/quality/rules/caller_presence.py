"""CallerPresenceRule — every baseline production symbol must have a non-test caller.

Closes the recurring "shipped but unwired" anti-pattern: every public class
listed in the class inventory baseline must be referenced by at least one
non-test module under ``backend/src/qts/``, ``scripts/``, or
``examples/``. Symbols that are legitimately library-only or framework-only
can be deferred via ``docs/plan/wiring_deferrals.md``.

Auto-detected exemptions:
- ``Protocol`` classes — never instantiated; their callers are concrete
  implementations, which the class inventory tracks separately.
- ``StrEnum`` / ``IntEnum`` / ``Enum`` subclasses — they exist as value
  carriers, not as call targets.
- Exception subclasses — caught by type rather than invoked.
- Value objects referenced as return / attribute / parameter annotations
  in their defining module — the owner type is the wiring signal.

Implementation note: this rule scans source files once per ``make
guardrails`` invocation. The scan reads each non-test ``.py`` file under
the relevant roots, extracts top-level identifier references, and builds
a reverse index from ``ClassName`` to caller paths. Performance is
acceptable up to a few thousand baseline symbols × a few thousand
source files; if that ratio grows, switch to AST symbol resolution.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from qts.quality.guardrails import GuardrailViolation

_BASELINE_PATH = Path("artifacts/quality/class_inventory_baseline.json")
_DEFERRALS_PATH = Path("docs/plan/wiring_deferrals.md")
_DEFERRAL_LINE_PATTERN = re.compile(
    r"^(?P<symbol>\S+)\s+expires=(?P<expires>\d{4}-\d{2}-\d{2})\s+target=(?P<target>\S+)$"
)
_EXPIRED_DEFERRAL_CODE = "EXPIRED_DEFERRAL"
_SEARCH_ROOTS = (
    Path("backend/src/qts"),
    Path("scripts"),
    Path("examples"),
)
_NAME_REFERENCE_PATTERN = re.compile(r"\b([A-Z][A-Za-z0-9_]+)\b")
_ENUM_BASE_NAMES = frozenset({"Enum", "StrEnum", "IntEnum", "Flag", "IntFlag"})
_EXCEPTION_BASE_NAMES = frozenset(
    {
        "Exception",
        "ValueError",
        "TypeError",
        "KeyError",
        "RuntimeError",
        "LookupError",
        "AttributeError",
        "ImportError",
        "NotImplementedError",
    }
)


@dataclass(frozen=True, slots=True)
class _BaselineEntry:
    module: str
    name: str
    fq_symbol: str


@dataclass(frozen=True, slots=True)
class _DeferralEntry:
    symbol: str
    expires_on: date
    target: str


class CallerPresenceRule:
    """Reject baseline-listed public symbols without a non-test caller."""

    code = "MISSING_PRODUCTION_CALLER"

    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root or Path(".")

    def check(
        self,
        *,
        relative_path: Path,
        qts_relative_path: Path,
        tree: ast.AST,
    ) -> list[GuardrailViolation]:
        """Per-file check is a no-op; the work happens in check_repository."""
        del relative_path, qts_relative_path, tree
        return []

    def check_repository(self, repo_root: Path) -> list[GuardrailViolation]:
        """Perform the repository-wide caller-presence check."""
        baseline = self._load_baseline(repo_root)
        if not baseline:
            return []
        deferrals = self._load_deferrals(repo_root)
        caller_index = self._build_caller_index(repo_root)
        value_object_cache: dict[Path, set[str]] = {}
        today = date.today()

        violations: list[GuardrailViolation] = []
        for symbol, deferral in deferrals.items():
            if deferral.expires_on < today:
                violations.append(
                    GuardrailViolation(
                        code=_EXPIRED_DEFERRAL_CODE,
                        path=str(_DEFERRALS_PATH),
                        line=1,
                        message=(
                            f"wiring deferral expired on {deferral.expires_on.isoformat()}; "
                            f"add a real caller or refresh the expiry "
                            f"(target={deferral.target})."
                        ),
                        symbol=symbol,
                    )
                )

        for entry in baseline:
            if entry.fq_symbol in deferrals:
                continue
            defining_file = self._defining_file(repo_root, entry)
            if defining_file is None:
                continue
            class_node = self._file_class_node(defining_file, entry.name)
            if class_node is None:
                continue
            if self._is_protocol_class(class_node):
                continue
            if self._is_enum_class(class_node):
                continue
            if self._is_exception_class(class_node):
                continue
            value_objects = value_object_cache.setdefault(
                defining_file, self._value_object_type_names(defining_file)
            )
            if entry.name in value_objects:
                continue
            caller_files = caller_index.get(entry.name, frozenset())
            non_defining_callers = {p for p in caller_files if p != defining_file}
            if non_defining_callers:
                continue
            # Owner-use: a class consumed by a co-located owner in its own module
            # (e.g. a value object a sibling class constructs/calls) is wired --
            # the owner is the durable signal (CLAUDE.md §11). Such a reference is
            # outside the class's own body, so it is distinct from a self-reference.
            if self._defining_module_uses_symbol(defining_file, class_node, entry.name):
                continue
            violations.append(
                GuardrailViolation(
                    code=self.code,
                    path=str(defining_file.relative_to(repo_root)),
                    line=class_node.lineno,
                    message=(
                        "production symbol has no non-test caller under "
                        "backend/src/qts, scripts, or examples; add a real "
                        "caller or list the FQ symbol in "
                        "docs/plan/wiring_deferrals.md."
                    ),
                    symbol=entry.fq_symbol,
                )
            )
        return violations

    @staticmethod
    def _load_baseline(repo_root: Path) -> tuple[_BaselineEntry, ...]:
        path = repo_root / _BASELINE_PATH
        if not path.exists():
            return ()
        payload = json.loads(path.read_text(encoding="utf-8"))
        classes = payload.get("production_classes", [])
        entries: list[_BaselineEntry] = []
        for symbol in classes:
            if "." not in symbol:
                continue
            module, _, name = symbol.rpartition(".")
            entries.append(_BaselineEntry(module=module, name=name, fq_symbol=symbol))
        return tuple(entries)

    @staticmethod
    def _load_deferrals(repo_root: Path) -> dict[str, _DeferralEntry]:
        """Parse the wiring_deferrals.md fenced code block into entries.

        Each line must match ``<symbol>  expires=<YYYY-MM-DD>  target=<id>``.
        Comment lines (``#`` prefix) and blank lines inside the block are
        skipped. Mis-formatted lines raise so the deferral schema cannot
        silently drift.
        """
        path = repo_root / _DEFERRALS_PATH
        if not path.exists():
            return {}
        entries: dict[str, _DeferralEntry] = {}
        in_code_block = False
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block or not stripped or stripped.startswith("#"):
                continue
            match = _DEFERRAL_LINE_PATTERN.match(stripped)
            if match is None:
                raise ValueError(
                    f"wiring_deferrals.md line does not match required format: {stripped!r}"
                )
            entry = _DeferralEntry(
                symbol=match.group("symbol"),
                expires_on=date.fromisoformat(match.group("expires")),
                target=match.group("target"),
            )
            entries[entry.symbol] = entry
        return entries

    @staticmethod
    def _is_protocol_class(node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "Protocol":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "Protocol":
                return True
        return False

    @staticmethod
    def _is_enum_class(node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in _ENUM_BASE_NAMES:
                return True
            if isinstance(base, ast.Attribute) and base.attr in _ENUM_BASE_NAMES:
                return True
        return False

    @staticmethod
    def _is_exception_class(node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in _EXCEPTION_BASE_NAMES:
                return True
        return False

    @staticmethod
    def _file_tree(file_path: Path) -> ast.Module | None:
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError:
            return None
        try:
            return ast.parse(source)
        except SyntaxError:
            return None

    @classmethod
    def _file_class_node(cls, file_path: Path, class_name: str) -> ast.ClassDef | None:
        tree = cls._file_tree(file_path)
        if tree is None:
            return None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    @staticmethod
    def _annotation_names(node: ast.AST | None) -> set[str]:
        names: set[str] = set()
        if node is None:
            return names
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
        return names

    @classmethod
    def _value_object_type_names(cls, file_path: Path) -> set[str]:
        """Return class names that appear as return / attribute annotations in the file.

        A class referenced as a return type from another class's method, or as a
        typed attribute / parameter of another class, is consumed indirectly
        through the owner's API. The owner is the durable wiring signal; the
        value object rides along.
        """
        tree = cls._file_tree(file_path)
        if tree is None:
            return set()
        references: set[str] = set()
        for class_node in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            for item in ast.walk(class_node):
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    references |= cls._annotation_names(item.returns)
                    for arg in item.args.args:
                        references |= cls._annotation_names(arg.annotation)
                    for arg in item.args.kwonlyargs:
                        references |= cls._annotation_names(arg.annotation)
                elif isinstance(item, ast.AnnAssign):
                    references |= cls._annotation_names(item.annotation)
        return references

    @staticmethod
    def _build_caller_index(repo_root: Path) -> dict[str, frozenset[Path]]:
        """Build identifier → caller file paths under the search roots."""
        index: dict[str, set[Path]] = {}
        for root in _SEARCH_ROOTS:
            root_path = repo_root / root
            if not root_path.exists():
                continue
            for path in root_path.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                if "/tests/" in str(path) or path.name.startswith("test_"):
                    continue
                try:
                    source = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                # A bare re-export (an ``import`` of a symbol, or its name in
                # ``__all__``) forwards the symbol without exercising it, so it
                # must not count as a caller. Stripping import / ``__all__`` lines
                # closes the loophole where a symbol satisfied the gate purely by
                # being re-exported from a package ``__init__``; a module that both
                # imports and uses a symbol still counts via its use site.
                scannable = CallerPresenceRule._caller_reference_source(source)
                for match in _NAME_REFERENCE_PATTERN.findall(scannable):
                    index.setdefault(match, set()).add(path)
        return {name: frozenset(paths) for name, paths in index.items()}

    @staticmethod
    def _caller_reference_source(source: str) -> str:
        """Return ``source`` with ``import`` statements and ``__all__`` removed.

        Re-exports forward a symbol without exercising it; dropping the lines they
        span (everything else -- real use sites -- is preserved) prevents a bare
        re-export from counting as a caller. Falls back to the raw source if the
        file does not parse.
        """
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return source
        excluded: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                excluded.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
            elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                excluded.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
        return "\n".join(
            line
            for number, line in enumerate(source.splitlines(), start=1)
            if number not in excluded
        )

    @classmethod
    def _defining_module_uses_symbol(
        cls, defining_file: Path, class_node: ast.ClassDef, name: str
    ) -> bool:
        """Return whether the defining module references ``name`` outside its class body.

        A reference outside the class's own ``lineno..end_lineno`` range (and
        outside imports / ``__all__``) is a co-located owner using the symbol --
        the wiring signal -- as opposed to the class merely referring to itself.
        """
        tree = cls._file_tree(defining_file)
        if tree is None:
            return False
        try:
            source = defining_file.read_text(encoding="utf-8")
        except OSError:
            return False
        excluded: set[int] = set(
            range(class_node.lineno, (class_node.end_lineno or class_node.lineno) + 1)
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import | ast.ImportFrom):
                excluded.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
            elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            ):
                excluded.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        return any(
            pattern.search(line)
            for number, line in enumerate(source.splitlines(), start=1)
            if number not in excluded
        )

    @staticmethod
    def _defining_file(repo_root: Path, entry: _BaselineEntry) -> Path | None:
        """Map a fully-qualified module to its source file."""
        relative_module = entry.module.replace(".", "/")
        candidate = repo_root / "backend/src" / f"{relative_module}.py"
        if candidate.exists():
            return candidate
        candidate_pkg = repo_root / "backend/src" / relative_module / "__init__.py"
        if candidate_pkg.exists():
            return candidate_pkg
        return None


__all__ = ["CallerPresenceRule"]
