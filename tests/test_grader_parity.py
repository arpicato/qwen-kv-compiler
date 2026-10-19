"""Parity guard for the shared instruction grader.

The HF agent evaluator (ROCm/XTF, no MLX) must import and use the EXACT same
grading functions as the MLX-era evaluator. `src/eval.py` imports mlx lazily, so
grading works without it. This test pins:

1. The grader module imports with ``mlx is None``.
2. ``grade_instruction`` dispatches as documented (yes/no vs term vs containment).
3. The grader's public behavior is stable across a table of cases, so a future
   edit that silently changes scoring fails here instead of in a benchmark.

Run on the bench env (numpy available, mlx absent): that is the parity proof.
"""
import hashlib
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_EVAL = os.path.join(os.path.dirname(_HERE), "src", "eval.py")

# Cases: (pred, answer, kind, topic, expected). Verified against the MLX-era
# grader semantics; a bare "no" verdict is graded on the verdict itself.
#
# NOTE (documented tolerance, not drift): for tool kinds the grader strips
# `mcp__<server>__` from BOTH sides, so a bare tool name matches a qualified
# answer and vice versa. That is intentional (the teacher and compiled model
# differ in how they qualify tool names) but means the primary tool metric is
# NOT whole-identifier exact match; the plan adds a separate strict diagnostic.
CASES = [
    ("SyntheticKVCache", "SyntheticKVCache", "tool_select", None, True),
    ("the class is SyntheticKVCache.", "SyntheticKVCache", "tool_select", None, True),
    ("I think it is something else", "SyntheticKVCache", "tool_select", None, False),
    ("mcp__fs__read_file", "mcp__fs__read_file", "tool_select", None, True),
    ("read_file", "mcp__fs__read_file", "tool_select", None, True),  # bare/qualified tolerance
    ("mcp__fs__write_file", "mcp__fs__read_file", "tool_select", None, False),
    ("no, it is not a LoRA", "no", "policy", ["lora"], True),
    ("no", "no", "policy", None, True),
    ("no, the machine is not listed", "no", "policy", ["lora"], True),
    ("yes, that is allowed", "no", "policy", None, False),
    ("E409", "E409", "recall", None, True),
    ("the code is E409.", "E409", "recall", None, True),
    ("E410", "E409", "recall", None, False),
]


def load_eval():
    spec = importlib.util.spec_from_file_location("kv_eval_parity", _EVAL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kv_eval_parity"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_grader_imports_without_mlx():
    ev = load_eval()
    assert ev.mx is None, "this parity test must run where mlx is absent"


def test_grader_table_is_stable():
    ev = load_eval()
    bad = []
    for pred, answer, kind, topic, want in CASES:
        got = ev.grade_instruction(pred, answer, kind, topic)
        if got != want:
            bad.append((pred, answer, kind, got, want))
    assert not bad, f"grader drift: {bad}"


def test_grader_source_hash_recorded():
    """Persist a hash of the grader source for provenance (printed, not asserted
    against a constant, so legitimate edits are not blocked -- the behavior
    table above is the real guard)."""
    h = hashlib.sha256(open(_EVAL, "rb").read()).hexdigest()
    print(f"src/eval.py sha256={h}")
    assert len(h) == 64


if __name__ == "__main__":
    fns = [v for name, v in sorted(globals().items()) if name.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")
