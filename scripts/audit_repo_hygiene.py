#!/usr/bin/env python3
"""Audit QTS repository hygiene without modifying files."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT_MARKERS = {".git", "pyproject.toml", "README.md"}
DEFAULT_OUTPUT = Path("artifacts/repo_hygiene_report.md")
TEXT_SUFFIXES = {".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".yaml", ".yml", ".toml", ".txt", ".sh"}
DOC_STATUS_RE = re.compile(r"^status:\s*(active|done|superseded|abandoned)\s*$", re.I | re.M)
SUSPICIOUS_DOC_RE = re.compile(r"\b(TODO|WIP|draft|deprecated|legacy|superseded|archive|obsolete|temporary|temp|manual)\b|(临时|历史|废弃|计划|归档|过期|待办|草稿)", re.I)
SUSPICIOUS_TEST_RE = re.compile(r"pytest\.mark\.(skip|skipif|xfail)|\b(skip|xfail|TODO|WIP|legacy|deprecated|manual|temporary|temp)\b|(临时|历史|废弃|手工|跳过|待办)", re.I)


@dataclass(frozen=True)
class Finding:
    category: str
    path: str
    detail: str


def run_git(args: Sequence[str], root: Path) -> list[str]:
    try:
        output = subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line for line in output.splitlines() if line]


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if any((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate
    return current


def tracked_files(root: Path) -> list[Path]:
    files = run_git(["ls-files"], root)
    if files:
        return [root / item for item in files]
    return [path for path in root.rglob("*") if path.is_file() and ".git" not in path.parts]


def read_text(path: Path, max_bytes: int = 512_000) -> str:
    try:
        if path.stat().st_size > max_bytes:
            with path.open("rb") as handle:
                return handle.read(max_bytes).decode("utf-8", errors="replace")
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def count_files_and_bytes(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    count = 0
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            count += 1
            total += file_size(item)
    return count, total


def scan_large_markdown(files: Iterable[Path], root: Path, threshold: int) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        if path.suffix.lower() == ".md" and file_size(path) >= threshold:
            findings.append(Finding("large-markdown", relative(path, root), f"{file_size(path) / 1024:.1f} KiB; likely generated or should be split/indexed"))
    return findings


def scan_runtime_dirs(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for name in ["runs", "artifacts", "evidence", ".local"]:
        path = root / name
        if path.exists():
            count, total = count_files_and_bytes(path)
            findings.append(Finding("runtime-or-evidence-dir", name, f"exists with {count} files and {total / 1024:.1f} KiB; classify as source, fixture, evidence, or generated output"))
    return findings


def scan_plan_status(files: Iterable[Path], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        rel = relative(path, root)
        if not rel.startswith("docs/") or path.suffix.lower() != ".md":
            continue
        text = read_text(path)
        looks_like_plan = any(token in rel.lower() for token in ["plan", "roadmap", "todo", "migration", "cleanup", "archive"]) or bool(SUSPICIOUS_DOC_RE.search(text[:20_000]))
        if looks_like_plan and not DOC_STATUS_RE.search(text[:4_000]):
            findings.append(Finding("plan-without-status", rel, "document looks like a plan/history item but has no lifecycle status metadata"))
    return findings


def scan_test_markers(files: Iterable[Path], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        rel = relative(path, root)
        if not rel.startswith("tests/") or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = read_text(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if SUSPICIOUS_TEST_RE.search(line):
                findings.append(Finding("test-review-marker", rel, f"line {lineno}: {line.strip()[:160]}"))
                break
    return findings


def scan_large_fixtures(files: Iterable[Path], root: Path, threshold: int) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        rel = relative(path, root)
        if rel.startswith("tests/") and file_size(path) >= threshold:
            findings.append(Finding("large-test-file", rel, f"{file_size(path) / 1024:.1f} KiB; verify this is a minimal stable fixture, not runtime output"))
    return findings


def scan_agent_docs(root: Path) -> list[Finding]:
    agent_docs = [root / name for name in ["AGENTS.md", "CLAUDE.md", "GEMINI.md"] if (root / name).exists()]
    if len(agent_docs) <= 1:
        return []
    sizes = ", ".join(f"{path.name}={file_size(path) / 1024:.1f} KiB" for path in agent_docs)
    return [Finding("agent-docs", ", ".join(path.name for path in agent_docs), f"multiple agent guidance files exist ({sizes}); keep AGENTS.md canonical and make model-specific files thin adapters")]


def render_report(findings: Sequence[Finding]) -> str:
    by_category: dict[str, list[Finding]] = {}
    for finding in findings:
        by_category.setdefault(finding.category, []).append(finding)

    lines = [
        "# QTS repository hygiene report",
        "",
        "Generated by `python scripts/audit_repo_hygiene.py`.",
        "",
        "This report is advisory. It does not prove a file should be deleted; it identifies files that need classification.",
        "",
        "## Summary",
        "",
    ]
    if not findings:
        lines.extend(["No hygiene findings detected by the current rules.", ""])
        return "\n".join(lines)
    for category in sorted(by_category):
        lines.append(f"- `{category}`: {len(by_category[category])}")
    lines.append("")
    for category in sorted(by_category):
        lines.extend([f"## {category}", ""])
        for finding in sorted(by_category[category], key=lambda item: item.path):
            lines.append(f"- `{finding.path}` — {finding.detail}")
        lines.append("")
    lines.extend([
        "## Suggested triage workflow",
        "",
        "1. Classify each finding as `keep`, `generate`, `move`, `archive`, or `delete`.",
        "2. Avoid deleting old tests until a replacement or obsolete behavior is confirmed.",
        "3. Promote only small stable fixtures to `tests/fixtures/`.",
        "4. Keep runtime output under ignored local directories.",
        "5. Add lifecycle status metadata to plan/history documents.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit repository hygiene and cleanup candidates.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root. Defaults to current directory.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown report output path.")
    parser.add_argument("--large-markdown-kib", type=int, default=128, help="Threshold for large Markdown findings.")
    parser.add_argument("--large-test-kib", type=int, default=256, help="Threshold for large test fixture findings.")
    args = parser.parse_args()

    root = find_repo_root(args.root)
    files = tracked_files(root)
    findings: list[Finding] = []
    findings.extend(scan_agent_docs(root))
    findings.extend(scan_large_markdown(files, root, args.large_markdown_kib * 1024))
    findings.extend(scan_runtime_dirs(root))
    findings.extend(scan_plan_status(files, root))
    findings.extend(scan_test_markers(files, root))
    findings.extend(scan_large_fixtures(files, root, args.large_test_kib * 1024))

    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(findings), encoding="utf-8")
    print(f"Wrote {relative(output, root)} with {len(findings)} findings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
