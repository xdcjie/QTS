# 2026-05-12 OOP Baseline (QTS)

## Scope
- Task sequence start: `docs/plan/2026-05-12_qts_oop_architecture_review_and_refactor_plan.md`
- Baseline date: 2026-05-12
- Commit: current working tree before OOP-00 → OOP-01 execution.

## Baseline checks

| Command | Result |
| --- | --- |
| `make format` | Passed (`uv run ruff format .` reported 323 files unchanged) |
| `make lint` | Passed (`uv run ruff check .` all checks passed) |
| `make typecheck` | Passed (`uv run mypy backend tests`, no issues in 307 source files) |
| `make test-unit` | Passed (237 passed) |
| `make test-integration` | Passed (47 passed) |
| `make test-anchor` | Passed (36 passed) |

## Notes
- No baseline failures observed.
- Next tasks can treat these results as the pre-refactor reference.
