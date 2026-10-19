"""Probe-set loading: load named/JSON probe sets with a stable identity.

The evaluator (``scripts/eval_toolset_fast.py``) historically hard-coded
``build_tool_probes()`` and selected a prefix with ``--limit``. That is not a
valid evaluation interface: the 103-probe list is *grouped by kind*, so the
first N probes are one or two kinds, and two runs compared with ``--limit`` are
not the same task.

This module provides:

* ``load_probeset(spec, n_smoke_domain, n_smoke_control)`` -- load a probe set
  from a JSON file (``{"probes": [...]}`` or a bare list), a named registry
  entry, or the built-in tool probe set.
* ``smoke_subset(probes, ...)`` -- a *kind-stratified* subset (round-robin by
  kind, deterministic) so a cheap screen is still balanced across kinds.
* ``probeset_identity(probes)`` -- a hash of the graded content (question +
  answer + kind + topic) used for baseline-cache identity and provenance.

Every probe is a dict with at least ``q``, ``answer``, ``kind``; optional
``topic`` (list of keyword stems, used by yes/no grading).
"""

from __future__ import annotations

import hashlib
import json
import os

REQUIRED_FIELDS = ("q", "answer", "kind")


def _validate(probes: list[dict], name: str) -> list[dict]:
    if not isinstance(probes, list) or not probes:
        raise ValueError(f"probe set {name!r} is empty or not a list")
    for i, p in enumerate(probes):
        if not isinstance(p, dict):
            raise ValueError(f"probe {i} in {name!r} is not a dict")
        for f in REQUIRED_FIELDS:
            if f not in p:
                raise ValueError(f"probe {i} in {name!r} missing required field {f!r}")
        if not isinstance(p["q"], str) or not p["q"].strip():
            raise ValueError(f"probe {i} in {name!r} has empty question")
        if not isinstance(p["answer"], str) or not p["answer"].strip():
            raise ValueError(f"probe {i} in {name!r} has empty answer")
        topic = p.get("topic")
        if topic is not None and not isinstance(topic, list):
            raise ValueError(f"probe {i} in {name!r} has non-list topic")
    return probes


def load_probeset(spec: str) -> list[dict]:
    """Load a probe set from a JSON path, a named registry entry, or 'tool'.

    JSON: either a bare list or ``{"probes": [...]}``. Unknown fields are kept
    (they ride along into eval rows for provenance).
    """
    if spec in ("tool", "", None):
        from tool_probes import build_tool_probes
        return _validate(build_tool_probes(), "tool")

    if spec == "dev":
        from dev_probes import build_dev_probes
        return _validate(build_dev_probes(), "dev")

    if spec == "heldout":
        from heldout_probes import build_heldout_probes
        return _validate(build_heldout_probes(), "heldout")

    if spec == "agent":
        from agent_probes import build_agent_probes_full
        return _validate(build_agent_probes_full(), "agent")

    # Realistic agent-prompt regime, large programmatic suites (real tool schemas).
    if spec == "agent_dev":
        from agent_probes import build_agent_probes_full
        from agent_probes_gen import build as gen
        return _validate(list(build_agent_probes_full()) + gen("dev"), "agent_dev")

    if spec == "agent_heldout":
        from agent_probes_gen import build as gen
        return _validate(gen("heldout"), "agent_heldout")

    if spec.endswith(".json"):
        if not os.path.exists(spec):
            raise SystemExit(f"probe set file not found: {spec}")
        with open(spec) as f:
            data = json.load(f)
        probes = data["probes"] if isinstance(data, dict) else data
        return _validate(probes, spec)

    raise SystemExit(
        f"unknown probe set {spec!r}; use 'tool', 'dev', 'heldout', or a path to a .json file"
    )


def probeset_identity(probes: list[dict]) -> str:
    """Content hash over graded fields, order-sensitive.

    Used for provenance; baseline-cache identity keys per-prompt separately, so
    reordering checks stay valid. This hash answers "which task exactly".
    """
    payload = []
    for p in probes:
        payload.append({
            "q": p["q"],
            "answer": p["answer"],
            "kind": p["kind"],
            "topic": list(p["topic"]) if p.get("topic") else None,
        })
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:24]


def smoke_subset(probes: list[dict], n_domain: int = 12,
                 n_control: int = 2) -> list[dict]:
    """Deterministic kind-stratified subset for cheap screening.

    Round-robins over kinds (sorted) so the smoke set is not one or two kinds,
    taking domain probes up to ``n_domain`` and 'unrelated' up to ``n_control``.
    Preserves first-seen order within each kind. Not a substitute for the full
    suite; only for catastrophic-failure screening.
    """
    domain, control = [], []
    for p in probes:
        (control if p["kind"] == "unrelated" else domain).append(p)

    def round_robin(items: list[dict], n: int) -> list[dict]:
        by_kind: dict[str, list[dict]] = {}
        for p in items:
            by_kind.setdefault(p["kind"], []).append(p)
        out: list[dict] = []
        kinds = sorted(by_kind)
        idx = 0
        while len(out) < n:
            added = False
            for k in kinds:
                if idx < len(by_kind[k]) and len(out) < n:
                    out.append(by_kind[k][idx])
                    added = True
            if not added:
                break
            idx += 1
        return out

    return round_robin(domain, n_domain) + round_robin(control, n_control)


if __name__ == "__main__":
    import sys
    spec = sys.argv[1] if len(sys.argv) > 1 else "tool"
    probes = load_probeset(spec)
    from collections import Counter
    print(f"{len(probes)} probes  id={probeset_identity(probes)}")
    print(Counter(p["kind"] for p in probes))
    sm = smoke_subset(probes)
    print(f"smoke n={len(sm)}: {Counter(p['kind'] for p in sm)}")
