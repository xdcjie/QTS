---
id: vwap_pullback
owner: research
status: candidate
hypothesis: Intraday VWAP pullbacks revert after liquidity shocks when session regime and volume confirmation agree.
entrypoint: strategies.production.vwap_production_pullback:VwapProductionPullbackStrategy
default_config: configs/research/quickstart.yaml
failure_conditions:
  - Paper reconciliation has unexplained cash, position, or order drift.
  - Risk limit review rejects the configured quantity, stop, target, or capital envelope.
  - Kill switch drill, monitoring checks, or alert routing cannot be evidenced for the promoted config.
---

# vwap_pullback

## Lifecycle

Current status: `candidate`

Allowed status changes must be recorded through `PromotionDecision` gate evidence. Research, paper, and live outcomes are evidence for human review; they do not mutate this card or the registry without the matching lifecycle gate.

## Failure Conditions

- Paper reconciliation has unexplained cash, position, or order drift.
- Risk limit review rejects the configured quantity, stop, target, or capital envelope.
- Kill switch drill, monitoring checks, or alert routing cannot be evidenced for the promoted config.
