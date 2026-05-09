# Test Rules

Test layout:

- `tests/unit`: local function/model/state-machine tests
- `tests/integration`: multi-module and runtime flow tests
- `tests/anchor`: domain correctness invariant tests

Rules:

- Bug fixes should include regression tests when practical.
- Domain invariants belong in anchor tests.
- Actor and order-flow behavior belongs in integration tests.
- Avoid tests that rely on wall-clock time or external services.
- Prefer deterministic fixtures and fake clocks.
