"""EXL3 trajectory capture for the realistic agent prompt.

Reproduces the MLX ``capture_tool_traj_v2.py`` output (schema
``v2-causal-occupied``) on ExLlamaV3/ROCm, so the existing PyTorch compiler
(``scripts/compile_torch_v2.py``) consumes it unchanged.

Per training item, per full-attention layer, the shard entry holds:
    q_rot       (1,H,Lq,D) fp16   post-RoPE queries (last prompt row + answer rows)
    q_logical   (Lq,)      int32  logical position of each query row
    gate        (1,Lq,H*Dh) fp16  teacher attention gate at those rows
    k_live      (1,Hkv,Lk,D) fp16 occupied live keys (user suffix + answer)
    v_live      (1,Hkv,Lk,D) fp16
    k_logical   (Lk,)      int32
    n_user      int
    pred_tokens list[str]

Capture mechanism: wrap ``Attention.decode_flash_attn`` / ``decode_flash_attn_nc``
for the 16 full-attention layers and read ``q,k,v,g`` right after ``project_qkv``
+ RoPE (the tensors attention actually uses). The eager python path must run, so
the bc_attn graph path is disabled for the capture pass.

Usage:
    python capture_agent_exl3.py --items artifacts/agent/questions.json \
        --out /mnt/data/artifacts/kvcompile/artifacts/agent/traj --teacher <state>
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import pickle
import sys
import time

from capture_store import CaptureStore

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import exl3  # noqa: E402
import prompt as P  # noqa: E402

SCHEMA = "v2-causal-occupied"
_CONTENT_HINTS = ("no", "not", "never", "must", "use", "uppercase", "rule",
                  "sev", "e40", "e50", "shutdown", "isolate", "retry", "class",
                  "accept", "limit", "token", "timeout", "permission", "role",
                  "branch", "commit", "pnpm", "uv", "sops", "acme")


def choose_positions(ids, tok, max_pos):
    # decode((1,1)) returns a list[str]; flatten to one piece string per id
    toks = []
    for t in ids:
        s = tok.decode(torch.tensor([[int(t)]]), decode_special_tokens=True)
        toks.append(s[0] if isinstance(s, list) else s)
    content, rest = [], []
    for j, s in enumerate(toks):
        st = s.strip().lower()
        if st and not all(c in ".,;:!?-_/ \n\"'()" for c in st):
            (content if any(h in st for h in _CONTENT_HINTS) else rest).append(j)
    chosen = content[:max_pos]
    if len(chosen) < max_pos:
        for j in rest:
            if len(chosen) >= max_pos:
                break
            chosen.append(j)
    return sorted(set(chosen))


class Capture:
    """Wraps full-attn layers to record post-RoPE q/k/v/g."""

    def __init__(self, model, layers):
        self.rec = {}
        self.layers = set(layers)
        self._orig = {}
        self.model = model

    def attach(self):
        from exllamav3.modules import attn as _attn
        self._bc = getattr(_attn, "_qkv_slice_enable", True)
        _attn._qkv_slice_enable = False
        mods = exl3.attn_modules(self.model)
        for L in self.layers:
            a = mods.get(L)
            if a is None:
                raise RuntimeError(f"no Attention module for layer {L}")
            self._orig[L] = (a.decode_flash_attn_nc, a.decode_flash_attn)
            a.decode_flash_attn_nc = self._mk(a, L, False)
            a.decode_flash_attn = self._mk(a, L, True)

    def detach(self):
        from exllamav3.modules import attn as _attn
        _attn._qkv_slice_enable = self._bc
        mods = exl3.attn_modules(self.model)
        for L, (nc, c) in self._orig.items():
            mods[L].decode_flash_attn_nc = nc
            mods[L].decode_flash_attn = c

    def _mk(self, attn, L, cached):
        def run(x, bsz, seqlen, params, _attn=attn, _L=L, _cached=cached):
            q, k, v, g, o = _capture_qkvg(_attn, x, bsz, seqlen, params, cached=_cached)
            # Move to CPU immediately: keeping fp32 q/k/v/g for 16 layers on the
            # GPU while the 26k prefix + cache are resident exhausts VRAM (observed
            # as an HSA hardware fault, not a clean OOM).
            # A phase may issue several forwards (chunked prefill + final token);
            # concatenate along the sequence axis so every row is kept.
            new = {
                "q_rot": q.detach().to("cpu", torch.float32).numpy(),
                "k_rot": k.detach().to("cpu", torch.float32).numpy(),
                "values": v.detach().to("cpu", torch.float32).numpy(),
                "gate": g.detach().to("cpu", torch.float32).numpy(),
            }
            cur = self.rec.get(_L)
            if cur is None:
                self.rec[_L] = new
            else:
                for key in new:
                    cur[key] = np.concatenate([cur[key], new[key]], axis=1)
            return o
        return run

    def reset(self):
        self.rec = {}


def _capture_qkvg(attn, x, bsz, seqlen, params, cached):
    """Run attention eagerly, returning post-projection q,k,v,g and output o."""
    from exllamav3.util.tensor import get_for_device
    from exllamav3.modules.attention_fn import attn_dispatch
    from exllamav3.ext import exllamav3_ext as ext

    causal = params.get("causal", True)
    position = params.get("position", 0)
    positions = get_for_device(params, "positions", attn.device, None)
    position_ids = get_for_device(params, "position_ids", attn.device, None)
    inv_freq = get_for_device(params, "inv_freq", attn.device, None)

    q, k, v, g = attn.project_qkv(x, params)
    if attn.q_norm:
        if attn.tp_span_heads_norm:
            q, k = attn.apply_qk_norms_tp(q, k, params)
        elif not attn.rope or attn.q_norm_tensor is None:
            q = attn.q_norm.forward(q, params, out_dtype=torch.half)
            k = attn.k_norm.forward(k, params, out_dtype=torch.half)
    if attn.rope:
        q, k = attn.rope.apply(q, k, position, positions, position_ids, True,
                               attn.q_norm_tensor, attn.k_norm_tensor,
                               attn.norm_eps, attn.norm_constant_bias, inv_freq)

    if cached:
        block_table = get_for_device(params, "block_table", attn.device)
        cache_seqlens = get_for_device(params, "cache_seqlens", attn.device)
        o = attn_dispatch(q=q, k=k, v=v, cache=params["cache"],
                          cache_idx=attn.layer_idx, cache_instance=params.get("layer_instance"),
                          block_table=block_table, cache_seqlens=cache_seqlens,
                          causal=causal, sm_scale=attn.sm_scale,
                          window_size=attn.sliding_window, softcap=attn.logit_softcapping,
                          sinks=attn.sinks, dispatch_cache=attn.dispatch_cache)
    else:
        o = attn_dispatch(q=q, k=k, v=v, causal=causal, sm_scale=attn.sm_scale,
                          window_size=attn.sliding_window, softcap=attn.logit_softcapping,
                          sinks=attn.sinks, dispatch_cache=attn.dispatch_cache)

    if attn.headwise_gate:
        ext.mul_sigmoid_broadcast_(o, g)
    o = o.reshape((bsz, seqlen, attn.num_q_heads * attn.head_dim))
    if attn.full_gate or attn.interleaved_gate:
        ext.mul_sigmoid_(o, g)
    o = attn.project_o(o, bsz, seqlen, params)
    return q, k, v, g, o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt-file", default="/home/arpin/kvcompile/prompts/agent_resident.txt")
    ap.add_argument("--model", default=os.path.expanduser(
        "~/exllamav3-rocm/models/Qwen3.8-27B-EXL3-3.5bpw"))
    ap.add_argument("--cap", type=int, default=32768)
    ap.add_argument("--max-pred-pos", type=int, default=10)
    ap.add_argument("--position-plan", help="frozen per-item answer query rows, verified against token IDs")
    ap.add_argument("--max-items", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--teacher-out", default=None)
    ap.add_argument("--partition-tools", action="store_true",
                    help="record exact leading policy/skill token boundary, without changing the prompt")
    ap.add_argument("--verify-roundtrip", action="store_true")
    ap.add_argument("--seed-traj", default=None,
                    help="reuse verified leading calibration trajectories from the same full teacher")
    ap.add_argument("--teacher-in", default=None, help="reuse saved full teacher state with verified prompt identity")
    ap.add_argument("--checkpoint-every", type=int, default=5)
    ap.add_argument("--reread-state", default=None, help="verified reread state root; split physical/logical prefix")
    args = ap.parse_args()
    if not 1 <= args.checkpoint_every <= 25:
        raise ValueError('checkpoint interval must be 1..25 questions')
    if args.reread_state and (args.teacher_in or args.teacher_out or args.seed_traj or args.partition_tools or args.verify_roundtrip):
        raise ValueError('reread capture must not reuse/export ordinary teacher state or trajectories')
    Q = lambda *a, **k: print(*a, **k, flush=True)
    t0 = time.time()

    with open(args.items) as f:
        data = json.load(f)
    items = data["items"] if isinstance(data, dict) else data
    if args.max_items:
        items = items[:args.max_items]
    position_plan = None
    if args.position_plan:
        import hashlib
        plan_bytes = open(args.position_plan, 'rb').read()
        position_plan = json.loads(plan_bytes)
        if (position_plan['items_hash'] != exl3.prompt_hash(json.dumps(items, sort_keys=True))
                or position_plan['max_pred_pos'] != args.max_pred_pos
                or len(position_plan['rows']) != len(items)):
            raise ValueError('query plan differs from calibration items or row cap')
    Q(f"items: {len(items)}")

    model, cache, tok, cfg = exl3.load(args.model,
        max_seq_len=65536 if args.reread_state else args.cap, cache_size=args.cap)
    layers = exl3.full_attn_layers(model)
    Q(f"full-attn layers: {layers}")

    body = open(args.prompt_file).read().rstrip()
    block = P.system_block(body)
    block_ids = exl3.encode(tok, block)
    n_sys = len(block_ids)
    Q(f"n_sys={n_sys}")
    keep = 0
    if args.partition_tools:
        marker = "\n# Connected MCP tools\n"
        if body.count(marker) != 1:
            raise ValueError("expected one tool-catalog boundary")
        leading = exl3.encode(tok, P.IM_START + "system\n" + body.split(marker)[0] + "\n")
        for a, b in zip(leading, block_ids):
            if a != b:
                break
            keep += 1
        if not 0 < keep < n_sys:
            raise ValueError("invalid exact-token boundary")
        Q(f"partition: exact leading rows={keep}, tool tail rows={n_sys-keep}")

    # teacher prefix state (block only) captured once, reused per item
    exl3.clear_cache(model, cache)
    physical = n_sys
    reread_meta = None
    if args.reread_state:
        from pathlib import Path
        from safetensors.torch import load_file
        root = Path(args.reread_state)
        gate = json.loads((root/'gate.json').read_text())
        reread_meta = json.loads((root/'state.json').read_text())
        assert gate['complete'] and gate['gate']['pass']
        assert reread_meta['config'] == gate['config']
        assert reread_meta['roundtrip']['state_bit_exact'] and reread_meta['roundtrip']['argmax_equal']
        import hashlib
        assert reread_meta['config']['prompt_sha256'] == hashlib.sha256(open(args.prompt_file, 'rb').read()).hexdigest()
        assert reread_meta['config']['model'] == args.model
        physical, n_sys = reread_meta['physical'], reread_meta['logical']
        assert physical + 1024 <= args.cap and n_sys == 2 * len(block_ids)
        saved = load_file(str(root/'state.safetensors'))
        delta = {str(L): {key: saved[f"delta.{L}.{key}"] for key in ('conv_state', 'recurrent_state')}
                 for L in exl3.recurrent_layers(model)}
        attn = {str(L): {'keys': saved[f'attn.{L}.keys'], 'values': saved[f'attn.{L}.values'],
                        'offset': physical} for L in layers}
        del saved
    elif args.teacher_in:
        from safetensors.torch import load_file
        saved_meta = json.load(open(os.path.join(args.teacher_in, "state.json")))
        assert saved_meta["system_tokens"] == n_sys and saved_meta["prompt_hash"] == exl3.prompt_hash(block)
        assert saved_meta["model"] == args.model
        saved = load_file(os.path.join(args.teacher_in, "state.safetensors"))
        delta = {str(L): {key: saved[f"delta.{L}.{key}"] for key in ("conv_state", "recurrent_state")}
                 for L in exl3.recurrent_layers(model)}
        attn = {str(L): {"keys": saved[f"attn.{L}.keys"], "values": saved[f"attn.{L}.values"],
                         "offset": int(saved[f"attn.{L}.offset"][0])} for L in layers}
        exl3.write_prefix_state(model, cache, delta, attn, n_sys)
        rs = [cache.recurrent_state_cls(cache, 0, n_sys, clear=False, test_state=True)]
        del saved
    else:
        p, rs, _lg, pr = exl3.prefill_tokens(model, cache, block_ids, cap=args.cap,
                                             chunk=2048, past_len=0)
        assert p == n_sys, (p, n_sys)
        delta, attn = exl3.extract_teacher_state(model, cache, n_sys)
    sys_kv = {L: (attn[str(L)]["keys"].half(), attn[str(L)]["values"].half()) for L in layers}
    Q(f"teacher prefix captured ({n_sys} tok)")
    roundtrip = None
    if args.verify_roundtrip:
        probe = exl3.encode(tok, P.user_turn(items[0]["q"], think=False))
        _, _, direct, _ = exl3.prefill_tokens(model, cache, probe, cap=args.cap,
                                             past_len=n_sys, recurrent_states=rs)
        exl3.clear_cache(model, cache)
        exl3.write_prefix_state(model, cache, delta, attn, n_sys)
        rd, ra = exl3.extract_teacher_state(model, cache, n_sys)
        assert all(torch.equal(ra[li][key], attn[li][key]) for li in attn for key in ("keys", "values"))
        assert all(torch.equal(rd[li][key], delta[li][key]) for li in delta for key in delta[li])
        restored_rs = [cache.recurrent_state_cls(cache, 0, n_sys, clear=False, test_state=True)]
        _, _, restored, _ = exl3.prefill_tokens(model, cache, probe, cap=args.cap,
            past_len=n_sys, recurrent_states=restored_rs)
        assert direct[0, -1].argmax().item() == restored[0, -1].argmax().item()
        roundtrip = {"state_bit_exact": True, "argmax_equal": True,
                     "logit_max_diff": float((direct-restored).abs().max())}
        Q("PASS prefix roundtrip " + json.dumps(roundtrip))
        del rd, ra, direct, restored
    if args.teacher_out:
        from pathlib import Path
        from safetensors.torch import save_file
        root = Path(args.teacher_out)
        root.mkdir(parents=True, exist_ok=True)
        arrays = {f"delta.{li}.{key}": value for li, state in delta.items() for key, value in state.items()}
        for li, state in attn.items():
            arrays[f"attn.{li}.keys"] = state["keys"]
            arrays[f"attn.{li}.values"] = state["values"]
            arrays[f"attn.{li}.offset"] = torch.tensor([state["offset"]])
        save_file(arrays, str(root/"state.safetensors.partial"))
        (root/"state.safetensors.partial").replace(root/"state.safetensors")
        (root/"state.json").write_text(json.dumps({"system_tokens": n_sys,
            "prompt_hash": exl3.prompt_hash(block), "keep_prefix_tokens": keep,
            "model": args.model}, indent=2))
        del arrays

    cap = Capture(model, layers)
    os.makedirs(args.out, exist_ok=True)
    per_layer = {L: [] for L in layers}
    index = []
    meta = {"source": args.items, "schema": SCHEMA, "n_items": len(items),
            "layers": layers, "n_sys": n_sys, "max_pred_pos": args.max_pred_pos,
            "prompt_hash": exl3.prompt_hash(block), "keep_prefix_tokens": keep,
             "items_hash": exl3.prompt_hash(json.dumps(items, sort_keys=True))}
    if position_plan:
        meta['position_plan_sha256'] = hashlib.sha256(plan_bytes).hexdigest()
    if reread_meta:
        meta['reread_state'] = reread_meta
        meta['physical_prefix'] = physical
    meta_path = os.path.join(args.out, "meta.json")
    previous = None
    if os.path.exists(meta_path):
        if not args.resume:
            raise ValueError('capture output already exists; use --resume')
        previous = json.load(open(meta_path))
        if any(previous['meta'].get(k) != v for k, v in meta.items()):
            raise ValueError('capture resume configuration differs')
        index = previous['index']
        if [(r['q'], r['answer']) for r in index] != [(r['q'], r['answer']) for r in items[:len(index)]]:
            raise ValueError('capture index differs')
        if previous['meta'].get('complete'):
            Q(f"Already complete -> {args.out}")
            return
    store = CaptureStore(args.out, layers, SCHEMA,
                         previous.get('storage') if previous else None)
    for L in layers:
        k_sys, v_sys = sys_kv[L]
        store.write_prefix(L, {'k_sys': k_sys.numpy().astype(np.float16),
                               'v_sys': v_sys.numpy().astype(np.float16)})
    def payload(complete=False):
        elapsed_before = previous['meta'].get('elapsed_s', 0) if previous else 0
        return {'meta': {**meta, 'roundtrip': roundtrip, 'elapsed_s': elapsed_before+time.time()-t0,
                         'complete': complete}, 'index': index}
    if previous:
        if previous.get('storage'):
            store.validate(len(index))
        else:
            # Migrate a legacy checkpoint one layer at a time; source files stay
            # intact until the new offset manifest has been atomically published.
            for L in layers:
                with open(os.path.join(args.out, f'layer_{L:03d}.pkl'), 'rb') as f:
                    saved = pickle.load(f)
                rows = saved['traj'][:len(index)]
                if len(rows) != len(index):
                    raise ValueError('incomplete legacy capture checkpoint')
                for name, tensor in zip(('k_sys', 'v_sys'), sys_kv[L]):
                    if not np.array_equal(saved[name], tensor.numpy()):
                        raise ValueError('legacy checkpoint teacher KV differs')
                store.append(L, rows)
                del saved, rows
            store.validate(len(index))
            store.checkpoint(per_layer, payload())
    if args.seed_traj and not os.path.exists(meta_path):
        seed_meta = json.load(open(os.path.join(args.seed_traj, "meta.json")))
        assert seed_meta["meta"]["complete"]
        assert seed_meta["meta"]["prompt_hash"] == meta["prompt_hash"]
        assert seed_meta["meta"]["n_sys"] == n_sys
        assert seed_meta["meta"]["layers"] == layers
        assert seed_meta["meta"]["max_pred_pos"] == args.max_pred_pos
        index = seed_meta["index"]
        assert [(r["q"], r["answer"]) for r in index] == [(r["q"], r["answer"]) for r in items[:len(index)]]
        if position_plan:
            for item, row in zip(items, position_plan['rows'][:len(index)]):
                ids = exl3.encode(tok, P.assistant_turn(item.get('answer_text', item['answer'])))
                assert row['answer_ids'] == ids and row['positions'] == choose_positions(ids, tok, args.max_pred_pos)
            assert 'position_plan_sha256' not in seed_meta['meta'], 'only legacy seed positions verified'
        for L in layers:
            with open(os.path.join(args.seed_traj, f"layer_{L:03d}.pkl"), "rb") as f:
                saved = pickle.load(f)
            for name, tensor in zip(("k_sys", "v_sys"), sys_kv[L]):
                assert np.array_equal(saved[name], tensor.numpy())
            assert len(saved["traj"]) == len(index)
            store.append(L, saved['traj'])
            del saved
        store.validate(len(index))
        store.checkpoint(per_layer, payload())
        Q(f"PASS reused {len(index)} original trajectories; teacher KV bit-exact")
    def checkpoint(complete=False):
        store.checkpoint(per_layer, payload())
        if complete:
            export_start = time.time()
            def progress(L):
                done = layers.index(L)+1
                elapsed = time.time()-export_start
                rate = done/max(elapsed, .001)
                Q(f"{datetime.now(timezone.utc).isoformat()} export elapsed={elapsed:.1f}s "
                  f"completed={done}/{len(layers)} rate={rate:.3f}layers/s "
                  f"ETA={(len(layers)-done)/rate:.1f}s layer={L}")
            store.finalize(len(index), progress)
            store.checkpoint(per_layer, payload(complete=True))

    for i, item in enumerate(items):
        if i < len(index):
            continue
        q = item["q"]
        ans_text = item.get("answer_text", item["answer"])
        ut = P.user_turn(q, think=False)
        ans = P.assistant_turn(ans_text)
        ut_ids = exl3.encode(tok, ut)
        ans_ids = exl3.encode(tok, ans)
        if not ans_ids:
            continue
        n_user = len(ut_ids)

        # install exact prefix (no forward needed)
        exl3.clear_cache(model, cache)
        exl3.write_prefix_state(model, cache, delta, attn, physical)
        rs = [cache.recurrent_state_cls(cache, 0, n_sys, clear=False, test_state=True)]

        cap.attach()
        cap.reset()
        # --- user turn forward (records last-row q/gate; fills user-suffix KV)
        pl, p, rs, _lg, pr = exl3.prefill_tokens_split(model, cache, ut_ids, cap=args.cap,
            chunk=2048, physical_len=physical, logical_pos=n_sys, recurrent_states=rs)
        rs = pr.get("recurrent_states", rs)
        n_live_user = p - n_sys
        user_rec = {L: cap.rec[L] for L in layers if L in cap.rec}
        user_suffix = {}
        from exllamav3.constants import PAGE_SIZE
        for L in layers:
            lay = exl3._attn_layer(cache, L)
            pages = (pl + PAGE_SIZE - 1) // PAGE_SIZE
            H, D = lay.k.shape[2], lay.k.shape[3]
            kk = lay.k[:pages].reshape(pages * PAGE_SIZE, H, D)[physical:pl]
            vv = lay.v[:pages].reshape(pages * PAGE_SIZE, H, D)[physical:pl]
            user_suffix[L] = (kk.transpose(0, 1).unsqueeze(0).half().cpu(),
                              vv.transpose(0, 1).unsqueeze(0).half().cpu())

        # --- answer forward (records all answer rows)
        cap.reset()
        pl2, p2, rs, _lg, pr = exl3.prefill_tokens_split(model, cache, ans_ids, cap=args.cap,
            chunk=2048, physical_len=pl, logical_pos=p, recurrent_states=rs)
        rs = pr.get("recurrent_states", rs)

        pos_ans = choose_positions(ans_ids, tok, args.max_pred_pos)
        if position_plan:
            row = position_plan['rows'][i]
            pos_ans = row['positions']
            if (row['q'] != q or row['answer'] != item['answer'] or row['answer_ids'] != ans_ids
                    or pos_ans != sorted(set(pos_ans)) or len(pos_ans) > args.max_pred_pos
                    or any(type(j) is not int or not 0 <= j < len(ans_ids) for j in pos_ans)):
                raise ValueError(f'invalid query plan at item {i}')
        for L in layers:
            urec = user_rec.get(L)
            arec = cap.rec.get(L)
            if urec is None or arec is None:
                continue
            # ExLlama records (B, L, H, D) as numpy fp32; the v2 schema is
            # (B, H, L, D) fp16. gate stays (B, L, H*Dh).
            uq, ug = urec["q_rot"], urec["gate"]
            aq, ak, av, ag = arec["q_rot"], arec["k_rot"], arec["values"], arec["gate"]
            last_q = np.transpose(uq[:, -1:, :, :], (0, 2, 1, 3))      # (1,H,1,D)
            last_gate = ug[:, -1:, :]                                  # (1,1,H*Dh)
            q_ans = np.transpose(aq, (0, 2, 1, 3))                     # (1,H,Lans,D)
            k_ans = np.transpose(ak, (0, 2, 1, 3))                     # (1,Hkv,Lans,D)
            v_ans = np.transpose(av, (0, 2, 1, 3))
            g_ans = ag                                                 # (1,Lans,H*Dh)

            k_live_all = np.concatenate([user_suffix[L][0].cpu().numpy(),
                                         k_ans.astype(np.float16)], axis=2)
            v_live_all = np.concatenate([user_suffix[L][1].cpu().numpy(),
                                         v_ans.astype(np.float16)], axis=2)
            live_pos = np.arange(n_live_user + len(ans_ids), dtype=np.int32) + n_sys

            q_rows = np.concatenate([last_q.astype(np.float16),
                                     q_ans[:, :, pos_ans, :].astype(np.float16)], axis=2)
            g_rows = np.concatenate([last_gate.astype(np.float16),
                                     g_ans[:, pos_ans, :].astype(np.float16)], axis=1)
            q_logical = np.array([n_sys + n_live_user - 1] +
                                 [n_sys + n_live_user + pp for pp in pos_ans], dtype=np.int32)
            pred_tokens = []  # filled crudely; compiler does not need exact strings
            per_layer[L].append({
                "item": i, "kind": item.get("kind", "unknown"), "schema": SCHEMA,
                "q_rot": q_rows, "q_logical": q_logical, "gate": g_rows,
                "k_live": k_live_all, "v_live": v_live_all, "k_logical": live_pos,
                "n_user": int(n_live_user), "pred_tokens": pred_tokens,
                "entropy": 0.0, "q": q, "answer": item.get("answer"),
            })
        cap.detach()
        index.append({"item": i, "q": q, "kind": item.get("kind"),
                      "answer": item.get("answer"), "n_ans": len(ans_ids),
                      "n_live_user": int(n_live_user)})
        exl3.clear_cache(model, cache)
        if (i + 1) % args.checkpoint_every == 0:
            checkpoint()
        if (i + 1) % 5 == 0:
            elapsed = time.time()-t0
            rate = (i+1)/elapsed
            Q(f"{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s "
              f"completed={i+1}/{len(items)} rate={rate:.3f}/s ETA={(len(items)-i-1)/rate:.1f}s")

    checkpoint(complete=True)
    Q(f"DONE {time.time()-t0:.0f}s -> {args.out}")


if __name__ == "__main__":
    main()
