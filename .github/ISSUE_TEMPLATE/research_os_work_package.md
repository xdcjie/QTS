---
name: Research OS work package
about: Track a scoped Research OS documentation, evidence, or promotion-gate package
title: "Research OS WP-XX: "
labels: ["research-os"]
assignees: ""
---

## Objective

State the concrete outcome this work package must deliver.

## Ownership / Allowed Write Scope

List exact files, directories, or modules the worker may edit. State any files
or directories that are explicitly out of scope.

## First-Principles Behavior Contract

State the invariant that must remain true regardless of implementation details.
For research work, identify whether the package belongs to `FLOW-RESEARCH`,
`FLOW-OPTIMIZER`, `FLOW-BACKTEST`, `FLOW-REPORTING`, or `FLOW-PROMOTION`.

If promotion is involved, state explicitly: research evidence is not
paper/live/production approval, and research evidence != paper/live/production
behavior.

## Required Evidence

- changed files list;
- artifact paths, manifest paths, documentation anchors, or screenshots when
  applicable;
- command output summary with exit status;
- data windows, config hashes, factor/strategy versions, and reviewer decisions
  when applicable;
- statement that paper/live/production behavior was not enabled unless this is
  an approved promotion package.

## Acceptance Criteria

- [ ] Objective is satisfied within the allowed write scope.
- [ ] Evidence gates are explicit: tests, guardrails, commands, checklist items,
      or documented manual review.
- [ ] No-lookahead, data visibility, and `[start, end)` interval rules are
      preserved where applicable.
- [ ] Research evidence is not treated as paper/live/production approval.
- [ ] Promotion, if requested, requires human review of the exact build, config,
      account, risk profile, capital limits, and runtime mode.
- [ ] Final response reports `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, or
      `NEEDS_CONTEXT`.

## Required Commands

List exact commands the worker must run before claiming completion.

```bash
git status --short
```

Add package-specific verification commands here.

## Risks / Follow-Up

List known gaps, incomplete checks, stale assumptions, data-quality risks,
future-data risks, promotion risks, and follow-up issues.
