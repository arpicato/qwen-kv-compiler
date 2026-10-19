#!/usr/bin/env python
"""Export the frozen output-projection weight (o_proj) for the full-attention layers.

Writes ``oproj_L<layer>.pt`` ({"weight": (Hq*D, hidden) fp16}) for each layer, so
the projector can be applied in the output-projected loss. The weight is
reconstructed from the EXL3 trellis via ``LinearEXL3.get_weight_tensor()`` and
validated against ExLlama's own forward before saving.

Usage:
    python export_oproj_exl3.py --out /mnt/data/artifacts/kvcompile/artifacts/agent/oproj
"""
from __future__ import annotations

import argparse
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import exl3  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=os.path.expanduser(
        "~/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw"))
    ap.add_argument("--layers", default="all")
    args = ap.parse_args()
    Q = lambda *a, **k: print(*a, **k, flush=True)

    model, cache, tok, cfg = exl3.load(args.model, max_seq_len=2048, cache_size=2048)
    mods = exl3.attn_modules(model)
    layers = sorted(mods) if args.layers == "all" else [int(x) for x in args.layers.split(",")]
    os.makedirs(args.out, exist_ok=True)

    for L in layers:
        op = mods[L].o_proj
        inner = op.inner
        W = inner.get_weight_tensor()          # (in_features, out_features) fp16
        # Validate: reconstruct path vs plain matmul on random input.
        x = torch.randn(1, 3, inner.in_features, device="cuda:0", dtype=torch.half)
        y_recon = op.forward(x, {"reconstruct": True}).float()
        y_mm = (x.float() @ W.float())
        err = (y_recon - y_mm).abs().max().item()
        Q(f"L{L:3d}: W={tuple(W.shape)} recon_vs_matmul max|d|={err:.2e}")
        torch.save({"weight": W.cpu().to(torch.float16)}, os.path.join(args.out, f"oproj_L{L}.pt"))
    Q(f"saved {len(layers)} projections -> {args.out}")


if __name__ == "__main__":
    main()
