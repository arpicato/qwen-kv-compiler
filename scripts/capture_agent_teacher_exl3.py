#!/usr/bin/env python
"""Capture the EXL3 teacher prefix state for the realistic agent prompt.

Writes ``state.safetensors`` (DeltaNet states + full-attn KV for the *block*
prefix) and ``state.json``, mirroring the MLX ``capture_system_teacher.py``
output so the eval path can install a full teacher prefix.

Usage:
    python capture_agent_teacher_exl3.py \
        --system-file /home/arpin/kvcompile/prompts/agent_resident.txt \
        --out /mnt/data/artifacts/kvcompile/artifacts/agent/teacher
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import exl3  # noqa: E402
import prompt as P  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--system-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default=os.path.expanduser(
        "~/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw"))
    ap.add_argument("--cap", type=int, default=32768)
    ap.add_argument("--chunk", type=int, default=2048)
    args = ap.parse_args()
    Q = lambda *a, **k: print(*a, **k, flush=True)
    t0 = time.time()

    body = open(args.system_file).read().rstrip()
    block = P.system_block(body)

    model, cache, tok, cfg = exl3.load(args.model, max_seq_len=args.cap, cache_size=args.cap)
    n_sys = len(exl3.encode(tok, block))
    Q(f"system tokens: {n_sys}")

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "system.txt"), "w") as f:
        f.write(body)

    exl3.clear_cache(model, cache)
    t1 = time.time()
    p, rs, _lg, pr = exl3.prefill_tokens(model, cache, exl3.encode(tok, block),
                                         cap=args.cap, chunk=args.chunk, past_len=0)
    assert p == n_sys, (p, n_sys)
    Q(f"prefilled {n_sys} tokens in {time.time()-t1:.1f}s")

    delta, attn = exl3.extract_teacher_state(model, cache, n_sys)
    kv_bytes = sum(a["keys"].numel() * a["keys"].element_size()
                   + a["values"].numel() * a["values"].element_size()
                   for a in attn.values())
    d_bytes = sum(d["recurrent_state"].numel() * d["recurrent_state"].element_size()
                  + d["conv_state"].numel() * d["conv_state"].element_size()
                  for d in delta.values())
    Q(f"teacher KV {kv_bytes/1e9:.3f} GB | DeltaNet {d_bytes/1e6:.1f} MB")

    arrays = {}
    for li, d in delta.items():
        arrays[f"delta.{li}.conv_state"] = d["conv_state"]
        arrays[f"delta.{li}.recurrent_state"] = d["recurrent_state"]
    for li, a in attn.items():
        arrays[f"attn.{li}.keys"] = a["keys"]
        arrays[f"attn.{li}.values"] = a["values"]
        arrays[f"attn.{li}.offset"] = torch.tensor([a["offset"]], dtype=torch.int64)
    from safetensors.torch import save_file
    path = os.path.join(args.out, "state.safetensors")
    save_file(arrays, path)

    meta = {"source": os.path.basename(args.system_file),
            "system_tokens": n_sys, "prompt_hash": exl3.prompt_hash(block),
            "model": os.path.basename(args.model),
            "teacher_kv_bytes": kv_bytes, "delta_bytes": d_bytes,
            "n_full_attn_layers": len(exl3.full_attn_layers(model)),
            "n_recurrent_layers": len(exl3.recurrent_layers(model))}
    with open(os.path.join(args.out, "state.json"), "w") as f:
        json.dump(meta, f, indent=2)
    Q(f"saved -> {path} ({os.path.getsize(path)/1e9:.3f} GB)")
    Q(f"n_sys={n_sys} prompt_hash={meta['prompt_hash']}")


if __name__ == "__main__":
    main()
