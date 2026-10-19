# External benchmark — Stage A & B results (2026-10-12)

## Harnesses built and validated on ROCm (Qwen3-4B)

Two independent evaluation paths, both landing near the published full-context
number, which validates the protocol:

| Harness | Path | Article 0 result |
|---|---|---|
| `compaction/stage_a_harness.py` | plain HF model, full context | **10/14 = 0.714**, parse 1.000 |
| `compaction/stage_b_harness.py` | Compaction KV-cache path, `original` | **11/14 = 0.786**, parse 1.000 |

Published Qwen3-4B QuALITY full-context baseline: **71.1%**. Both harnesses
straddle it, so the MCQ protocol (prompt, parsing, scoring) is sound.

## First real comparison — article 0 (14 questions)

| Method | Budget | Compacted tokens | Accuracy | Notes |
|---|---|---:|---:|---|
| Full context | — | 6543 | **0.786** (11/14) | reference |
| **AM-HighestAttnKeys** | **2%** | **129** | **0.571** (8/14) | ~50× compression, 946 s prep |

- AM method: `highest_attn_keys_rms_nnls2_-3_3_lsq_on-policy` (the paper's
  AM-HighestAttnKeys / "fastest"), query config `ss-plus-repeat`,
  released head budget `optimized_agnostic.json`, `--max-ratio-per-head 0.75`.
- peak GPU: 7.8 GiB (AM path), well within 24 GiB.
- The 946 s prep is dominated by self-study query generation (HF path, no vLLM).

Published reference for context: AM-HighestAttnKeys at 2% over 50 articles is
65.0% vs full-context 71.1% (a ~6-point drop). Our single-article 0.786→0.571
is a larger drop, but n=14 and one article — not comparable yet.

## Key ROCm findings (for reuse)

1. `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` required.
2. Monkeypatch `transformers.modeling_utils.caching_allocator_warmup` to a no-op
   (its single ~7.5 GiB allocation fails on this build even with free VRAM).
3. 0-dim CUDA scalar comparisons (`torch.isin`, `(t<0).any()`) raise
   "no kernel image" → route small helpers to CPU.
4. CPU<->GPU model offload/reload breaks subsequent kernel launches → make
   `offload_model_to_cpu`/`reload_model_to_gpu` no-ops.
5. vLLM is unavailable; substitute an HF-backed shim exposing
   `generate(prompts, SamplingParams)` + `sleep()/wake_up()`, bound to the
   already-loaded model (never a second copy).
6. Upstream's own evaluator still OOMs on its materialised float attention mask
   for the `no_context` text path; the standalone harnesses avoid it.

## Artifacts on XTX
```
/home/arpin/kvbench/results/stageA_art0.json           # 10/14 full context
/home/arpin/kvbench/results/am_highest_2pct_art0.json  # 8/14 @ 2%
/home/arpin/kvbench/compaction/stage_a_harness.py
/home/arpin/kvbench/compaction/stage_b_harness.py
/home/arpin/kvbench/compaction/rocm_vllm_shim.py
```

## Next
- Run `original` + AM 2% on articles 1 and 2 (Stage B early comparison, 3 articles).
- Build our compiler's Qwen3 capture + uniform-K install adapter, then evaluate
  the same articles at matched budget (~129 tokens).
- Then K=2048 track and AM-OMP-fast.

## Our compiler on Qwen3 — capture + compile verified (2026-10-12)

`scripts/capture_qwen3_traj.py` monkeypatches `Qwen3Attention.forward` to record
post-RoPE q/k/v and emits the same `v2-causal-occupied` shard schema the existing
compiler consumes. Verified on 2 synthetic contexts:

- 36 layer shards produced; schema checks pass:
  `k_sys (1,8,80,128)`, `q_rot (1,32,9,128)`, `k_live (1,8,29,128)`, gate
  `(1,9,4096)` — Hq=32, Hkv=8, D=128 for Qwen3-4B.
- `scripts/compile_torch_v2.py` consumed it and optimised all 36 layers with the
  loss descending (e.g. L35: 7.35e-3 → 5.64e-4 over 50 steps).
- Qwen3 has **no attention output gate**, so the gate is identity and
  `--oproj-dir` is optional (raw-output loss baseline). The uniform-K synthetic
  cache is written per layer as `layer_NNN.safetensors`.

**Remaining for its evaluation:** an install adapter that injects the compiled
uniform-K cache into the HF model (replacing the article prefix) and generates
via the Stage-B MCQ path. Then run the same 3 articles at matched budget.

