"""C3: promotion-evidence value-flows are wired producer -> consumer.

The "math exists but no production entrypoint consumes it through a value path"
anti-pattern (OPT-15/17/25/26/29) is closed for promotion evidence by four
named wirings. Rather than a brittle generic call-graph guardrail -- which would
hardcode method names, argument positions, and file paths and break on benign
refactors -- C3's intent is enforced by behavior/regression tests that exercise
the real value path, plus narrow static wiring locks here:

(a) ``BacktestEngine.from_config`` derives the ``ExecutionTimingModel`` from the
    config's ``fill_policy`` so the run manifest's ``promotion_grade`` flag is
    honest. Behavior is locked by
    ``tests/integration/test_backtest_next_obtainable_fill_policy.py``
    (``test_config_fill_policy_next_bar_open_is_promotion_grade``); the static
    lock below guards the producer->consumer call.
(b) ``AutonomousResearchEngine`` passes a real ``trial_count`` (the cardinality
    of the configurations tried this generation) into ``CandidateSelector.select``
    so the multiplicity haircut is not a no-op default of 1. This wiring had no
    dedicated lock, so the behavior+static lock below closes the gap.
(c) research metrics are derived from validation artifacts, not literals. Locked
    by ``tests/unit/research/orchestrator/test_metrics_value_honesty.py`` and the
    ``PromotionValueHonestyRule`` guardrail.
(d) ``PromotionPacketV2`` consumes the execution-timing evidence
    (``fill_timing_promotion_grade``) when ruling on eligibility. Behavior is
    locked by ``tests/unit/research/test_promotion_packet_execution_timing_gate.py``;
    the static lock below guards the consumer reference.

See ``docs/architecture/module_boundaries.md`` ("Value-honesty guardrails")
for the enforcement-mechanism note.
"""

from __future__ import annotations

import ast
from pathlib import Path

from qts.research.selector import (
    CandidateSelector,
    SelectedCandidate,
    SelectionPolicy,
    SelectionResult,
)

_ENGINE_SOURCE = Path("backend/src/qts/research/engine/autonomous_research_engine.py").read_text(
    encoding="utf-8"
)
_BACKTEST_ENGINE_SOURCE = Path("backend/src/qts/backtest/engine.py").read_text(encoding="utf-8")
# QTS-FINAL-002 moved the config->timing derivation out of BacktestEngine.from_config and
# into BacktestEngineAssembler.runtime_config_inputs, which from_config now delegates to.
_ENGINE_ASSEMBLY_SOURCE = Path("backend/src/qts/backtest/engine_assembly.py").read_text(
    encoding="utf-8"
)
_PROMOTION_PACKET_SOURCE = Path("backend/src/qts/research/promotion_packet.py").read_text(
    encoding="utf-8"
)


def _selector_select_calls(tree: ast.AST) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "select"
            and isinstance(node.func.value, ast.Call)
            and isinstance(node.func.value.func, ast.Name)
            and node.func.value.func.id == "CandidateSelector"
        ):
            calls.append(node)
    return calls


# --- (a) engine.from_config derives ExecutionTimingModel from config.fill_policy ---


def test_backtest_engine_from_config_derives_timing_from_fill_policy() -> None:
    # The config->timing derivation now lives in BacktestEngineAssembler.runtime_config_inputs,
    # which BacktestEngine.from_config delegates to (QTS-FINAL-002). Verify the wiring there,
    # and that from_config still routes through the assembler.
    assert "runtime_config_inputs" in _BACKTEST_ENGINE_SOURCE, (
        "from_config must delegate config translation to BacktestEngineAssembler"
    )
    tree = ast.parse(_ENGINE_ASSEMBLY_SOURCE)
    deriver = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "runtime_config_inputs"
    )
    # The producer->consumer wiring: the timing model is derived from the config's
    # fill_policy via ExecutionTimingModel.from_value(config.fill_policy).
    from_value_calls = [
        node
        for node in ast.walk(deriver)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "from_value"
    ]
    assert from_value_calls, "runtime_config_inputs must call ExecutionTimingModel.from_value(...)"
    references_fill_policy = any(
        isinstance(inner, ast.Attribute) and inner.attr == "fill_policy"
        for call in from_value_calls
        for inner in ast.walk(call)
    )
    assert references_fill_policy, "timing model must be derived from config.fill_policy"


# --- (b) engine -> selector trial_count is the real cardinality, not literal 1 ---


def test_engine_passes_derived_trial_count_into_selector() -> None:
    calls = _selector_select_calls(ast.parse(_ENGINE_SOURCE))
    assert calls, "AutonomousResearchEngine must call CandidateSelector(...).select(...)"
    for call in calls:
        trial_count = next((kw.value for kw in call.keywords if kw.arg == "trial_count"), None)
        assert trial_count is not None, "select(...) must pass an explicit trial_count"
        # Value honesty: trial_count must be derived from the inputs' cardinality
        # (a len(...) expression), never a constant literal such as 1 (which makes
        # the expected-maximum-Sharpe haircut a no-op).
        assert not isinstance(trial_count, ast.Constant), (
            "trial_count must be derived from the configurations tried, not a literal"
        )
        derived_from_len = any(
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id == "len"
            for inner in ast.walk(trial_count)
        )
        assert derived_from_len, "trial_count must be derived from len(selector_inputs)"


def test_selector_haircut_responds_to_trial_count() -> None:
    # The consumer-side value path: a larger trial_count strictly lowers the
    # adjusted score, so passing the real cardinality is observable, not cosmetic.
    candidates = (
        _candidate("winner", observed_sharpe=0.18, oos_sharpe=2.85),
        _candidate("runner-up", observed_sharpe=0.06, oos_sharpe=0.95),
    )
    policy = SelectionPolicy()
    single = CandidateSelector(policy).select(candidates, trial_count=1)
    many = CandidateSelector(policy).select(candidates, trial_count=1000)

    single_winner = _winner(single)
    many_winner = _winner(many)
    assert single_winner.adjusted_score is not None
    assert many_winner.adjusted_score is not None
    assert many_winner.adjusted_score < single_winner.adjusted_score


# --- (d) PromotionPacketV2 consumes execution-timing evidence ---


def test_promotion_packet_consumes_fill_timing_evidence() -> None:
    # The consumer references the manifest-derived execution-timing fact when
    # ruling on eligibility; behavior is locked by the dedicated gate test.
    assert "fill_timing_promotion_grade" in _PROMOTION_PACKET_SOURCE
    tree = ast.parse(_PROMOTION_PACKET_SOURCE)
    gate = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_append_execution_timing_reasons"
    )
    reads_flag = any(
        isinstance(node, ast.Constant) and node.value == "fill_timing_promotion_grade"
        for node in ast.walk(gate)
    )
    assert reads_flag, "execution-timing gate must read research.fill_timing_promotion_grade"


# --- helpers -----------------------------------------------------------------


def _winner(result: SelectionResult) -> SelectedCandidate:
    return next(
        candidate for candidate in result.selected_candidates if candidate.candidate_id == "winner"
    )


def _candidate(
    candidate_id: str,
    *,
    observed_sharpe: float,
    oos_sharpe: float,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "metrics": {
            "performance": {
                "max_drawdown": 0.07,
                "observed_sharpe": observed_sharpe,
                "oos_sharpe": oos_sharpe,
                "return_observation_count": 252,
                "total_return": 0.16,
            },
            "quality": {"profit_factor": 1.5},
            "trading": {"oos_trade_count": 50},
            "costs": {"cost_sensitivity": 0.01},
        },
        "data_quality": {"accepted": True},
        "reproducibility": {"git_dirty": False},
    }
