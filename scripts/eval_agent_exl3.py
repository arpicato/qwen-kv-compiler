#!/usr/bin/env python
"""EXL3 evaluation: teacher / none / compiled arms on the agent probesets.

ExLlama counterpart of ``eval_toolset_fast.py``. Because the DeltaNet state is
destructive (ExLlama cannot cleanly roll a recurrent model back to a prefix),
each probe rebuilds its prefix state by injection - cheap, no forward pass:

    teacher  -> write_prefix_state(block)                      prefix = n_sys
    compiled -> write synthetic K/V at slots [0,K), logical pos = n_sys
    none     -> clear cache                                    prefix = 0

Generation is greedy with the full EOS set and an optional 64-token cap, and
grading reuses ``src/eval.grade_instruction`` unchanged.

Usage:
    python eval_agent_exl3.py --compiled <dir> --probeset agent \
        --out /mnt/data/artifacts/kvcompile/results/agent_k6508.json
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import exl3  # noqa: E402
import eval as ev  # noqa: E402
import prompt as P  # noqa: E402
from probesets import load_probeset, probeset_identity, smoke_subset  # noqa: E402

GEN_PROTOCOL = "exl3-gpu-argmax-eos-set"

# Qwen3.5 EOS set (matches the MLX recorded protocol)
EOS_IDS = [248044, 248046]


def load_compiled(compiled_dir, K):
    """Return per-layer synthetic K/V tensors from compiled layer_*.safetensors."""
    from safetensors.torch import load_file
    out = {}
    for fn in os.listdir(compiled_dir):
        if fn.startswith("layer_") and fn.endswith(".safetensors"):
            L = int(fn.split("_")[1].split(".")[0])
            d = load_file(os.path.join(compiled_dir, fn))
            out[L] = {"k": d["k"], "v": d["v"]}
    return out


def install_prefix(model, cache, arm, *, n_sys, delta, attn, compiled, K):
    """Prepare the cache for one probe.

    Returns ``(logical_pos, physical_len)`` - equal for teacher/none, and
    ``(n_sys, K)`` for compiled (synthetic slots but true prompt position).
    """
    exl3.clear_cache(model, cache)
    if arm == "teacher":
        exl3.write_prefix_state(model, cache, delta, attn, n_sys)
        return n_sys, n_sys
    if arm == "compiled":
        # synthetic K/V occupy physical slots [0, K); logical continuation stays n_sys
        # compiled[L]["k"] is already (1, Hkv, K, D)
        syn_attn = {str(L): {"keys": compiled[L]["k"],
                             "values": compiled[L]["v"],
                             "offset": K} for L in compiled}
        exl3.write_prefix_state(model, cache, delta, syn_attn, K)
        return n_sys, K
    return 0, 0  # none


def gen_greedy(model, cache, tok, prompt_ids, *, cap, logical_pos, physical_len,
               max_tokens):
    """Greedy decode with full EOS set; returns (ids, text, stop_reason).

    ``logical_pos`` is the RoPE/recurrence continuation position; ``physical_len``
    is the number of slots already occupied in the paged cache (K for compiled,
    n_sys for teacher, 0 for none). These are equal for teacher/none and differ
    for compiled, which is why the split param path is used.
    """
    # Aliased recurrent-state handle pointing at slot 0 (the injected state).
    rs = [cache.recurrent_state_cls(cache, 0, logical_pos, clear=False, test_state=True)] \
        if logical_pos > 0 else None
    split = (physical_len != logical_pos)
    pl, lp, rs, logits, params = exl3.prefill_tokens_split(
        model, cache, prompt_ids, cap=cap, physical_len=physical_len,
        logical_pos=logical_pos, chunk=2048, recurrent_states=rs)
    out = []
    stop = "cap"
    for _ in range(max_tokens):
        nid = int(logits[0, -1].argmax().item())
        if nid in EOS_IDS:
            stop = "eos"
            break
        out.append(nid)
        if split:
            params = exl3.batch_params_split(cache, cap, pl, lp, 1, rs)
        else:
            params = exl3.batch_params(cache, cap, lp, rs)
        logits = model.forward(input_ids=torch.tensor([[nid]], dtype=torch.long, device="cuda:0"),
                               params=params)
        rs = params.get("recurrent_states", rs)
        pl += 1
        lp += 1
    text = tok.decode(torch.tensor([out], dtype=torch.long)) if out else ""
    if isinstance(text, list):
        text = text[0]
    return out, text, stop, logits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher", default="/mnt/data/artifacts/kvcompile/artifacts/agent/teacher")
    ap.add_argument("--compiled", default=None)
    ap.add_argument("--prompt-file", default="/home/arpin/kvcompile/prompts/agent_resident.txt")
    ap.add_argument("--model", default=os.path.expanduser(
        "~/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw"))
    ap.add_argument("--probeset", default="agent")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--cap", type=int, default=32768)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--arms", default=None, help="comma-separated subset of teacher,none,compiled")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--reread-state", default=None, help="advanced recurrent state/logical position; compiled arm only")
    args = ap.parse_args()
    if args.reread_state and (args.arms != 'compiled' or not args.compiled):
        raise ValueError('reread evaluation requires explicit compiled-only arm')
    Q = lambda *a, **k: print(*a, **k, flush=True)
    t0 = time.time()

    probes = load_probeset(args.probeset)
    if args.smoke:
        probes = smoke_subset(probes)
    if args.limit:
        probes = probes[:args.limit]
    pid = probeset_identity(probes)
    Q(f"probeset={args.probeset} n={len(probes)} id={pid}")

    model, cache, tok, cfg = exl3.load(args.model,
        max_seq_len=65536 if args.reread_state else args.cap, cache_size=args.cap)
    layers = exl3.full_attn_layers(model)

    body = open(args.prompt_file).read().rstrip()
    block = P.system_block(body)
    n_sys = len(exl3.encode(tok, block))
    from safetensors.torch import load_file
    st = load_file(os.path.join(args.teacher, "state.safetensors"))
    delta = {li: {"conv_state": st[f"delta.{li}.conv_state"],
                  "recurrent_state": st[f"delta.{li}.recurrent_state"]}
             for li in [str(x) for x in exl3.recurrent_layers(model)]}
    attn = {li: {"keys": st[f"attn.{li}.keys"], "values": st[f"attn.{li}.values"],
                 "offset": int(st[f"attn.{li}.offset"][0])}
            for li in [str(x) for x in layers]}
    Q(f"teacher state loaded, n_sys={n_sys}")
    reread_meta = None
    if args.reread_state:
        from pathlib import Path
        import hashlib
        root = Path(args.reread_state)
        reread_meta = json.loads((root/'state.json').read_text())
        gate = json.loads((root/'gate.json').read_text())
        assert gate['complete'] and gate['gate']['pass']
        assert reread_meta['config'] == gate['config']
        assert reread_meta['config']['model'] == args.model
        assert reread_meta['config']['prompt_sha256'] == hashlib.sha256(open(args.prompt_file, 'rb').read()).hexdigest()
        assert reread_meta['logical'] == 2 * n_sys
        saved = load_file(str(root/'state.safetensors'))
        delta = {li: {key: saved[f'delta.{li}.{key}'] for key in ('conv_state', 'recurrent_state')} for li in delta}
        n_sys = reread_meta['logical']
        del saved
        Q(f'reread recurrent state loaded, logical={n_sys}')

    compiled = None
    K = None
    if args.compiled:
        mf = json.load(open(os.path.join(args.compiled, "manifest.json")))
        K = mf["slots"]
        compiled = load_compiled(args.compiled, K)
        Q(f"compiled loaded K={K} layers={len(compiled)}")
        keep = mf.get("keep_prefix_tokens", 0)
        if keep:
            assert set(compiled) == set(layers)
            for L in layers:
                for name, teacher_name in (("k", "keys"), ("v", "values")):
                    assert compiled[L][name].shape[2] == K
                    assert torch.equal(compiled[L][name][:, :, :keep].half(),
                                       attn[str(L)][teacher_name][:, :, :keep].half())
            Q(f"PASS mixed exact leading rows={keep}, synthetic rows={K-keep}, total={K}")

    arms = ["teacher", "none"] + (["compiled"] if compiled else [])
    if args.arms:
        requested = args.arms.split(",")
        if not requested or not set(requested) <= set(arms):
            raise ValueError("invalid arms")
        arms = requested
    rows = {a: [] for a in arms}
    config = {"probeset_id": pid, "max_tokens": args.max_tokens, "cap": args.cap,
              "model": args.model, "teacher": args.teacher, "compiled": args.compiled,
              "arms": arms, "n_sys": n_sys}
    if reread_meta:
        config['reread_state'] = reread_meta
    if args.resume and os.path.exists(args.out):
        previous = json.load(open(args.out))
        if previous.get("config") != config:
            raise ValueError("evaluation resume configuration differs")
        rows = previous["rows"]
        for arm in arms:
            if [(r["q"], r["answer"]) for r in rows[arm]] != [(p["q"], p["answer"]) for p in probes[:len(rows[arm])]]:
                raise ValueError("evaluation resume questions differ")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    def checkpoint(summary=None):
        with open(args.out + ".partial", "w") as f:
            json.dump({"config": config, "summary": summary or {"complete": False},
                       "rows": rows}, f, indent=2)
        os.replace(args.out + ".partial", args.out)
    for arm in arms:
        Q(f"=== arm {arm} ===")
        for i, p in enumerate(probes):
            if i < len(rows[arm]):
                continue
            ple = exl3.encode(tok, P.user_turn(p["q"], think=False))
            logical, physical = install_prefix(model, cache, arm, n_sys=n_sys, delta=delta,
                                               attn=attn, compiled=compiled, K=K)
            ids, text, stop, _lg = gen_greedy(model, cache, tok, ple, cap=args.cap,
                                              logical_pos=logical, physical_len=physical,
                                              max_tokens=args.max_tokens)
            ok = (set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", text)) == set(p["strict_answers"])) \
                if "strict_answers" in p else ev.grade_instruction(text, p["answer"], p["kind"], p.get("topic"))
            rows[arm].append({"kind": p["kind"], "q": p["q"], "answer": p["answer"],
                              "ok": bool(ok), "pred": text, "stop": stop,
                               "n_tok": len(ids)})
            checkpoint()
            if (i+1) % 10 == 0 or i+1 == len(probes):
                elapsed = time.time()-t0
                completed = sum(len(r) for r in rows.values())
                total = len(arms)*len(probes)
                rate = completed/max(elapsed, .001)
                Q(f"{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s "
                  f"completed={completed}/{total} rate={rate:.3f}/s ETA={(total-completed)/rate:.1f}s arm={arm}")
        acc = np.mean([r["ok"] for r in rows[arm]]) if rows[arm] else 0.0
        Q(f"  {arm}: acc={acc:.3f} ({sum(r['ok'] for r in rows[arm])}/{len(rows[arm])}) "
          f"({time.time()-t0:.0f}s)")

    # informational retention: teacher-ok and none-fail
    summary = {"probeset": args.probeset, "probeset_id": pid, "n": len(probes),
               "gen_protocol": GEN_PROTOCOL, "max_tokens": args.max_tokens,
               "compiled": args.compiled, "slots": K,
               "by_arm_acc": {a: float(np.mean([r["ok"] for r in rows[a]])) for a in arms}}
    if set(("teacher", "none", "compiled")) <= set(arms):
        t = rows["teacher"]; n = rows["none"]; c = rows["compiled"]
        inform = [(t[i]["ok"] and not n[i]["ok"]) for i in range(len(t))]
        num = sum(1 for i in range(len(t)) if inform[i] and c[i]["ok"])
        den = sum(inform)
        summary["informative_retention_num"] = num
        summary["informative_retention_den"] = den
        summary["informative_retention"] = (num / den) if den else 0.0
        Q(f"informative retention: {num}/{den} = {summary['informative_retention']:.3f}")

    summary.update({"complete": True, "elapsed_s": time.time()-t0})
    checkpoint(summary)
    Q(f"DONE {time.time()-t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
