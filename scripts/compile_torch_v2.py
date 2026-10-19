#!/usr/bin/env python
"""PyTorch/CUDA port of the corrected (v2) synthetic-KV compiler.

Consumes ``capture_tool_traj_v2`` shards (schema ``v2-causal-occupied``) and
writes the same ``layer_NNN.safetensors`` artifact format as the MLX v2 path
(bf16 by default).

Loss (identical semantics to src/batched_loss_v2.py):
  * causal live-key support from per-query/per-key logical positions,
  * occupied-length live region (no capacity padding),
  * optional gate weighting (E5): error compared as sigmoid(gate)*out,
  * optional frozen attention sink at slot 0 (E2),
  * optional trajectory minibatching (E4).

No model is needed. Meant for the CUDA box; falls back to CPU.

Usage:
    python compile_torch_v2.py --traj traj_v2 --out out/e1 --ratio 0.25 --steps 400 --batched
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F


def gqa(x, n_rep):
    if n_rep == 1:
        return x
    B, H, L, D = x.shape
    return x[:, :, None, :, :].expand(B, H, n_rep, L, D).reshape(B, H * n_rep, L, D)


def sdpa(q, k, v, scale, mask=None):
    """GQA-aware SDPA via torch's native enable_gqa (avoids materializing the
    expanded K/V, which OOMs a 6 GB card at K=4738)."""
    return F.scaled_dot_product_attention(q, k, v, scale=scale, attn_mask=mask,
                                          enable_gqa=True)


class MLXAdam:
    """Adam matching mlx.optimizers.Adam defaults (bias_correction=False)."""

    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8):
        self.params = list(params)
        self.lr = lr
        self.b1, self.b2 = betas
        self.eps = eps
        self.m = [torch.zeros_like(p) for p in self.params]
        self.v = [torch.zeros_like(p) for p in self.params]

    def zero_grad(self, set_to_none=True):
        for p in self.params:
            p.grad = None

    @torch.no_grad()
    def step(self):
        for i, p in enumerate(self.params):
            g = p.grad
            self.m[i].mul_(self.b1).add_(g, alpha=1 - self.b1)
            self.v[i].mul_(self.b2).addcmul_(g, g, value=1 - self.b2)
            p.addcdiv_(self.m[i], self.v[i].sqrt().add_(self.eps), value=-self.lr)


def lr_schedule(step, steps, base_lr, kind="none", floor_frac=0.1, warmup_frac=0.05):
    """Per-step lr. 'none' = static. 'cosine' = optional linear warmup then cosine
    decay to floor_frac*base_lr. 'linear' = linear decay to floor_frac*base_lr.
    """
    if kind == "none" or steps <= 1:
        return base_lr
    floor = base_lr * floor_frac
    w = max(1, int(round(warmup_frac * steps))) if warmup_frac > 0 else 0
    if step < w:
        return base_lr * (step + 1) / w
    t = (step - w) / max(1, steps - w)
    t = min(1.0, max(0.0, t))
    if kind == "cosine":
        return floor + 0.5 * (base_lr - floor) * (1 + math.cos(math.pi * t))
    if kind == "linear":
        return base_lr + (floor - base_lr) * t
    return base_lr


def _causal_mask(qlog, klog, n_syn, device):
    """(Lq, n_syn+Lk) float additive mask; system prefix always visible."""
    qlog = torch.as_tensor(qlog, dtype=torch.long)
    klog = torch.as_tensor(klog, dtype=torch.long)
    live = (klog[None, :] <= qlog[:, None]).float().to(device)
    sysm = torch.ones(qlog.shape[0], n_syn, device=device)
    return torch.cat([sysm, live], dim=1)


def init_from_teacher(k_sys, v_sys, n_slots, seed, freeze_sink=False):
    n_pos = k_sys.shape[2]
    rng = np.random.default_rng(seed)
    if freeze_sink:
        edges = np.linspace(1, n_pos, n_slots)
        idx = np.array([rng.integers(int(edges[j]), max(int(edges[j]) + 1, int(edges[j + 1])))
                        for j in range(len(edges) - 1)]).clip(1, n_pos - 1).astype(np.int64)
        idx = np.concatenate([[0], idx])
    else:
        edges = np.linspace(0, n_pos, n_slots + 1)
        idx = np.array([rng.integers(int(edges[j]), max(int(edges[j]) + 1, int(edges[j + 1])))
                        for j in range(n_slots)]).clip(0, n_pos - 1).astype(np.int64)
    t = torch.from_numpy(idx).to(k_sys.device)
    return k_sys.index_select(2, t).clone(), v_sys.index_select(2, t).clone()


def init_mixed_prefix(k_sys, v_sys, n_slots, seed, keep):
    if not 0 < keep < n_slots < k_sys.shape[2]:
        raise ValueError("mixed prefix requires 0 < exact rows < slots < teacher rows")
    k, v = init_from_teacher(k_sys[:, :, keep:], v_sys[:, :, keep:], n_slots-keep, seed)
    return torch.cat([k_sys[:, :, :keep], k], dim=2), torch.cat([v_sys[:, :, :keep], v], dim=2)


def default_scale(head_dim):
    """Qwen-family attention scale: ``head_dim ** -0.5``.

    The capture stores post-RoPE queries and keys whose dot products must be
    scaled exactly as the deployed model scales them. A hardcoded ``1/16`` only
    happens to be correct for ``head_dim == 256``; Qwen3-4B has ``head_dim ==
    128``, so the correct scale is ``1/sqrt(128) ~= 0.08839``. Training under the
    wrong scale optimises a different attention distribution than the one the
    cache is installed into, so the reported loss does not predict deployment.
    """
    return float(head_dim) ** -0.5


class BatchedCausalTorchLoss:
    def __init__(self, k_sys, v_sys, traj, n_slots, scale=None,
                 cosine_weight=1.0, gate_weight=False, device="cuda", chunk=0,
                 o_proj=None, clean_by_item=None):
        """``o_proj``: optional (Hq*D, hidden) fp32 tensor. When given, the loss
        is computed in the *output-projected* space: the gated attention output
        is mapped through the frozen output projection before comparison, so the
        objective penalises the error that actually enters the residual stream
        rather than the raw per-head attention output (which o_proj discards).

        ``clean_by_item``: optional ``{item_id: clean_traj_entry}``. When given
        the loss runs in *paired* mode: ``traj`` supplies the deployed model's
        own (student) inputs - queries, gate, live K/V - while the clean entry
        supplies the **target** for the same query rows. Both captures tokenize
        the same stream at the same logical positions, so the rows align.

        Paired mode therefore asks: "given the queries the compiled model really
        produces, reproduce the attention the ORIGINAL prompt would have
        produced." That is the point of the exercise: a mismatch here is exactly
        the query drift that clean-input training cannot see.
        """
        dev = torch.device(device)
        self.cosine_weight = cosine_weight
        self.gate_weight = gate_weight
        self.o_proj = o_proj.to(dev).float() if o_proj is not None else None
        self.clean_by_item = clean_by_item
        self.n_syn = int(n_slots)
        self.NT = len(traj)
        self.Hkv = traj[0]["k_live"].shape[1]
        self.Hq = traj[0]["q_rot"].shape[1]
        self.D = traj[0]["q_rot"].shape[3]
        # Default to the deployed model's own attention scale so training and
        # installation agree; callers may still override explicitly.
        self.scale = default_scale(self.D) if scale is None else scale
        self.Lq = max(t["q_rot"].shape[2] for t in traj)
        self.Lk = max(t["k_live"].shape[2] for t in traj)
        self.chunk = chunk if chunk and chunk > 0 else self.NT

        Q, KL, VL, TG, G, M = [], [], [], [], [], []
        okq = np.zeros((self.NT, self.Lq), np.float32)
        okl = np.zeros((self.NT, self.Lk), np.float32)
        for i, tr in enumerate(traj):
            # Inputs: always from this shard. In paired mode these are the
            # compiled model's own queries/gate/live-KV (the "dirty input").
            q = torch.from_numpy(tr["q_rot"].astype(np.float32))
            kl = torch.from_numpy(tr["k_live"].astype(np.float32))
            vl = torch.from_numpy(tr["v_live"].astype(np.float32))
            qlog = np.asarray(tr["q_logical"], np.int64)
            klog = np.asarray(tr["k_logical"], np.int64)
            lq, lk = q.shape[2], kl.shape[2]
            cm_s = _causal_mask(qlog, klog, self.n_syn, dev)       # student prefix

            if self.clean_by_item is not None:
                # Paired target: the CLEAN capture's queries attending to the
                # ORIGINAL prompt K/V. Query/key rows align because both captures
                # tokenize the same stream at the same logical positions.
                cl = self.clean_by_item[tr["item"]]
                cq = torch.from_numpy(cl["q_rot"].astype(np.float32))
                ckl = torch.from_numpy(cl["k_live"].astype(np.float32))
                cvl = torch.from_numpy(cl["v_live"].astype(np.float32))
                cqlog = np.asarray(cl["q_logical"], np.int64)
                cklog = np.asarray(cl["k_logical"], np.int64)
                if cq.shape[2] != lq or ckl.shape[2] != lk:
                    raise SystemExit(
                        f"paired item {tr['item']}: clean/paired row counts differ "
                        f"({cq.shape[2]} vs {lq} queries, {ckl.shape[2]} vs {lk} keys)")
                cm_t = _causal_mask(cqlog, cklog, k_sys.shape[2], dev)
                add_t = ((1.0 - cm_t) * -1e9)[None, None, :, :]
                with torch.no_grad():
                    tgt = sdpa(cq.to(dev), torch.cat([k_sys, ckl.to(dev)], dim=2),
                               torch.cat([v_sys, cvl.to(dev)], dim=2), scale,
                               mask=add_t).cpu()
            else:
                cm_t = _causal_mask(qlog, klog, k_sys.shape[2], dev)   # teacher prefix
                add_t = ((1.0 - cm_t) * -1e9)[None, None, :, :]
                with torch.no_grad():
                    tgt = sdpa(q.to(dev), torch.cat([k_sys, kl.to(dev)], dim=2),
                               torch.cat([v_sys, vl.to(dev)], dim=2), scale, mask=add_t).cpu()
            Q.append(F.pad(q, (0, 0, 0, self.Lq - lq)))
            KL.append(F.pad(kl, (0, 0, 0, self.Lk - lk)))
            VL.append(F.pad(vl, (0, 0, 0, self.Lk - lk)))
            TG.append(F.pad(tgt, (0, 0, 0, self.Lq - tgt.shape[2])))
            if gate_weight:
                g = torch.from_numpy(tr["gate"].astype(np.float32))
                G.append(F.pad(g, (0, 0, 0, self.Lq - g.shape[1])))
            okq[i, :lq] = 1.0
            okl[i, :lk] = 1.0
            # Build a per-trajectory mask over [syn(n_syn) | live(lk)] and pad
            # BOTH the query axis (to Lq) and the live axis (to Lk) so M_cpu is
            # rectangular. Padded live columns are masked (not visible) and the
            # padded key tensors are zero; padded query rows use an all-visible
            # dummy mask (their loss weight is zero).
            full = torch.cat([cm_s, torch.ones(self.Lq - lq, self.n_syn + lk, device=dev)],
                             dim=0)  # (Lq, n_syn+lk); padded rows all-visible
            if lk < self.Lk:
                pad_cols = torch.zeros(self.Lq, self.Lk - lk, device=dev)
                full = torch.cat([full, pad_cols], dim=1)
            M.append(full.cpu())

        self.Q_cpu = torch.cat(Q, 0)
        self.KL_cpu = torch.cat(KL, 0)
        self.VL_cpu = torch.cat(VL, 0)
        self.T_cpu = torch.cat(TG, 0)
        self.G_cpu = torch.cat(G, 0) if gate_weight else None
        self.M_cpu = torch.stack(M, 0)  # (NT, Lq, n_syn+Lk)
        self.okq_cpu = torch.from_numpy(okq)
        self.okl_cpu = torch.from_numpy(okl)
        self.dev = dev
        self.wq_cpu = torch.from_numpy((okq / okq.sum(1)[:, None]).astype(np.float32))

        # E5 energy-scaling scalar (ungated control recovery: all-ones gate ->
        # S == 1 -> c_layer == 1 -> gated loss == ungated loss).
        self.c_layer = 1.0
        self.teacher_raw_energy = 0.0
        self.teacher_gated_energy = 0.0
        if gate_weight:
            T = self.T_cpu.to(dev)
            G = self.G_cpu.to(dev)
            S = torch.sigmoid(G).reshape(self.NT, self.Lq, self.Hq, self.D).permute(0, 2, 1, 3)
            T_gated = T * S

            if self.o_proj is not None:
                # Energy must be measured in the SAME (projected) space as the
                # loss, otherwise c_layer under-scales the projected MSE because
                # the projection changes the magnitude.
                W = self.o_proj
                def _proj(x):
                    return (x.permute(0, 2, 1, 3).reshape(self.NT, self.Lq, self.Hq * self.D) @ W)
                wq = self.wq_cpu.to(dev)                       # (NT, Lq)

                def _wq_mean(x):
                    return float(((x ** 2).mean(dim=-1) * wq).sum() / self.NT)

                self.teacher_raw_energy = _wq_mean(_proj(T))
                self.teacher_gated_energy = _wq_mean(_proj(T_gated))
            else:
                wq = self.wq_cpu.to(dev)[:, None, :, None]

                def _wq_mean(x):
                    return float(((x ** 2).mean(dim=(1, 3), keepdim=True) * wq).sum() / self.NT)

                self.teacher_raw_energy = _wq_mean(T)
                self.teacher_gated_energy = _wq_mean(T_gated)
            self.c_layer = self.teacher_raw_energy / max(self.teacher_gated_energy, 1e-8)
            del T, G, S, T_gated

    def _chunk_tensors(self, lo, hi):
        dev = self.dev
        cm = self.M_cpu[lo:hi].to(dev)
        add = ((1.0 - cm) * -1e9)[:, None, :, :]
        out = {"Q": self.Q_cpu[lo:hi].to(dev), "KL": self.KL_cpu[lo:hi].to(dev),
               "VL": self.VL_cpu[lo:hi].to(dev), "T": self.T_cpu[lo:hi].to(dev),
               "add": add, "wq": self.wq_cpu[lo:hi].to(dev),
               "n": hi - lo}
        if self.gate_weight:
            out["G"] = self.G_cpu[lo:hi].to(dev)
        return out

    def loss_fn(self, k, v):
        total_mse = 0.0
        total_cos = 0.0
        for lo in range(0, self.NT, self.chunk):
            hi = min(lo + self.chunk, self.NT)
            mse_c, cos_c = self._chunk_terms(lo, hi, k, v)
            total_mse = total_mse + mse_c
            total_cos = total_cos + cos_c
        mse = self.c_layer * total_mse / self.NT
        if self.cosine_weight <= 0:
            return mse
        return mse + self.cosine_weight * (1.0 - total_cos / self.NT)

    def chunk_losses(self, k, v):
        """Yield (index, partial_loss) so callers can backward each chunk and
        free its graph, holding peak activation memory to a single chunk.

        The cosine constant (``cosine_weight * 1.0``) is *not* included in any
        chunk; the driver adds it once to the running total. Summing the yielded
        partials plus that single constant reproduces ``loss_fn`` exactly.
        """
        for lo in range(0, self.NT, self.chunk):
            hi = min(lo + self.chunk, self.NT)
            mse_c, cos_c = self._chunk_terms(lo, hi, k, v)
            part = self.c_layer * mse_c / self.NT
            if self.cosine_weight > 0:
                part = part - self.cosine_weight * cos_c / self.NT
            yield (lo, hi), part

    def _chunk_terms(self, lo, hi, k, v):
        c = self._chunk_tensors(lo, hi)
        n = c["n"]
        Kb = torch.cat([k.expand(n, self.Hkv, self.n_syn, self.D), c["KL"]], dim=2)
        Vb = torch.cat([v.expand(n, self.Hkv, self.n_syn, self.D), c["VL"]], dim=2)
        out = F.scaled_dot_product_attention(c["Q"], Kb, Vb, scale=self.scale,
                                             attn_mask=c["add"], enable_gqa=True)
        tgt = c["T"]
        if self.gate_weight:
            s = torch.sigmoid(c["G"]).reshape(n, self.Lq, self.Hq, self.D).permute(0, 2, 1, 3)
            out = out * s
            tgt = tgt * s

        if self.o_proj is not None:
            # Map the gated per-head output into the residual-stream
            # contribution: (n, Hq, Lq, D) -> (n, Lq, Hq*D) -> @ W -> (n, Lq, hidden).
            W = self.o_proj
            ho = out.permute(0, 2, 1, 3).reshape(n, self.Lq, self.Hq * self.D)
            ht = tgt.permute(0, 2, 1, 3).reshape(n, self.Lq, self.Hq * self.D)
            out = ho @ W
            tgt = ht @ W
            diff = (out - tgt) ** 2
            per_q = diff.mean(dim=-1)                      # (n, Lq)
            mse_c = (per_q * c["wq"]).sum()                # wq is (n, Lq)
        else:
            diff = (out - tgt) ** 2
            per_q = diff.mean(dim=(1, 3))
            mse_c = (per_q * c["wq"]).sum()
        cos_c = 0.0
        if self.cosine_weight > 0:
            if self.o_proj is not None:
                # (n, Lq, hidden): one cosine per query over the projected vector.
                # Each *trajectory* gets weight 1/NT, exactly like the MSE term;
                # the query rows inside a trajectory are averaged by the same
                # wq distribution used for the MSE. Summing the raw row cosines
                # instead lets a long question dominate the cosine term.
                valid = ((c["wq"] > 0).float() * c["wq"]).clamp(min=0.0)
                a = out / (out.norm(dim=-1, keepdim=True) + 1e-8)
                b = tgt / (tgt.norm(dim=-1, keepdim=True) + 1e-8)
                rowcos = (a * b).sum(-1)                       # (n, Lq)
                cos_c = (rowcos * valid).sum()
            else:
                valid = (c["wq"] > 0)[:, None, :, None]
                a = torch.where(valid, out, torch.zeros_like(out) + 1.0)
                b = torch.where(valid, tgt, torch.zeros_like(tgt) + 1.0)
                a = a / (a.norm(dim=-1, keepdim=True) + 1e-8)
                b = b / (b.norm(dim=-1, keepdim=True) + 1e-8)
                rowcos = (a * b).sum(-1).reshape(n, -1)
                rmask = valid[:, 0, :, 0].unsqueeze(1).expand(n, self.Hq, self.Lq).reshape(n, -1)
                rmask = rmask.float()
                denom = rmask.sum(-1) + 1e-8
                cos_c = ((rowcos * rmask).sum(-1) / denom).sum()
        del c, Kb, Vb, out, tgt
        return mse_c, cos_c


def sample_indices(rng, size, count, plan=None):
    if plan is None:
        return sorted(rng.choice(size, size=count, replace=False))
    groups = plan['groups']
    pools = [g['indices'] for g in groups]
    assert sum(g['count'] for g in groups) == count
    assert sorted(i for pool in pools for i in pool) == list(range(size))
    assert all(0 < g['count'] <= len(g['indices']) for g in groups)
    return sorted(int(i) for g in groups for i in rng.choice(g['indices'], size=g['count'], replace=False))


def optimize_layer(shard_path, n_slots, steps, lr, cosine_weight, seed, log_every,
                   device, batched=False, chunk=0, gate_weight=False,
                   freeze_sink=False, examples_per_update=0, o_proj=None,
                   lr_sched="none", lr_floor_frac=0.1, warmup_frac=0.05,
                   full_eval=False, clean_shard_path=None, init_from=None,
                     scale=None, keep_prefix_tokens=0, sampling_plan=None):
    with open(shard_path, "rb") as f:
        sh = pickle.load(f)
    if sh.get("schema") not in (None, "v2-causal-occupied"):
        raise SystemExit(f"{shard_path}: schema {sh.get('schema')!r} is not v2")
    traj = sh["traj"]

    # Paired mode: inputs from this shard, targets from the clean shard.
    # k_sys/v_sys (the ORIGINAL prompt K/V) are needed to reconstruct the clean
    # target, so they come from the clean shard; the paired shard deliberately
    # does not carry them.
    clean_by_item = None
    if clean_shard_path is not None:
        with open(clean_shard_path, "rb") as f:
            csh = pickle.load(f)
        if csh.get("schema") not in (None, "v2-causal-occupied"):
            raise SystemExit(f"{clean_shard_path}: schema {csh.get('schema')!r} is not v2")
        k_sys = torch.from_numpy(csh["k_sys"].astype(np.float32)).to(device)
        v_sys = torch.from_numpy(csh["v_sys"].astype(np.float32)).to(device)
        clean_by_item = {t["item"]: t for t in csh["traj"]}
        want = {t["item"] for t in traj}
        missing = sorted(want - set(clean_by_item))
        if missing:
            raise SystemExit(f"clean shard is missing paired items {missing}")
    else:
        k_sys = torch.from_numpy(sh["k_sys"].astype(np.float32)).to(device)
        v_sys = torch.from_numpy(sh["v_sys"].astype(np.float32)).to(device)
    if init_from is not None:
        # Warm start: continue from an existing compiled cache. Needed so a
        # refinement arm and its matched control differ ONLY in the objective,
        # not in the initialisation.
        from safetensors.torch import load_file
        d = load_file(init_from)
        k0 = d["k"].to(device).float()
        v0 = d["v"].to(device).float()
        if k0.shape[2] != n_slots:
            raise SystemExit(
                f"--init-from {init_from}: has {k0.shape[2]} slots but --slots={n_slots}")
    elif keep_prefix_tokens:
        k0, v0 = init_mixed_prefix(k_sys, v_sys, n_slots, seed, keep_prefix_tokens)
    else:
        k0, v0 = init_from_teacher(k_sys, v_sys, n_slots, seed, freeze_sink=freeze_sink)
    if keep_prefix_tokens:
        if not 0 < keep_prefix_tokens < n_slots < k_sys.shape[2]:
            raise ValueError("invalid mixed prefix budget")
        torch.testing.assert_close(k0[:, :, :keep_prefix_tokens], k_sys[:, :, :keep_prefix_tokens], rtol=0, atol=0)
        torch.testing.assert_close(v0[:, :, :keep_prefix_tokens], v_sys[:, :, :keep_prefix_tokens], rtol=0, atol=0)
    k = k0.clone().requires_grad_(True)
    v = v0.clone().requires_grad_(True)
    opt = MLXAdam([k, v], lr=lr)
    rng = np.random.default_rng(seed + 1)

    frozen_rows = keep_prefix_tokens or int(freeze_sink)
    if frozen_rows:
        # Zero the gradient at slot 0 so Adam keeps it bit-identical to init.
        def _zero_sink_k(g):
            g = g.clone()
            g[:, :, :frozen_rows, :] = 0
            return g

        def _zero_sink_v(g):
            g = g.clone()
            g[:, :, :frozen_rows, :] = 0
            return g

        k.register_hook(_zero_sink_k)
        v.register_hook(_zero_sink_v)
        # MLXAdam keeps its own m/v buffers; zero those at slot 0 too so no
        # momentum leaks into the frozen slot on later steps.
        for buf in (opt.m[0], opt.v[0]):
            buf[:, :, :frozen_rows, :] = 0
        for buf in (opt.m[1], opt.v[1]):
            buf[:, :, :frozen_rows, :] = 0

    def _backward_step(bl, cosine_weight):
        """One optimizer step with chunked (memory-bounded) or full backward."""
        opt.zero_grad(set_to_none=True)
        chunked = chunk and chunk < bl.NT
        if chunked:
            tot = cosine_weight if cosine_weight > 0 else 0.0
            for _rng, part in bl.chunk_losses(k, v):
                part.backward()
                tot += float(part.detach())
                del part
            loss_val = tot
        else:
            loss = bl.loss_fn(k, v)
            loss.backward()
            loss_val = float(loss.detach())
        opt.step()
        return loss_val

    if batched and examples_per_update and examples_per_update < len(traj):
        hist = []
        # Optional full-set evaluator: minibatch loss is noisy across different
        # 24/71 samples, so it cannot show a plateau. When enabled this computes
        # the exact loss over ALL trajectories under no_grad at checkpoints (a
        # deterministic curve), at ~2x wall-clock cost - so it is OPT-IN and off
        # for production runs.
        _eval_full = None
        if full_eval and log_every:
            def _eval_full():
                blf = BatchedCausalTorchLoss(
                    k_sys, v_sys, traj, n_slots, scale=scale, cosine_weight=cosine_weight,
                    gate_weight=gate_weight, device=device, chunk=chunk, o_proj=o_proj,
                    clean_by_item=clean_by_item)
                with torch.no_grad():
                    return float(blf.loss_fn(k, v).detach())
        for step in range(steps):
            if lr_sched != "none":
                opt.lr = lr_schedule(step, steps, lr, lr_sched, lr_floor_frac, warmup_frac)
            idx = sample_indices(rng, len(traj), examples_per_update, sampling_plan)
            sub = [traj[i] for i in idx]
            bl = BatchedCausalTorchLoss(k_sys, v_sys, sub, n_slots, scale=scale,
                                        cosine_weight=cosine_weight,
                                        gate_weight=gate_weight, device=device, chunk=chunk, o_proj=o_proj,
                                        clean_by_item=clean_by_item)
            loss_val = _backward_step(bl, cosine_weight)
            hist.append(loss_val)
            if log_every and (step % log_every == 0 or step == steps - 1):
                if _eval_full:
                    fl = _eval_full()
                    print(f"      step {step:4d}  loss={hist[-1]:.6e}  full={fl:.6e}  "
                          f"lr={opt.lr:.3e}  (mb={len(sub)})", flush=True)
                else:
                    print(f"      step {step:4d}  loss={hist[-1]:.6e}  lr={opt.lr:.3e}  "
                          f"(mb={len(sub)})", flush=True)
        return k.detach(), v.detach(), hist

    if batched:
        bl = BatchedCausalTorchLoss(k_sys, v_sys, traj, n_slots, scale=scale,
                                    cosine_weight=cosine_weight,
                                    gate_weight=gate_weight, device=device, chunk=chunk, o_proj=o_proj,
                                    clean_by_item=clean_by_item)
        forward_loss = lambda: bl.loss_fn(k, v)
    else:
        if clean_by_item is not None:
            raise SystemExit("--paired-traj requires --batched (non-batched path is ungated)")
        # Match the deployed model's attention scale (derived from head_dim).
        nb_scale = default_scale(traj[0]["q_rot"].shape[3])
        batch = []
        for tr in traj:
            q = torch.from_numpy(tr["q_rot"].astype(np.float32)).to(device)
            kl = torch.from_numpy(tr["k_live"].astype(np.float32)).to(device)
            vl = torch.from_numpy(tr["v_live"].astype(np.float32)).to(device)
            qlog = np.asarray(tr["q_logical"], np.int64)
            klog = np.asarray(tr["k_logical"], np.int64)
            cm_s = _causal_mask(qlog, klog, n_slots, device)
            cm_t = _causal_mask(qlog, klog, k_sys.shape[2], device)
            add_s = ((1.0 - cm_s) * -1e9)[None, None, :, :]
            add_t = ((1.0 - cm_t) * -1e9)[None, None, :, :]
            batch.append((q, kl, vl, add_s, add_t))

        # NOTE: the non-batched reference loop implements the ungated objective
        # only. Gate-aware training (E5) must use --batched (production path),
        # which carries the c_layer scaling and the all-ones-gate invariant.
        def forward_loss():
            total = 0.0
            for q, kl, vl, add_s, add_t in batch:
                out = sdpa(q, torch.cat([k, kl], dim=2), torch.cat([v, vl], dim=2),
                           nb_scale, mask=add_s)
                tgt = sdpa(q, torch.cat([k_sys, kl], dim=2), torch.cat([v_sys, vl], dim=2),
                           nb_scale, mask=add_t)
                total = total + F.mse_loss(out, tgt)
                if cosine_weight > 0:
                    a = out.reshape(-1, out.shape[-1]); b = tgt.reshape(-1, tgt.shape[-1])
                    a = a / (a.norm(dim=-1, keepdim=True) + 1e-8)
                    b = b / (b.norm(dim=-1, keepdim=True) + 1e-8)
                    total = total + cosine_weight * (1.0 - (a * b).sum(-1).mean())
            return total / len(batch)

    hist = []
    for step in range(steps):
        if batched:
            loss_val = _backward_step(bl, cosine_weight)
        else:
            opt.zero_grad(set_to_none=True)
            loss = forward_loss()
            loss.backward()
            opt.step()
            loss_val = float(loss.detach())
        hist.append(loss_val)
        if log_every and (step % log_every == 0 or step == steps - 1):
            print(f"      step {step:4d}  loss={hist[-1]:.6e}", flush=True)
    return k.detach(), v.detach(), hist


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--resume", action="store_true", help="reuse verified completed layers with the same recipe")
    ap.add_argument("--slots", type=int, default=512)
    ap.add_argument("--ratio", default=None)
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--cosine-weight", type=float, default=1.0)
    ap.add_argument("--scale", type=float, default=None,
                    help="attention scale for the training loss. Default derives it from "
                         "the trajectory head_dim (head_dim**-0.5), matching the deployed "
                         "model. An explicit value reproduces legacy behaviour.")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--layers", default="all")
    ap.add_argument("--log-every", type=int, default=100)
    ap.add_argument("--device", default=None)
    ap.add_argument("--batched", action="store_true")
    ap.add_argument("--batch-chunk", type=int, default=0)
    ap.add_argument("--gate-weight", action="store_true")
    ap.add_argument("--freeze-sink", action="store_true")
    ap.add_argument("--keep-prefix-tokens", type=int, default=0,
                    help="keep this many leading teacher KV rows exact; remaining slots compress the tail")
    ap.add_argument("--examples-per-update", type=int, default=0)
    ap.add_argument("--sampling-plan", default=None, help="JSON disjoint index pools and per-update quotas")
    ap.add_argument("--kv-dtype", default="bfloat16")
    ap.add_argument("--oproj-dir", default=None,
                    help="directory of oproj_L<layer>.pt files (frozen output-projection "
                         "weights). When set, the loss is computed in output-projected space "
                         "and implies --gate-weight semantics.")
    ap.add_argument("--lr-deep", type=float, default=None,
                    help="lr for layers at/after --deep-from (per-layer adaptive lr). The "
                         "LR sweep showed deep layers are lr-limited under a single static lr.")
    ap.add_argument("--deep-from", type=int, default=0,
                    help="layer index at/after which --lr-deep applies (default 0 = all).")
    ap.add_argument("--lr-sched", default="none", choices=["none", "cosine", "linear"],
                    help="per-step lr schedule (default none = static).")
    ap.add_argument("--lr-floor-frac", type=float, default=0.1,
                    help="decay floor as a fraction of the base lr (default 0.1).")
    ap.add_argument("--warmup-frac", type=float, default=0.05,
                    help="fraction of steps used for linear warmup (default 0.05).")
    ap.add_argument("--full-eval", action="store_true",
                    help="also log the deterministic full-set loss at checkpoints (~2x wall "
                         "clock). Use only for convergence/plateau analysis, not production.")
    ap.add_argument("--clean-traj", default=None,
                    help="paired mode: directory of CLEAN trajectory shards. Inputs are read "
                         "from --traj (the model's own, 'dirty' queries/gate/live-KV) while "
                         "the target is reconstructed from the clean capture's queries "
                         "attending to the ORIGINAL prompt K/V. Requires --batched.")
    ap.add_argument("--init-from-dir", default=None,
                    help="warm start from an existing compiled dir (layer_NNN.safetensors). "
                         "A refinement arm and its matched control must share this so they "
                         "differ only in the objective.")
    args = ap.parse_args()
    sampling_plan = json.loads(Path(args.sampling_plan).read_text()) if args.sampling_plan else None
    if sampling_plan is not None and not (args.batched and args.examples_per_update):
        raise ValueError('sampling plan requires batched minibatch updates')
    P = lambda *a, **k: print(*a, **k, flush=True)

    _dt = {"bfloat16": torch.bfloat16, "bf16": torch.bfloat16,
           "float16": torch.float16, "fp16": torch.float16,
           "float32": torch.float32, "fp32": torch.float32}
    if args.kv_dtype.lower() not in _dt:
        raise SystemExit(f"unknown --kv-dtype {args.kv_dtype!r}")
    kv_dtype = _dt[args.kv_dtype.lower()]
    P(f"kv-dtype: {kv_dtype}")

    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    P(f"device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device == "cuda" else ""))

    with open(os.path.join(args.traj, "meta.json")) as f:
        meta = json.load(f)["meta"]
    layers = meta["layers"] if args.layers == "all" else [int(x) for x in args.layers.split(",")]
    ratio = None
    if args.ratio is not None:
        ratio = eval(args.ratio) if isinstance(args.ratio, str) else args.ratio
        args.slots = max(1, round(int(meta["n_sys"]) * ratio))
        P(f"ratio {ratio} of n_sys={meta['n_sys']} -> slots={args.slots}")
    os.makedirs(args.out, exist_ok=True)
    # Resolve the effective attention scale up front so it is logged and
    # recorded even when it is derived from the trajectory head_dim.
    with open(os.path.join(args.traj, f"layer_{layers[0]:03d}.pkl"), "rb") as f:
        _d0 = pickle.load(f)
    eff_head_dim = int(_d0["traj"][0]["q_rot"].shape[3])
    eff_scale = default_scale(eff_head_dim) if args.scale is None else float(args.scale)
    del _d0
    P(f"layers: {len(layers)}  slots={args.slots}  steps={args.steps}  lr={args.lr}  "
      f"gate={args.gate_weight} sink={args.freeze_sink} mbsz={args.examples_per_update}")
    P(f"attention scale: {eff_scale:.6f} (head_dim={eff_head_dim}, "
      f"{'derived' if args.scale is None else 'explicit --scale'})")

    from safetensors.torch import save_file

    manifest = {"schema": "v2-causal-occupied", "slots": args.slots, "steps": args.steps,
                "lr": args.lr, "ratio": ratio, "cosine_weight": args.cosine_weight,
                "attention_scale": eff_scale, "head_dim": eff_head_dim,
                "traj": args.traj, "device": device, "kv_dtype": str(kv_dtype),
                "gate_weight": args.gate_weight, "freeze_sink": args.freeze_sink,
                "keep_prefix_tokens": args.keep_prefix_tokens,
                "oproj_dir": args.oproj_dir, "clean_traj": args.clean_traj,
                "init_from_dir": args.init_from_dir,
                "lr_sched": args.lr_sched,
                "lr_deep": args.lr_deep, "deep_from": args.deep_from,
                 "examples_per_update": args.examples_per_update, "seed": args.seed,
                 "batch_chunk": args.batch_chunk, "batched": args.batched,
                 "lr_floor_frac": args.lr_floor_frac, "warmup_frac": args.warmup_frac,
                 "full_eval": args.full_eval, "requested_layers": layers, "layers": []}
    manifest_path = Path(args.out) / "manifest.json"
    if sampling_plan is not None:
        manifest['sampling_plan'] = sampling_plan
    if args.resume and manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if any(previous.get(key) != value for key, value in manifest.items()
               if key not in ("layers", "complete", "elapsed_s")):
            raise SystemExit("resume configuration differs from checkpoint")
        from safetensors.torch import load_file
        for entry in previous["layers"]:
            tensors = load_file(str(Path(args.out) / entry["path"]))
            if any(tensors[key].shape[2] != args.slots or not torch.isfinite(tensors[key]).all()
                   for key in ("k", "v")):
                raise SystemExit(f"invalid completed layer {entry['layer']}")
        manifest["layers"] = previous["layers"]

    elapsed_before = previous.get("elapsed_s", 0) if args.resume and manifest_path.exists() else 0
    completed_before = len(manifest["layers"])

    def checkpoint(complete=False):
        manifest["complete"] = complete
        manifest["elapsed_s"] = elapsed_before + time.time() - t_all
        temporary = manifest_path.with_suffix(".json.partial")
        temporary.write_text(json.dumps(manifest, indent=2))
        temporary.replace(manifest_path)

    t_all = time.time()
    for n, L in enumerate(layers):
        if any(entry["layer"] == L for entry in manifest["layers"]):
            P(f"  layer {L}: verified checkpoint, skip")
            continue
        o_proj = None
        if args.oproj_dir:
            op_path = os.path.join(args.oproj_dir, f"oproj_L{L}.pt")
            if not os.path.exists(op_path):
                raise SystemExit(f"missing projected weight {op_path}")
            o_proj = torch.load(op_path, map_location="cpu")["weight"]
        shard = os.path.join(args.traj, f"layer_{L:03d}.pkl")
        if not os.path.exists(shard):
            P(f"  layer {L}: no shard, skip")
            continue
        t0 = time.time()
        lr_L = args.lr
        if args.lr_deep is not None and L >= args.deep_from:
            lr_L = args.lr_deep
        P(f"  [{n+1:2d}/{len(layers)}] layer {L:2d}  lr={lr_L:g}")
        clean_shard = (os.path.join(args.clean_traj, f"layer_{L:03d}.pkl")
                       if args.clean_traj else None)
        if clean_shard is not None and not os.path.exists(clean_shard):
            raise SystemExit(f"missing clean shard {clean_shard}")
        init_from = None
        if args.init_from_dir:
            init_from = os.path.join(args.init_from_dir, f"layer_{L:03d}.safetensors")
            if not os.path.exists(init_from):
                raise SystemExit(f"missing warm-start file {init_from}")
        k, v, hist = optimize_layer(shard, args.slots, args.steps, lr_L,
                                    args.cosine_weight, args.seed, args.log_every,
                                    device, batched=args.batched, chunk=args.batch_chunk,
                                    gate_weight=args.gate_weight, freeze_sink=args.freeze_sink,
                                    examples_per_update=args.examples_per_update, o_proj=o_proj,
                                    lr_sched=args.lr_sched, lr_floor_frac=args.lr_floor_frac,
                                    warmup_frac=args.warmup_frac, full_eval=args.full_eval,
                                    clean_shard_path=clean_shard, init_from=init_from,
                                    scale=args.scale, keep_prefix_tokens=args.keep_prefix_tokens,
                                    sampling_plan=sampling_plan)
        path = os.path.join(args.out, f"layer_{L:03d}.safetensors")
        exported = {"k": k.to(kv_dtype).cpu().contiguous(),
                    "v": v.to(kv_dtype).cpu().contiguous()}
        if args.keep_prefix_tokens:
            with open(shard, "rb") as f:
                teacher = pickle.load(f)
            for name in ("k", "v"):
                exported[name] = exported[name].half()
                source = torch.from_numpy(teacher[f"{name}_sys"][:, :, :args.keep_prefix_tokens])
                exact = source.half()
                fitted = k if name == "k" else v
                assert torch.equal(fitted[:, :, :args.keep_prefix_tokens].cpu(), source.float())
                exported[name][:, :, :args.keep_prefix_tokens].copy_(exact)
                assert torch.equal(exported[name][:, :, :args.keep_prefix_tokens], exact)
            del teacher
        save_file(exported, path + ".partial")
        os.replace(path + ".partial", path)
        manifest["layers"].append({"layer": L, "slots": args.slots,
                                   "init_loss": hist[0], "final_loss": hist[-1],
                                   "path": os.path.basename(path)})
        P(f"     L{L:2d}: {hist[0]:.3e} -> {hist[-1]:.3e} ({time.time()-t0:.0f}s)")
        checkpoint()
        completed = len(manifest["layers"])
        elapsed = time.time() - t_all
        rate = (completed - completed_before) / max(elapsed, 0.001)
        P(f"{datetime.now(timezone.utc).isoformat()} elapsed={elapsed:.1f}s "
          f"completed={completed}/{len(layers)} rate={rate:.4f}layers/s "
          f"ETA={(len(layers)-completed)/rate:.1f}s")
        del k, v, hist, exported
        if device == "cuda":
            torch.cuda.empty_cache()

    checkpoint(complete=len(manifest["layers"]) == len(layers))
    P(f"manifest -> {os.path.join(args.out, 'manifest.json')}")
    P(f"total_duration={time.time()-t_all:.1f}s artifact={args.out}")


if __name__ == "__main__":
    main()
