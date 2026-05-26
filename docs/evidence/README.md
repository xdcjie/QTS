<!-- QTS-REPO-HYGIENE -->
# Evidence

Use this directory only for durable validation evidence that should remain attached to the repository.

Each evidence item should include enough context to avoid being mistaken for current runtime output:

```markdown
Status: active | archived | superseded
Related commit:
Related issue/PR:
Reason retained:
Review/delete after:
```

Temporary logs, one-off experiment output, screenshots, and generated reports should normally stay under ignored local output directories such as `artifacts/`, `runs/`, or `.local/`.
