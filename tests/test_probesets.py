"""Probe-set loading and smoke-subset contracts.

These guard the evaluation interface: the old `--limit N` prefix convention was
not a valid task selector (probes are grouped by kind), and a smoke subset must
be kind-stratified, not a prefix.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dev_probes import build_dev_probes
from probesets import (load_probeset, probeset_identity, smoke_subset,
                       _validate)


def test_tool_probeset_loads():
    probes = load_probeset("tool")
    assert len(probes) == 103
    kinds = {p["kind"] for p in probes}
    assert "unrelated" in kinds
    assert len([p for p in probes if p["kind"] != "unrelated"]) == 97


def test_dev_probeset_shape():
    probes = build_dev_probes()
    assert len(probes) == 52
    dom = [p for p in probes if p["kind"] != "unrelated"]
    assert len(dom) == 48
    assert len(probes) - len(dom) == 4
    # registry load must match the builder
    assert load_probeset("dev") == probes
    # no unknown kinds (the grader routes on the kind string)
    assert {p["kind"] for p in probes} <= {
        "tool_select", "lookup", "revision", "ordering", "workflow",
        "error_policy", "refusal", "escalation", "style", "class_binding",
        "unrelated",
    }


def test_validate_rejects_malformed():
    for bad in ([], [{"q": "x", "answer": "y"}], [{"q": "", "answer": "y", "kind": "k"}],
                [{"q": "x", "answer": "", "kind": "k"}],
                [{"q": "x", "answer": "y", "kind": "k", "topic": "notalist"}]):
        try:
            _validate(bad, "bad")
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {bad!r}")


def test_identity_is_content_sensitive():
    a = [{"q": "q1", "answer": "a1", "kind": "k"}]
    b = [{"q": "q1", "answer": "a2", "kind": "k"}]
    c = [{"q": "q1", "answer": "a1", "kind": "k", "topic": ["t"]}]
    assert probeset_identity(a) != probeset_identity(b)
    assert probeset_identity(a) != probeset_identity(c)
    assert probeset_identity(a) == probeset_identity([dict(a[0])])
    # reordering changes the id (order is part of the task)
    d = [{"q": "q2", "answer": "a2", "kind": "k"}, {"q": "q1", "answer": "a1", "kind": "k"}]
    assert probeset_identity(a + b) != probeset_identity(b + a)
    assert probeset_identity(d) == probeset_identity(d)


def test_smoke_is_kind_stratified_not_prefix():
    probes = load_probeset("tool")
    sm = smoke_subset(probes, n_domain=12, n_control=2)
    assert len(sm) == 14
    dom = [p for p in sm if p["kind"] != "unrelated"]
    assert len(dom) == 12
    # must not be the first 12 of the list (those are all tool_select)
    assert len({p["kind"] for p in dom}) >= 8
    # control budget respected
    assert len([p for p in sm if p["kind"] == "unrelated"]) == 2
    # deterministic
    assert smoke_subset(probes, 12, 2) == sm


def test_heldout_probeset_shape_and_isolation():
    """Second held-out suite: shape, registry load, and the anti-overfit rule.

    It must not reuse any exact question from the 103 benchmark or the dev
    suite, and it must not grade any of the four known compiled failures.
    """
    from heldout_probes import build_heldout_probes, _KNOWN_FAILING_TARGETS
    probes = build_heldout_probes()
    assert load_probeset("heldout") == probes
    dom = [p for p in probes if p["kind"] != "unrelated"]
    assert len(probes) - len(dom) == 4  # 4 controls
    assert {p["kind"] for p in probes} <= {
        "tool_select", "lookup", "revision", "ordering", "workflow",
        "error_policy", "refusal", "escalation", "style", "class_binding",
        "unrelated",
    }
    # isolation from the other two suites
    seen = {p["q"] for p in load_probeset("tool")} | {p["q"] for p in build_dev_probes()}
    assert not (seen & {p["q"] for p in probes}), "held-out duplicates an existing probe"
    # anti-overfit: no probe targets a known failing fact
    leaked = [p["q"] for p in probes
              if str(p["answer"]).strip().lower() in _KNOWN_FAILING_TARGETS]
    assert not leaked, f"held-out targets known failing facts: {leaked}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok", fn.__name__)
    print("probeset tests: PASS")
