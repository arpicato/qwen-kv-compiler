"""Regression: the projected cosine term must be averaged per trajectory.

The original ``BatchedCausalTorchLoss`` summed raw row cosines under an output
projection, so duplicating a query row changed the loss linearly (identical
teacher/student gave loss 0 for 1 row and -3 for 4 rows). The corrected term
weights each row by ``wq`` (which sums to 1 per trajectory, exactly like the
MSE term), so duplicating rows leaves the loss unchanged.

These tests are pure CPU torch: no model, no shard, no GPU.
"""
import importlib.util
import os
import sys

import numpy as np
import torch

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_COMPILER = os.path.join(_ROOT, "scripts", "compile_torch_v2.py")


def load_compiler():
    spec = importlib.util.spec_from_file_location("compile_torch_v2", _COMPILER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["compile_torch_v2"] = mod
    spec.loader.exec_module(mod)
    return mod


def build_loss(mod, k, v, n_rows, o_proj):
    """One trajectory whose ``n_rows`` query rows are exact duplicates."""
    D = k.shape[-1]
    Hkv = k.shape[1]
    q = torch.ones(1, Hkv, 1, D)
    traj = {
        "item": 0,
        "q_rot": np.repeat(q.numpy(), n_rows, axis=2),
        "q_logical": np.full(n_rows, k.shape[2], dtype=np.int64),
        "k_live": np.zeros((1, Hkv, 0, D), np.float32),
        "v_live": np.zeros((1, Hkv, 0, D), np.float32),
        "k_logical": np.zeros(0, dtype=np.int64),
    }
    return mod.BatchedCausalTorchLoss(
        k, v, [traj], k.shape[2], device="cpu", o_proj=o_proj, cosine_weight=1.0
    )


def test_identical_teacher_student_cosine_is_zero_for_any_row_count():
    mod = load_compiler()
    torch.manual_seed(0)
    k = torch.randn(1, 1, 3, 2)
    v = torch.randn(1, 1, 3, 2)
    for n_rows in (1, 4, 9):
        loss = build_loss(mod, k, v, n_rows, torch.eye(2))
        val = float(loss.loss_fn(k, v))
        assert abs(val) < 1e-5, f"{n_rows} identical rows -> loss {val}, expected 0"


def test_duplicating_rows_does_not_change_cosine_term():
    mod = load_compiler()
    torch.manual_seed(1)
    k = torch.randn(1, 1, 3, 2)
    v = torch.randn(1, 1, 3, 2)
    one = build_loss(mod, k, v, 1, torch.eye(2))
    many = build_loss(mod, k, v, 5, torch.eye(2))
    assert abs(float(one.loss_fn(k, v)) - float(many.loss_fn(k, v))) < 1e-5


def test_cosine_term_is_bounded_when_projecting():
    """A summed row cosine scales with row count; an averaged one is in [-1, 1]."""
    mod = load_compiler()
    torch.manual_seed(2)
    k = torch.randn(1, 1, 3, 4)
    v = torch.randn(1, 1, 3, 4)
    W = torch.randn(4, 3) * 0.3
    loss = build_loss(mod, k, v, 12, W)
    val = float(loss.loss_fn(k, v))
    # loss = mse + (1 - mean_cos); mse >= 0 and mean_cos <= 1, so loss >= -1.
    assert val > -1.0 - 1e-4, f"loss {val} below the averaged-cosine floor -1"


def test_unprojected_branch_is_already_averaged():
    """Without o_proj the cosine term divides by the valid-row count, so it is
    a per-trajectory mean and duplicating rows leaves it unchanged."""
    mod = load_compiler()
    torch.manual_seed(4)
    k = torch.randn(1, 2, 3, 2)
    v = torch.randn(1, 2, 3, 2)
    one = build_loss(mod, k, v, 1, None)
    many = build_loss(mod, k, v, 5, None)
    v1, v5 = float(one.loss_fn(k, v)), float(many.loss_fn(k, v))
    assert abs(v1 - v5) < 1e-5, f"unprojected branch not row-count invariant: {v1} vs {v5}"
    for loss_val in (v1, v5):
        assert loss_val > -1.0 - 1e-4


def test_chunked_matches_unchunked_with_cosine():
    mod = load_compiler()
    torch.manual_seed(3)
    k = torch.randn(1, 1, 3, 2)
    v = torch.randn(1, 1, 3, 2)
    full = build_loss(mod, k, v, 6, torch.eye(2))
    chunked = build_loss(mod, k, v, 6, torch.eye(2))
    chunked.chunk = 2
    assert abs(float(full.loss_fn(k, v)) - float(chunked.loss_fn(k, v))) < 1e-5


if __name__ == "__main__":
    fns = [v for name, v in sorted(globals().items()) if name.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"{len(fns)} tests passed")
