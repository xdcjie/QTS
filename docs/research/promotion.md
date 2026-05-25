# Research Promotion Boundary

Promotion is the human-controlled boundary between research evidence and
paper/live operation. Research evidence is not paper/live/production approval.
Research evidence != paper/live/production behavior.

Promotion belongs to `FLOW-PROMOTION`, not `FLOW-RESEARCH`,
`FLOW-OPTIMIZER`, `FLOW-BACKTEST`, or `FLOW-REPORTING`.

## What Research Evidence Can Do

Research evidence may support a promotion review by providing:

- factor specifications and human review decisions;
- deterministic factor-evaluation artifacts;
- optimizer validation summaries;
- backtest manifests and reports;
- ablation and cost-stress results;
- trade diagnostics and failure-window analysis;
- known limitations, unresolved risks, and follow-up items.

Research evidence may not:

- start paper or live runtime;
- enable order submission;
- approve capital allocation;
- bypass risk, order, execution, or account actors;
- create runtime config changes after signoff;
- promote generated or unreviewed code;
- treat optimizer ranking, backtest PnL, or paper success as automatic approval.

## Promotion Packet

A promotion packet must identify:

- target mode: paper simulated, paper broker, live observation, or live;
- strategy and factor code versions;
- config files and config hashes;
- dataset/feed identities and date windows;
- broker/data-source adapter boundaries;
- account, risk profile, capital limits, and kill-switch settings;
- evidence links and manifest hashes;
- required commands and their fresh output;
- reviewers, decision date, decision status, and rollback criteria.

## Human Review Requirement

Promotion requires human review. The reviewer must decide whether the evidence
supports the exact requested target mode and configuration. A Go decision is not
general approval for later code, later configs, different accounts, larger
capital, or a different runtime mode.

If evidence is incomplete, stale, irreproducible, or inconsistent with the
documented architecture, the promotion decision is No-Go or Needs More Evidence.

## Required Gates

Before a candidate can be considered for paper/live promotion, the packet must
show:

- research evidence with declared windows and no-lookahead discipline;
- ablation evidence and cost/slippage stress;
- trade diagnostics and risk interactions;
- backtest evidence through the shared Strategy SDK -> RiskEngine ->
  OrderManagerActor -> ExecutionActor -> AccountActor path when executable
  strategy behavior is involved;
- paper evidence, soak evidence, reconciliation, kill-switch, rollback, and
  operations review for live promotion;
- fresh verification commands appropriate to the code/config changes.

`make check` is required before milestone or live enablement when code changed.
Documentation-only promotion packets may record that no code changed and run the
narrow documentation verification commands instead.

## Decision Outcomes

- **Go:** only the exact reviewed build, config hash, account, strategy set,
  risk profile, capital limits, and runtime mode may proceed.
- **No-Go:** the packet returns to the originating flow with explicit gaps.
- **Needs More Evidence:** specific evidence, commands, or diagnostics are
  required before another review.

Later paper/live outcomes require a new review record. They cannot be backdated
into an earlier approval.
