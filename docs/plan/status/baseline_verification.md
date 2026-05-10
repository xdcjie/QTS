# Baseline Verification

Date: 2026-05-09

Command:

```bash
make check
```

Result: passed after fixing import ordering in `tests/unit/data/test_session_filter.py`.

Summary:

- Unit tests: passed.
- Integration tests: passed.
- Anchor tests: passed.
- Lint and typecheck: passed.

## S3 Baseline

Date: 2026-05-10

Command:

```bash
make check
```

Result: passed before S3 implementation.

Observed output:

- Ruff format: 235 files left unchanged.
- Ruff lint: all checks passed.
- Mypy: success, no issues in 226 source files.
- Unit tests: 118 passed.
- Integration tests: 16 passed.
- Anchor tests: 17 passed.
