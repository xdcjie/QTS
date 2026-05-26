<!-- QTS-REPO-HYGIENE -->
# QTS documentation index

This index is the stable entry point for QTS documentation. Keep root-level documentation short and link from here to deeper design, operating, testing, and planning material.

## Core project entry points

- `README.md` — user-facing project overview and quick start.
- `AGENTS.md` — authoritative guidance for AI/code agents working in this repository.
- `docs/repo-hygiene.md` — repository lifecycle rules for generated output, historical plans, evidence, and large files.
- `docs/testing.md` — test taxonomy, naming, and execution guidance.

## Planning and decisions

- `docs/plans/` — active and archived implementation plans. Every plan should declare its status.
- `docs/archive/` — historical material that is intentionally retained but should not be treated as current guidance.
- `docs/evidence/` — retained validation evidence, acceptance evidence, or audit material.

## Maintenance rules

1. Prefer one canonical document over multiple near-duplicates.
2. Generated files must say how they are generated and should not be edited by hand.
3. Runtime output belongs in ignored local output directories unless it is a small, stable test fixture or explicit evidence.
4. Plans need a lifecycle status: `active`, `done`, `superseded`, or `abandoned`.
5. Tests should be grouped by execution cost and dependency profile: `unit`, `integration`, `e2e`, `regression`, and `fixtures`.
