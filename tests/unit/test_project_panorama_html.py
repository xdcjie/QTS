from pathlib import Path

from scripts.update_project_panorama_source_index import (
    END_MARKER,
    START_MARKER,
    render_source_inventory_section,
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
