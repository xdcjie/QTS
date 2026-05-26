<!-- QTS-REPO-HYGIENE -->
# Testing guide

This guide defines the intended test layout for QTS. It is deliberately conservative: existing tests should be moved only after their dependencies and purpose are understood.

## Recommended layout

```text
tests/
  unit/             # fast, deterministic, no external services
  integration/      # database, filesystem, services, docker, or API boundaries
  e2e/              # full frontend/backend or user-flow tests
  regression/       # tests that pin previously fixed bugs
  fixtures/         # small stable data used by tests
```

## Naming conventions

- Use `test_<subject>.py` for normal pytest modules.
- Use `test_<bug_or_case>_regression.py` for regression tests.
- Put manual checks outside the default pytest collection path, or mark them explicitly.

## Pytest marker policy

Long-lived `skip`, `xfail`, `TODO`, and manual-only tests should be reviewed. A skipped test should explain why it is skipped and what condition allows it to be re-enabled.

Recommended markers:

```python
@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.regression
```

## Audit commands

```bash
pytest --collect-only -q
pytest -q --durations=20
```

## Deletion rule

Before deleting a test, confirm at least one of the following:

1. The tested behavior is no longer supported.
2. A newer test covers the same behavior more directly.
3. The file is a manual or temporary script and is not part of the intended suite.
4. The test depends on obsolete historical artifacts that should not drive current behavior.
