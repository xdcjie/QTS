<!-- QTS-REPO-HYGIENE -->
# Plans

Use this directory for implementation plans that may guide current or future work.

## Required status

Each plan should declare a status at the top:

```markdown
---
status: active | done | superseded | abandoned
owner: xdcjie
created: YYYY-MM-DD
last_reviewed: YYYY-MM-DD
superseded_by:
related_pr:
---
```

## Status meanings

- `active` — still guides current implementation.
- `done` — implemented or no longer requiring action.
- `superseded` — replaced by another document or PR.
- `abandoned` — intentionally not pursued.

Historical plans can remain in git, but they must not look current. Prefer moving them to an archive subdirectory or marking them at the top.
