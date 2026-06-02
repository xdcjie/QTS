## MCP Tools: codegraph

This project uses the `codegraph` MCP knowledge graph for code exploration,
impact analysis, and architecture questions. Prefer it before raw text search
when looking up symbols, callers, callees, flows, or ownership boundaries.

Use `codegraph_context` for task or area context, `codegraph_search` for symbol
lookup, `codegraph_explore` for related source snippets, `codegraph_node` for a
single symbol body, `codegraph_trace` for flow/path tracing, `codegraph_impact`
for blast radius, and `codegraph_status` for index health. Fall back to `rg` or
file reads when `codegraph` does not cover the needed detail.
