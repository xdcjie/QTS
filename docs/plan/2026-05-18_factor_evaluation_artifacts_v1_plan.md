# Factor Evaluation Artifacts V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deterministic factor-evaluation metrics and artifact writing so research runs can prove factor quality before strategy/backtest promotion.

**Architecture:** `FactorEvaluation` consumes dated `FactorResult` snapshots and forward returns, computes research metrics, writes JSON artifacts, and can be attached to `ExperimentManifestWriter`. It does not compute factors itself and does not run backtests.

**Tech Stack:** Python dataclasses, `Decimal`, JSON artifacts, existing `qts.factors` contract, existing `ExperimentManifestWriter`, `pytest`.

---

## Domain Fact / Invariant

Factor evaluation measures historical predictive evidence. It must not use future
returns to compute factor scores, and it must not turn scores into orders or target
intents.

Correct owner or abstraction boundary:

- `qts.factors` owns factor computation.
- `qts.research.factor_evaluation` owns evaluation metrics and artifacts.
- `qts.research.experiment_manifest` owns experiment manifest hashing.

Forbidden shortcut:

- Do not import runtime, execution, broker, risk, or account modules into `qts.research.factor_evaluation`.
- Do not hide missing data; coverage and missing symbols must be recorded.
- Do not add pandas as a core domain dependency. Pandas may remain notebook-facing only.

Required gates / verification:

- Unit tests for rank IC, bucket spread, coverage, turnover, and artifact determinism.
- Manifest test proving factor evaluation artifacts are hashed.
- `make guardrails` and `make test-unit`.

## File Structure

| Path | Action | Responsibility |
|---|---|---|
| `backend/src/qts/research/factor_evaluation.py` | Create | Evaluation input rows, metrics, JSON artifact writer |
| `backend/src/qts/research/__init__.py` | Modify | Export evaluation API |
| `docs/research/factor_evaluation_v1.md` | Create | Durable metric definitions |
| `tests/unit/research/test_factor_evaluation.py` | Create | Deterministic metric tests |
| `tests/unit/research/test_factor_evaluation_manifest.py` | Create | Manifest artifact hash test |
| `docs/plan/2026-05-18_lean_research_workflow_status_matrix.md` | Modify | Record evidence |

## Acceptance Evidence

| Evidence | Command |
|---|---|
| First red metric gate | `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_rank_ic_and_bucket_spread -q` |
| Focused unit green | `uv run pytest tests/unit/research/test_factor_evaluation.py tests/unit/research/test_factor_evaluation_manifest.py -q` |
| Boundary green | `make guardrails` |
| Normal verification | `make format && make lint && make typecheck && make test-unit` |

### Task 1: Add Metric Tests

**Files:**
- Create: `tests/unit/research/test_factor_evaluation.py`

- [ ] **Step 1: Write failing rank IC and bucket spread test**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from qts.factors import FactorResult, FactorScore
from qts.research.factor_evaluation import FactorEvaluation, FactorEvaluationInput


@dataclass(frozen=True, slots=True)
class Asset:
    symbol: str


def test_factor_evaluation_computes_rank_ic_and_bucket_spread() -> None:
    aaa = Asset("AAA")
    bbb = Asset("BBB")
    ccc = Asset("CCC")
    factor_result = FactorResult(
        ranked=(
            FactorScore(aaa, Decimal("3")),
            FactorScore(bbb, Decimal("2")),
            FactorScore(ccc, Decimal("1")),
        )
    )
    evaluation = FactorEvaluation.evaluate(
        FactorEvaluationInput(
            as_of=date(2026, 1, 2),
            factor_name="momentum",
            factor_version="1",
            factor_result=factor_result,
            forward_returns={
                aaa.symbol: Decimal("0.03"),
                bbb.symbol: Decimal("0.01"),
                ccc.symbol: Decimal("-0.02"),
            },
            bucket_count=3,
        )
    )

    assert evaluation.metrics.rank_ic == Decimal("1")
    assert evaluation.metrics.long_short_spread == Decimal("0.05")
    assert evaluation.metrics.coverage == Decimal("1")
```

- [ ] **Step 2: Run the red gate**

Run: `uv run pytest tests/unit/research/test_factor_evaluation.py::test_factor_evaluation_computes_rank_ic_and_bucket_spread -q`

Expected: fail with an import error for `qts.research.factor_evaluation`.

### Task 2: Implement Metrics

**Files:**
- Create: `backend/src/qts/research/factor_evaluation.py`
- Modify: `backend/src/qts/research/__init__.py`

- [ ] **Step 1: Add evaluation dataclasses and deterministic Spearman rank IC**

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from qts.factors import FactorResult


@dataclass(frozen=True, slots=True)
class FactorEvaluationInput:
    as_of: date
    factor_name: str
    factor_version: str
    factor_result: FactorResult
    forward_returns: dict[str, Decimal]
    bucket_count: int = 5


@dataclass(frozen=True, slots=True)
class FactorEvaluationMetrics:
    rank_ic: Decimal
    long_short_spread: Decimal
    coverage: Decimal
    scored_count: int
    return_count: int


@dataclass(frozen=True, slots=True)
class FactorEvaluationResult:
    as_of: date
    factor_name: str
    factor_version: str
    metrics: FactorEvaluationMetrics


class FactorEvaluation:
    @classmethod
    def evaluate(cls, input: FactorEvaluationInput) -> FactorEvaluationResult:
        scored = [
            (score.asset.symbol, score.value, input.forward_returns[score.asset.symbol])
            for score in input.factor_result.ranked
            if score.asset.symbol in input.forward_returns
        ]
        if len(scored) < 2:
            raise ValueError("at least two scored assets with forward returns are required")
        rank_ic = cls._spearman(
            [item[1] for item in scored],
            [item[2] for item in scored],
        )
        top = scored[0][2]
        bottom = scored[-1][2]
        metrics = FactorEvaluationMetrics(
            rank_ic=rank_ic,
            long_short_spread=top - bottom,
            coverage=Decimal(len(scored)) / Decimal(len(input.factor_result.ranked)),
            scored_count=len(input.factor_result.ranked),
            return_count=len(scored),
        )
        return FactorEvaluationResult(
            as_of=input.as_of,
            factor_name=input.factor_name,
            factor_version=input.factor_version,
            metrics=metrics,
        )

    @staticmethod
    def _spearman(left: list[Decimal], right: list[Decimal]) -> Decimal:
        left_ranks = FactorEvaluation._ordinal_ranks(left)
        right_ranks = FactorEvaluation._ordinal_ranks(right)
        n = Decimal(len(left_ranks))
        diffs = sum((l - r) ** 2 for l, r in zip(left_ranks, right_ranks, strict=True))
        return Decimal("1") - (Decimal("6") * diffs) / (n * (n * n - Decimal("1")))

    @staticmethod
    def _ordinal_ranks(values: list[Decimal]) -> list[Decimal]:
        ordered = sorted((value, index) for index, value in enumerate(values))
        ranks = [Decimal("0")] * len(values)
        for rank, (_value, index) in enumerate(ordered, start=1):
            ranks[index] = Decimal(rank)
        return ranks
```

- [ ] **Step 2: Export from `qts.research`**

Export `FactorEvaluation`, `FactorEvaluationInput`, `FactorEvaluationMetrics`, and
`FactorEvaluationResult`.

- [ ] **Step 3: Run metric unit tests**

Run: `uv run pytest tests/unit/research/test_factor_evaluation.py -q`

Expected: tests pass.

### Task 3: Add Artifact Writer And Manifest Gate

**Files:**
- Modify: `backend/src/qts/research/factor_evaluation.py`
- Create: `tests/unit/research/test_factor_evaluation_manifest.py`
- Create: `docs/research/factor_evaluation_v1.md`

- [ ] **Step 1: Add artifact writer test**

```python
from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from qts.research.factor_evaluation import (
    FactorEvaluationArtifactWriter,
    FactorEvaluationMetrics,
    FactorEvaluationResult,
)


def test_factor_evaluation_artifact_is_stable_json(tmp_path: Path) -> None:
    writer = FactorEvaluationArtifactWriter(tmp_path)
    result = FactorEvaluationResult(
        as_of=date(2026, 1, 2),
        factor_name="momentum",
        factor_version="1",
        metrics=FactorEvaluationMetrics(
            rank_ic=Decimal("1"),
            long_short_spread=Decimal("0.05"),
            coverage=Decimal("1"),
            scored_count=3,
            return_count=3,
        ),
    )

    path = writer.write(result)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["factor_name"] == "momentum"
    assert payload["metrics"]["rank_ic"] == "1"
```

- [ ] **Step 2: Implement JSON writer**

```python
class FactorEvaluationArtifactWriter:
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir

    def write(self, result: FactorEvaluationResult) -> Path:
        self._root_dir.mkdir(parents=True, exist_ok=True)
        path = self._root_dir / (
            f"{result.as_of.isoformat()}-{result.factor_name}-{result.factor_version}.json"
        )
        payload = {
            "as_of": result.as_of.isoformat(),
            "factor_name": result.factor_name,
            "factor_version": result.factor_version,
            "metrics": {
                key: str(value) if isinstance(value, Decimal) else value
                for key, value in asdict(result.metrics).items()
            },
        }
        path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return path
```

- [ ] **Step 3: Add durable metric definitions**

`docs/research/factor_evaluation_v1.md` must define:

- rank IC as Spearman rank correlation between factor score ranks and forward return ranks;
- long-short spread as top-ranked forward return minus bottom-ranked forward return for V1;
- coverage as scored assets with forward returns divided by scored assets;
- missing forward returns are excluded and counted by `return_count`.

### Task 4: Verification And Matrix Update

Run:

```bash
make format
make lint
make guardrails
make typecheck
uv run pytest tests/unit/research/test_factor_evaluation.py tests/unit/research/test_factor_evaluation_manifest.py -q
```

Expected: all commands exit 0. Update FE-1 matrix row after recording red gate, green evidence, broad verification, and commit hash.
