"""Research-only implementation task scaffolding from reviewed FactorSpec evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qts.core.hashing import stable_json_dumps, stable_json_hash
from qts.research.factor_spec import FactorSpec


class FactorImplementationTaskWriter:
    """Writes implementation-task artifacts without creating executable modules."""

    def write(self, *, factor_spec: FactorSpec, output_dir: Path) -> dict[str, Any]:
        """Write a reviewed implementation task packet and templates."""

        output_dir.mkdir(parents=True, exist_ok=True)
        task_payload = self._task_payload(factor_spec)
        task_path = output_dir / "implementation_task.json"
        prompt_path = output_dir / "ai_prompt.md"
        factor_template_path = output_dir / "factor_template.py"
        strategy_template_path = output_dir / "strategy_template.py"
        test_template_path = output_dir / "test_no_lookahead_template.py"
        task_path.write_text(stable_json_dumps(task_payload) + "\n", encoding="utf-8")
        prompt_path.write_text(self._prompt(factor_spec), encoding="utf-8")
        factor_template_path.write_text(_FACTOR_TEMPLATE, encoding="utf-8")
        strategy_template_path.write_text(_STRATEGY_TEMPLATE, encoding="utf-8")
        test_template_path.write_text(_TEST_TEMPLATE, encoding="utf-8")
        return {
            "factor_template_path": str(factor_template_path),
            "implementation_task_hash": stable_json_hash(task_payload),
            "implementation_task_path": str(task_path),
            "output_dir": str(output_dir),
            "promotion_boundary": "research_task_only",
            "prompt_path": str(prompt_path),
            "strategy_template_path": str(strategy_template_path),
            "test_template_path": str(test_template_path),
        }

    @staticmethod
    def _task_payload(factor_spec: FactorSpec) -> dict[str, Any]:
        return {
            "candidate_tags": list(factor_spec.candidate_tags),
            "data_requirements": list(factor_spec.data_requirements),
            "expected_factor_module": f"qts.factors.{factor_spec.name}",
            "expected_strategy_module": f"examples.strategies.{factor_spec.name}",
            "factor_spec": factor_spec.to_payload(),
            "factor_spec_name": factor_spec.name,
            "implementation_boundary": (
                "Human-reviewed Python code under qts.factors.* and Strategy SDK examples"
            ),
            "no_trading_side_effects": True,
            "promotion_boundary": "research_task_only",
            "required_tests": [
                "unit factor timing/no-lookahead test",
                "strategy signal behavior test",
                "implementation_gate import check",
            ],
            "review_status": factor_spec.review_status,
            "runtime_promotion_allowed": False,
        }

    @staticmethod
    def _prompt(factor_spec: FactorSpec) -> str:
        return (
            "# Factor Implementation Task\n\n"
            f"- FactorSpec: {factor_spec.name}\n"
            f"- Review status: {factor_spec.review_status}\n"
            "- Boundary: research task only; this packet is not promotion approval.\n"
            "- No broker, runtime, order, or account imports in factor or strategy code.\n"
            "- Implement reviewed code under `qts.factors.*` and Strategy SDK examples only.\n"
            "- Add timing/no-lookahead tests before implementation.\n"
        )


_FACTOR_TEMPLATE = '''"""Template for a reviewed qts.factors implementation.

Replace this file with a reviewed, tested factor module. This template is
non-executable guidance; do not import broker, runtime, order, or account APIs.
"""

from __future__ import annotations


class ReviewedFactorTemplate:
    """Owns reviewed factor computation after human implementation."""

    name = "replace_me"
    version = "1"

    def compute(self, window: object) -> object:
        """Compute scores using only data visible at the factor timestamp."""

        raise NotImplementedError("replace with reviewed factor implementation")
'''

_STRATEGY_TEMPLATE = '''"""Template for a reviewed Strategy SDK implementation."""

from __future__ import annotations

from qts.strategy_sdk import Strategy, StrategyContext


class ReviewedStrategyTemplate(Strategy):
    """Owns reviewed signal-to-target behavior using only Strategy SDK APIs."""

    def initialize(self, ctx: StrategyContext) -> None:
        """Declare symbols/subscriptions here after review."""

    def on_bar(self, ctx: StrategyContext, bar: object) -> None:
        """Emit target intents only after visible bar data is complete."""
'''

_TEST_TEMPLATE = '''"""Template tests for reviewed factor timing and no-lookahead behavior."""

from __future__ import annotations


def test_factor_uses_only_visible_window_data() -> None:
    # Arrange a window whose future observation would change the score.
    # Assert the factor score is unchanged when future-only data is withheld.
    raise NotImplementedError("replace with reviewed no-lookahead test")
'''


__all__ = ["FactorImplementationTaskWriter"]
