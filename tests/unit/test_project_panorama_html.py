import subprocess
import sys
from pathlib import Path

from scripts.update_project_panorama_source_index import (
    END_MARKER,
    STALE_GENERATED_DOC_TOKENS,
    START_MARKER,
    render_source_inventory_section,
)


def _generated_doc_paths() -> tuple[Path, ...]:
    return (
        Path("project_panorama.html"),
        Path("docs/architecture/backtest_live_parallel_sequence.html"),
    )


def test_project_panorama_explains_runtime_flow_stages() -> None:
    html = Path("project_panorama.html").read_text(encoding="utf-8")

    assert 'href="#runtime-flow-detail"' in html
    assert 'section id="runtime-flow-detail"' in html
    assert "运行链路阶段详解" in html

    expected_stages = [
        "配置与输入装配",
        "行情归一化进入 MarketDataActor",
        "聚合、completed bar gating 与 fan-out",
        "StrategyActor、StrategyContext、DataView",
        "TargetIntent 聚合与账户快照",
        "RiskEngine 到 OrderManagerActor",
        "ExecutionActor、ExecutionReport、AccountActor",
        "Artifacts / API / WebSocket 输出",
    ]
    for stage in expected_stages:
        assert stage in html

    expected_contract_labels = [
        "输入",
        "Owner / 边界",
        "处理动作",
        "输出",
        "必须守住",
        "验证依据",
    ]
    for label in expected_contract_labels:
        assert label in html


def test_project_panorama_source_inventory_is_current() -> None:
    html = Path("project_panorama.html").read_text(encoding="utf-8")
    start = html.index(START_MARKER)
    end = html.index(END_MARKER) + len(END_MARKER)

    assert html[start:end] == render_source_inventory_section(Path("."))
    assert 'href="#source-inventory"' in html
    assert "src 文件、类、函数清单" in html
    assert "backend/src/qts/runtime/actors/market_data_actor.py" in html
    assert "frontend/src/App.tsx" in html


def test_generated_architecture_docs_have_no_stale_text() -> None:
    stale_hits: list[str] = []
    for path in _generated_doc_paths():
        html = path.read_text(encoding="utf-8")
        for token in STALE_GENERATED_DOC_TOKENS:
            if token in html:
                stale_hits.append(f"{path}:{token}")

    assert stale_hits == []


def test_source_inventory_check_fails_on_stale_generated_doc_text(tmp_path: Path) -> None:
    stale_html = tmp_path / "stale.html"
    stale_html.write_text(
        "\n".join(
            [
                "<html><body>",
                render_source_inventory_section(Path(".")),
                "<p>Boundary placeholder</p>",
                "</body></html>",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/update_project_panorama_source_index.py",
            "--repo-root",
            ".",
            "--html",
            str(stale_html),
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "stale generated documentation token" in result.stdout
