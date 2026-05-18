# Optimizer Validation V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing optimizer with constraints, deterministic walk-forward split definitions, and validation summary artifacts while preserving the shared `BacktestPipelineRunner` path.

**Architecture:** `OptimizationConstraint` filters or marks `OptimizationResult` rows after each run; `WalkForwardPlan` describes train/test date windows; `OptimizerValidationSummary` records accepted/rejected runs and validation evidence. Backtest execution remains owned by `BacktestPipelineRunner`.

**Tech Stack:** Python dataclasses, `Decimal`, existing `OptimizationResult`, existing optimizer CLI, JSON artifacts, `pytest`.

---

## Domain Fact / Invariant

Optimizer validation may compare backtest metrics and parameter choices, but it
must not redefine strategy behavior, market data semantics, sessions, instrument
identity, or execution path. Each executable performance claim must still come
from a manifest produced by QTS backtest execution.

Correct owner or abstraction boundary:

- `qts.research.optimizer.constraints` owns metric constraints.
- `qts.research.optimizer.walk_forward` owns split definitions.
- `scripts/run_optimizer.py` remains a thin CLI entrypoint.
- `BacktestPipelineRunner` continues to own config-driven run execution.

Forbidden shortcut:

- Do not add a vectorized optimizer path that bypasses `BacktestPipelineRunner`.
- Do not silently drop failed runs without recording rejection reason.
- Do not optimize against in-sample metrics without writing the validation split metadata.

Required gates / verification:

- Unit tests for constraints and split definitions.
- Integration tests proving the CLI writes validation summary artifacts and applies
  configured validation constraints/walk-forward metadata.
- Existing optimizer integration tests still pass.
- `make guardrails`, `make test-unit`, and `make test-integration`.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `backend/src/qts/research/optimizer/constraints.py` | Create | Metric constraints and rejection reasons |
| `backend/src/qts/research/optimizer/walk_forward.py` | Create | Deterministic train/test split value objects |
| `backend/src/qts/research/optimizer/validation.py` | Create | Validation summary artifact payload and writer |
| `backend/src/qts/research/optimizer/__init__.py` | Modify | Export public optimizer validation APIs |
| `scripts/run_optimizer.py` | Modify | Optional `--validation-output` path and optional `validation:` config parsing; no execution-path rewrite |
| `docs/research/optimizer_validation_v1.md` | Create | Durable validation contract |
| `tests/unit/research/test_optimizer_constraints.py` | Create | Constraint behavior |
| `tests/unit/research/test_optimizer_walk_forward.py` | Create | Split validation |
| `tests/integration/test_optimizer_validation_cli.py` | Create | CLI artifact output |

## Acceptance Evidence

| Evidence | Command |
|---|---|
| First red constraint gate | `uv run pytest tests/unit/research/test_optimizer_constraints.py::test_constraint_rejects_result_below_minimum_metric -q` |
| Focused unit green | `uv run pytest tests/unit/research/test_optimizer_constraints.py tests/unit/research/test_optimizer_walk_forward.py -q` |
| CLI integration green | `uv run pytest tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py -q` |
| Boundary green | `make guardrails` |
| Normal verification | `make format && make lint && make typecheck && make test-unit && make test-integration` |

### Task 1: Add Constraint Tests

**Files:**
- Create: `tests/unit/research/test_optimizer_constraints.py`

- [ ] **Step 1: Write failing constraint test**

```python
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from qts.research.optimizer.constraints import MetricConstraint
from qts.research.optimizer.result import OptimizationResult


def test_constraint_rejects_result_below_minimum_metric() -> None:
    result = OptimizationResult(
        parameters={"window": 20},
        manifest_path=Path("runs/run-0001/manifest.json"),
        manifest_hash="abc",
        objective_value=Decimal("0.8"),
    )
    constraint = MetricConstraint(metric_name="sharpe_ratio", operator=">=", threshold=Decimal("1"))

    decision = constraint.evaluate(result, metrics={"sharpe_ratio": Decimal("0.8")})

    assert not decision.accepted
    assert decision.reason == "sharpe_ratio 0.8 is not >= 1"
```

- [ ] **Step 2: Run the red gate**

Run: `uv run pytest tests/unit/research/test_optimizer_constraints.py::test_constraint_rejects_result_below_minimum_metric -q`

Expected: fail with an import error for `qts.research.optimizer.constraints`.

### Task 2: Implement Constraints

**Files:**
- Create: `backend/src/qts/research/optimizer/constraints.py`
- Modify: `backend/src/qts/research/optimizer/__init__.py`

- [ ] **Step 1: Add constraint implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from qts.research.optimizer.result import OptimizationResult


@dataclass(frozen=True, slots=True)
class ConstraintDecision:
    accepted: bool
    reason: str


@dataclass(frozen=True, slots=True)
class MetricConstraint:
    metric_name: str
    operator: str
    threshold: Decimal

    def __post_init__(self) -> None:
        if self.operator not in {">", ">=", "<", "<=", "=="}:
            raise ValueError("operator must be one of >, >=, <, <=, ==")
        if not self.metric_name.strip():
            raise ValueError("metric_name must not be empty")

    def evaluate(
        self,
        result: OptimizationResult,
        *,
        metrics: dict[str, Decimal],
    ) -> ConstraintDecision:
        value = metrics[self.metric_name]
        accepted = {
            ">": value > self.threshold,
            ">=": value >= self.threshold,
            "<": value < self.threshold,
            "<=": value <= self.threshold,
            "==": value == self.threshold,
        }[self.operator]
        if accepted:
            return ConstraintDecision(True, "accepted")
        return ConstraintDecision(
            False,
            f"{self.metric_name} {value} is not {self.operator} {self.threshold}",
        )
```

- [ ] **Step 2: Export constraints**

Export `ConstraintDecision` and `MetricConstraint` from `qts.research.optimizer`.

- [ ] **Step 3: Run focused tests**

Run: `uv run pytest tests/unit/research/test_optimizer_constraints.py -q`

Expected: tests pass.

### Task 3: Add Walk-Forward Split Plan

**Files:**
- Create: `backend/src/qts/research/optimizer/walk_forward.py`
- Create: `tests/unit/research/test_optimizer_walk_forward.py`

- [ ] **Step 1: Write failing split test**

```python
from __future__ import annotations

from datetime import date

from qts.research.optimizer.walk_forward import WalkForwardPlan, WalkForwardSplit


def test_walk_forward_split_requires_non_overlapping_train_and_test_windows() -> None:
    split = WalkForwardSplit(
        name="wf-001",
        train_start=date(2024, 1, 1),
        train_end=date(2024, 6, 1),
        test_start=date(2024, 6, 1),
        test_end=date(2024, 9, 1),
    )
    plan = WalkForwardPlan(splits=(split,))

    assert plan.splits[0].train_end == plan.splits[0].test_start
```

- [ ] **Step 2: Implement split value objects**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class WalkForwardSplit:
    name: str
    train_start: date
    train_end: date
    test_start: date
    test_end: date

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("split name must not be empty")
        if not self.train_start < self.train_end <= self.test_start < self.test_end:
            raise ValueError("walk-forward windows must be ordered and non-overlapping")


@dataclass(frozen=True, slots=True)
class WalkForwardPlan:
    splits: tuple[WalkForwardSplit, ...]

    def __post_init__(self) -> None:
        if not self.splits:
            raise ValueError("walk-forward plan requires at least one split")
```

- [ ] **Step 3: Run walk-forward tests**

Run: `uv run pytest tests/unit/research/test_optimizer_walk_forward.py -q`

Expected: tests pass.

### Task 4: Add Validation Summary Artifact

**Files:**
- Create: `backend/src/qts/research/optimizer/validation.py`
- Create: `tests/integration/test_optimizer_validation_cli.py`
- Modify: `scripts/run_optimizer.py`
- Create: `docs/research/optimizer_validation_v1.md`

- [ ] **Step 1: Add CLI integration test**

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_optimizer_cli_writes_validation_summary(tmp_path: Path) -> None:
    output_path = tmp_path / "validation-summary.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_optimizer.py",
            "configs/optimizer/quickstart.yaml",
            "--output-root",
            str(tmp_path / "optimizer-runs"),
            "--validation-output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONPATH": "backend/src", "QTS_API_DEV_TOKENS": "1"},
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["run_count"] == 4
    assert payload["accepted_count"] == 4
```

- [ ] **Step 2: Implement summary writer**

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from qts.research.optimizer.result import OptimizationResult


@dataclass(frozen=True, slots=True)
class OptimizerValidationSummary:
    run_count: int
    accepted_count: int
    rejected_count: int

    @classmethod
    def from_results(cls, results: tuple[OptimizationResult, ...]) -> OptimizerValidationSummary:
        return cls(run_count=len(results), accepted_count=len(results), rejected_count=0)


class OptimizerValidationSummaryWriter:
    def write(self, path: Path, summary: OptimizerValidationSummary) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "run_count": summary.run_count,
                    "accepted_count": summary.accepted_count,
                    "rejected_count": summary.rejected_count,
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path
```

- [ ] **Step 3: Wire CLI option without changing execution path**

Add:

```python
parser.add_argument("--validation-output", type=Path, default=None)
```

After `results` are produced by the existing runner, write:

```python
if args.validation_output is not None:
    summary = OptimizerValidationSummary.from_results(tuple(results))
    OptimizerValidationSummaryWriter().write(args.validation_output, summary)
```

- [ ] **Step 4: Run integration tests**

Run:

```bash
uv run pytest tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py -q
```

Expected: both integration tests pass.

### Task 5: Verification And Matrix Update

Run:

```bash
make format
make lint
make guardrails
make typecheck
uv run pytest tests/unit/research/test_optimizer_constraints.py tests/unit/research/test_optimizer_walk_forward.py tests/integration/test_optimizer_validation_cli.py tests/integration/test_run_optimizer_cli_outputs_ranked_results.py -q
```

Expected: all commands exit 0. Update OPTV-1 matrix row after recording red gate, green evidence, broad verification, and commit hash.
