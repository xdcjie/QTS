# Trade Diagnostics

Trade diagnostics are required research evidence for paper and small-live
candidate review. They do not promote strategy code by themselves.

Each completed trade must include R-PnL, MAE_R, MFE_R, exit reason, direction,
positive quantity, non-negative holding bars, timing, and factor snapshot data
for standard artifacts.

Diagnostics support:

- direction, quantity, exit-reason, and factor-bucket summaries;
- missing and unbucketed factor evidence;
- overnight time buckets such as `20:00-02:00`;
- JSONL trade rows, JSON summary, and Markdown report artifacts.

Known failure modes: missing diagnostics, invalid direction, non-positive
quantity, negative holding bars, and paper/small-live candidate specs without
diagnostics, validation scorecard, or cost-stress evidence.
