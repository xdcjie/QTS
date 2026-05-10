# S4 Production Readiness Report Template

## Decision

- Decision: Go / No-Go
- Decision date:
- Approver:
- Scope:

## Completed Tasks

| Task | Evidence | Notes |
|---|---|---|
| S4-00 baseline | `make check` output | |

## Verification

| Check | Result | Evidence |
|---|---|---|
| `make check` | Pass / Fail | |
| `make test-replay` | Pass / Fail | |
| `make test-reconciliation` | Pass / Fail | |
| `make test-soak` | Pass / Fail | |
| `make readiness-check` | Pass / Fail | |

## Failed Checks

| Check | Failure | Owner | Blocking? |
|---|---|---|---|

## Known Risks

| Risk | Mitigation | Owner | Blocking? |
|---|---|---|---|

## Accepted Limitations

| Limitation | Rationale | Expiry / Review Date |
|---|---|---|

## Go / No-Go Rationale

Record unresolved critical drift, missing broker evidence, missing soak evidence, or operator signoff gaps here. Critical unresolved items require No-Go.
