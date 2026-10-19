"""Probe-set diversity constraints.

Grading is token/yes-no match (``eval.grade_instruction``), so a probe set
dominated by one answer can be "passed" by a compiled model that learned a
default response, without retrieving anything from the handbook. That would
inflate the retention number and make the compression result look better than
it is.

These tests pin the invariant we rely on:
  * no single answer token exceeds ``MAX_ANSWER_SHARE`` of the set,
  * no two questions are near-duplicates (token Jaccard > ``MAX_JACCARD``),
  * the ``unrelated`` controls stay a small, separate slice.

They are fast and CPU-only (no model, no artifacts).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from collections import Counter

from tool_probes import MAX_ANSWER_SHARE, MAX_JACCARD, build_tool_probes


def probes():
    return build_tool_probes()


def _tokens(text: str) -> set[str]:
    return {t for t in "".join(c.lower() if c.isalnum() else " "
                               for c in text).split() if t}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def test_size_in_target_range(probes):
    """The set should be large enough for per-kind reading, per the plan."""
    assert 50 <= len(probes) <= 120


def test_no_single_answer_dominates(probes):
    counts = Counter(p["answer"].strip().lower() for p in probes)
    answer, n = counts.most_common(1)[0]
    share = n / len(probes)
    assert share <= MAX_ANSWER_SHARE, (
        f"answer {answer!r} is {share:.0%} of probes, over the "
        f"{MAX_ANSWER_SHARE:.0%} budget (n={n}/{len(probes)})"
    )


def test_answers_are_diverse(probes):
    """A large fraction of answers should be unique."""
    counts = Counter(p["answer"].strip().lower() for p in probes)
    assert len(counts) >= 0.6 * len(probes), (
        f"only {len(counts)} distinct answers for {len(probes)} probes"
    )


def test_no_near_duplicate_questions(probes):
    """Near-duplicate = same question AND same answer.

    Two probes may share a question frame ("Which prefix denotes X?") while
    asking genuinely different things; those are fine. What is not fine is a
    literal restatement, which inflates the set without adding coverage.
    """
    toks = [_tokens(p["q"]) for p in probes]
    answers = [p["answer"].strip().lower() for p in probes]
    offenders = []
    for i in range(len(probes)):
        for j in range(i + 1, len(probes)):
            if answers[i] != answers[j]:
                continue
            jac = _jaccard(toks[i], toks[j])
            if jac > MAX_JACCARD:
                offenders.append((jac, probes[i]["q"], probes[j]["q"]))
    assert not offenders, (
        "near-duplicate questions with the same answer (jaccard > "
        f"{MAX_JACCARD}): " + "; ".join(f"{j:.2f}: {a!r} / {b!r}"
                                        for j, a, b in offenders[:3])
    )


def test_controls_are_small(probes):
    """The uninformed-passing controls must not dominate the set."""
    n_unrel = sum(1 for p in probes if p["kind"] == "unrelated")
    assert 0 < n_unrel <= 0.10 * len(probes), (
        f"{n_unrel} unrelated controls is too many/few for {len(probes)} probes"
    )


def test_every_probe_has_required_fields(probes):
    for p in probes:
        assert p["q"].strip()
        assert p["answer"].strip()
        assert p["kind"].strip()


def test_yesno_probes_have_topic_for_disambiguation(probes):
    """grade_yesno uses ``topic`` to disambiguate copular denial, so every
    yes/no probe that needs it should carry one."""
    missing = []
    for p in probes:
        if p["answer"].strip().lower() in ("yes", "no") and not p.get("topic"):
            missing.append(p["q"])
    assert not missing, "yes/no probes missing topic: " + "; ".join(missing)


if __name__ == '__main__':
    rows = probes()
    for name, fn in sorted(globals().copy().items()):
        if name.startswith('test_'):
            fn(rows)
            print('PASS', name)
