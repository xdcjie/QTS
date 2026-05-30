"""H4: no-lookahead timing runs on real cutoff-anchored times and flags
forward-looking factor transforms.

Previously the autonomous path stamped every feature with a 1970 epoch, so the
feature-timestamp/visibility checks were vacuously satisfied. Features are now
anchored to the out-of-sample cutoff, and a factor transform that reads bars
after the decision (forward/future/lead type, or a negative offset) is placed
past the cutoff so the runner flags it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from qts.research.orchestrator.experiment_runner import ResearchExperimentRunner

_ANCHOR = datetime(2026, 3, 1, tzinfo=UTC)


def _runner() -> ResearchExperimentRunner:
    return ResearchExperimentRunner(repo_root=Path("."))


def test_forward_transform_detected_by_type() -> None:
    factor = {"transforms": [{"type": "forward_returns", "horizon": 5}]}
    assert _runner()._forward_looking_transform(factor) is not None


def test_forward_transform_detected_by_negative_offset() -> None:
    factor = {"transforms": [{"type": "returns", "lookback": -3}]}
    assert _runner()._forward_looking_transform(factor) is not None


def test_backward_transform_not_flagged() -> None:
    factor = {"transforms": [{"type": "returns", "lookback": 2}]}
    assert _runner()._forward_looking_transform(factor) is None


def test_forward_transform_feature_placed_after_cutoff() -> None:
    pipeline_config = {
        "research_factory": {
            "factor_definition": {
                "inputs": [{"root": "GC", "field": "close"}],
                "transforms": [{"type": "forward_returns", "horizon": 5}],
            }
        }
    }
    features = _runner()._no_lookahead_features({}, pipeline_config, _ANCHOR)
    # The backward input is observable at the cutoff; the forward transform is not.
    forward = [f for f in features if f.name.startswith("transform:")]
    assert forward, "expected a forward-looking transform feature"
    assert all(f.timestamp > _ANCHOR for f in forward)
    assert all(f.timestamp <= _ANCHOR for f in features if not f.name.startswith("transform:"))


def test_backward_factor_features_observable_at_cutoff() -> None:
    pipeline_config = {
        "research_factory": {
            "factor_definition": {
                "inputs": [{"root": "GC", "field": "close"}],
                "transforms": [{"type": "returns", "lookback": 2}],
            }
        }
    }
    features = _runner()._no_lookahead_features({}, pipeline_config, _ANCHOR)
    assert features
    assert all(f.timestamp <= _ANCHOR for f in features)
