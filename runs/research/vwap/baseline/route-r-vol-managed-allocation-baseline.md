# Route R Volatility-Managed Allocation Baseline

Baseline source: `runs/research/vwap/route-r/vol-managed-allocation-summary.json`

Source SHA-256: `38aeb26780896973850ee9ef8c9fc6f92af45d94f3c4662132c290e7640f6749`

Report source: `runs/research/vwap/route-r/reports/route-r-vol-managed-allocation-report.md`

Report SHA-256: `5d22425a580d7eba117117049417799d73c2b932bfd60970f7cd980826489a7d`

## Boundary

This baseline is research evidence only. It is not a tradable allocation config
and does not promote Route R into paper or live execution.

First-principles gate:

- Score periods: `is_2020_2022`, `validation_2022_2024`
- Baseline period: `is_2020_2022`
- Validation periods: `validation_2022_2024`
- Holdout report-only periods: `holdout_2024_2026`
- Weight construction uses prior returns only.

## Selected Parameters

| Parameter | Value |
| --- | ---: |
| `lookback_days` | 63 |
| `min_history_days` | 20 |
| `min_trailing_return` | 0 |
| `top_n_legs` | 2 |
| `target_annual_vol` | 0.40 |
| `max_gross_exposure` | 2.0 |
| `max_leg_weight` | 0.70 |

## Evidence

The selected allocation is rank 1 in the source summary, satisfies all declared
constraints, and has score `0.343646067459534555`.

| Period | Role | Annual Return | Total Return | Sharpe | Max Drawdown | Avg Gross Exposure |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `is_2020_2022` | score/baseline | 39.14% | 93.35% | 1.322 | 17.96% | 1.900 |
| `validation_2022_2024` | score/validation | 19.28% | 41.91% | 1.023 | 10.00% | 1.975 |
| `holdout_2024_2026` | report-only | 29.62% | 80.04% | 0.823 | 31.90% | 1.617 |

Selection constraints:

- Baseline annual return >= 10%: observed 39.14%
- Selection/post annual return >= 10%: observed minimum 19.28%
- Selection drawdown <= 20%: observed maximum 17.96%

## Cleanup Scope

After this baseline is frozen, the only VWAP research run artifacts intended to
remain are this `baseline` directory and the selected `route-r` source evidence.
