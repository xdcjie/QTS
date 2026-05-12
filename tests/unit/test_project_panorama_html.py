from pathlib import Path


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
