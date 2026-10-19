# Vendored GitHub MCP tool schemas

`pkg/github/__toolsnaps__/*.snap` are tool-schema snapshots from
[github/github-mcp-server](https://github.com/github/github-mcp-server) (MIT),
vendored at pinned revision **`eb47a99ddb866ca2b8a162920e6bda9521f33ebb`**.

## Why vendored

`src/agent_probes_gen.py` builds the `agent_dev` / `agent_heldout` probe suites
from these schemas. It originally read them from a `/tmp/opencode/...` checkout
from an earlier session, which was lost. Without the schemas those suites silently
degraded: `agent_dev` fell back to the hand-written `agent` probes and
`agent_heldout` raised empty. Vendoring restores reproducibility.

## Regenerating

`scripts/fetch_agent_snapshots.sh` re-vendors at the pinned revision. Probe
semantics are derived from the snapshots, so a revision bump changes the probe
suites (and their IDs) — treat that as a deliberate, recorded change.

## Recovered probe counts (revision above)

| Suite | Probes | Composition |
|---|---:|---|
| `agent` (hand-written) | 78 | lookup 28 / style 20 / tool_select 26 / unrelated 4 |
| `agent_dev` | 276 | 78 hand-written + 198 generated |
| `agent_heldout` | 199 | tool_select 62 / lookup 137 |
