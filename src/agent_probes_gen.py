"""Programmatic probe generation from the real GitHub MCP tool schemas.

Produces many deterministic probes for the realistic agent-prompt regime,
grounded in the real ``__toolsnaps__`` schemas (github/github-mcp-server, MIT).
Two probe families:

* **tool_select**: which tool handles a described action -> exact tool name.
  Built from each tool's *own* description first sentence, but only when that
  sentence is a distinctive paraphrase (boilerplate descriptions excluded).
* **argument**: which argument of a named tool holds a described value ->
  exact argument name. Built from non-boilerplate argument descriptions.

Diversity guards:
* a shared boilerplate-arg allowlist (owner/repo/method/page/...) is excluded
  from argument probes because they appear in dozens of tools and add no signal;
* tool_select descriptions must be unique to one tool.

Partition: deterministic even/odd split into ``dev`` and ``heldout`` so the
regime has both a tuning set and a clean confirmation set.
"""
from __future__ import annotations

import glob
import json
import os
import re

# Pinned tool-schema snapshots. The original path was an ephemeral /tmp checkout
# that no longer exists, so the snapshots are now vendored at a pinned upstream
# revision (github/github-mcp-server @ eb47a99ddb866ca2b8a162920e6bda9521f33ebb).
# Override with AGENT_SNAPS_GLOB when reproducing on another machine.
_DEFAULT_SNAPS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data_mcp", "github-mcp-server", "pkg", "github", "__toolsnaps__", "*.snap",
)
SNAPS = os.environ.get("AGENT_SNAPS_GLOB", _DEFAULT_SNAPS)
PINNED_REVISION = "eb47a99ddb866ca2b8a162920e6bda9521f33ebb"

# arguments that recur across many tools: excluded from argument probes
BOILERPLATE_ARGS = {
    "owner", "repo", "method", "page", "perPage", "per_page", "cursor",
    "fields", "body", "title", "state", "type", "name", "id", "number",
    "org", "username", "q", "query", "limit", "sort", "order", "direction",
    "after", "before", "first", "last", "sha", "ref", "path", "base", "head",
}


def _first_sentence(desc: str) -> str:
    desc = desc.strip().split("\n")[0].strip()
    m = re.match(r"^(.*?[.!?])(\s|$)", desc)
    return (m.group(1) if m else desc).strip()


def load_tools():
    out = []
    for f in sorted(glob.glob(SNAPS)):
        d = json.load(open(f))
        # A few snapshots declare a null inputSchema; normalize so argument
        # probe generation never dereferences None.
        if d.get("inputSchema") is None:
            d["inputSchema"] = {"properties": {}}
        out.append(d)
    return out


def gen_tool_select(tools):
    """tool name -> probe, only where the first sentence is distinctive."""
    seen = {}
    cand = []
    for d in tools:
        fs = _first_sentence(d.get("description", ""))
        if len(fs) < 25:
            continue
        cand.append((d["name"], fs))
        seen.setdefault(fs.lower(), []).append(d["name"])
    probes = []
    for name, fs in cand:
        if len(seen[fs.lower()]) != 1:
            continue  # shared/boilerplate description
        # phrase as a request for the tool
        q = f"Which tool should be used to do the following: {fs}"
        probes.append({"q": q, "answer": name, "kind": "tool_select",
                       "topic": ["tool"]})
    return probes


def gen_arguments(tools):
    probes = []
    for d in tools:
        props = d.get("inputSchema", {}).get("properties", {})
        for k, v in props.items():
            if k in BOILERPLATE_ARGS:
                continue
            desc = (v.get("description") or "").strip().split("\n")[0]
            if len(desc) < 20:
                continue
            q = (f"For the tool `{d['name']}`, which argument is described as: "
                 f"{desc}")
            probes.append({"q": q, "answer": k, "kind": "lookup",
                           "topic": ["argument"]})
    return probes


def build(which: str):
    tools = load_tools()
    ts = gen_tool_select(tools)
    ar = gen_arguments(tools)
    allp = ts + ar
    # deterministic partition: even index -> dev, odd -> heldout
    dev = [p for i, p in enumerate(allp) if i % 2 == 0]
    held = [p for i, p in enumerate(allp) if i % 2 == 1]
    # de-duplicate by question (argument descriptions can repeat verbatim)
    def dedup(ps):
        seen, out = set(), []
        for p in ps:
            if p["q"] in seen:
                continue
            seen.add(p["q"])
            out.append(p)
        return out
    if which == "dev":
        return dedup(dev)
    if which == "heldout":
        return dedup(held)
    return dedup(allp)


if __name__ == "__main__":
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    ps = build(which)
    from collections import Counter
    print(f"{which}: {len(ps)} probes")
    print(Counter(p["kind"] for p in ps))
    for p in ps[:5]:
        print(f"  [{p['kind']}] Q: {p['q'][:80]}")
        print(f"       A: {p['answer']}")
    # audit: answer must appear in the tool schema text
    tools = load_tools()
    blob = json.dumps(tools).lower()
    miss = [p for p in ps if str(p["answer"]).lower() not in blob]
    print("answers not in schema blob:", len(miss))
