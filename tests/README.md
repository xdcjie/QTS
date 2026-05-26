<!-- QTS-REPO-HYGIENE -->
# Tests

QTS tests should be organized by dependency profile and runtime cost.

Recommended layout:

```text
tests/
  unit/
  integration/
  e2e/
  regression/
  fixtures/
```

Keep old tests when they encode real expected behavior. Move them to `regression/` when they exist to protect against a historical bug. Mark or isolate tests that require external services, local credentials, or manually prepared runtime data.
