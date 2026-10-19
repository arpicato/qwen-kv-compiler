# External benchmark — environment + progress checkpoint (2026-10-12)

## Status: infrastructure GREEN, Stage A PASSED, Stage B in progress

### Completed
- **Archival (verified):** 27B EXL model + all agent artifacts copied to
  `/home/arpin/archives/kvcompile-xtx-2026-10-12/` over the direct-LAN tailnet
  path. `rsync --dry-run --checksum` returned clean for both. Sources removed
  from XTX to reclaim space.
- **XTX space:** root ~13 GiB free; `/mnt/sandisk` ~9 GiB free.
  Ventoy ISOs, config backup, ComfyUI, ROCm env all preserved.
- **Bench env (`/home/arpin/kvbench/env`, Python 3.12.15):**
  - torch **2.8.0+rocm6.4** (GPU detected, gfx1100), torchvision 0.23.0
  - transformers 4.57.1, accelerate 1.12.0, datasets 4.4.1 (the Compaction pins)
  - Installed via `uv` with explicit ROCm wheel URLs (`--no-deps` for torch).
  - **ROCm quirk:** set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`; also
    monkeypatch `transformers.modeling_utils.caching_allocator_warmup` to a
    no-op (its single 7.5 GiB alloc fails on this build).
- **Repos cloned at pinned commits:**
  - `/home/arpin/kvbench/compaction` @ `2020f6d37940fe013e7e7f1ebf409e5d107c5670`
  - `/home/arpin/kvbench/cartridges` @ `ef34ba97a06049c34820506e2c283746284ae5f0`
  - Compaction imports OK (`compaction`, `compaction.algorithms.omp`,
    `evaluation.datasets`).
- **Model:** `/mnt/sandisk/kvbench/models/Qwen3-4B` (original, 7.6 GiB, BF16).
  Smoke: 36 layers, 32 q-heads, 8 kv-heads, head_dim 128, max_pos 40960.
- **QuALITY data:** bundled at `compaction/data/QuALITY.v1.0.1.htmlstripped.dev`.
  115 unique articles / 2086 questions. **First 20 = 357 q; first 50 = 894 q**
  (matches the paper exactly).
- **Stage A correctness PASSED** via `stage_a_harness.py`:
  - article 0, 14 questions, full context, greedy, max_new_tokens 512
  - **accuracy 10/14 = 0.714, parse rate 1.000, peak 9.0 GiB, 180 s**
  - consistent with the published Qwen3-4B QuALITY full-context 71.1%.
  - result JSON: `/home/arpin/kvbench/results/stageA_art0.json`

### Known blocker (documented deviation)
Compaction's own evaluator (`evaluation/run_qa_evaluation.py`) **OOMs on ROCm**:
- it needs vLLM for text-based methods; we substituted an HF shim
  (`compaction/rocm_vllm_shim.py` + `compaction/run_qa_rocm.py`), which got the
  pipeline running further.
- 0-dim CUDA scalar ops (`torch.isin`, `(t<0).any()`) raise
  "no kernel image" → patched in the shim.
- the custom `models/qwen3` forward materialises a full float attention mask for
  the `CompactedPrefixCache` beta path, which disables flash/efficient SDPA and
  forces the math fallback (5.3 GiB alloc) → OOM at 6.5k context.
- **Decision:** do NOT fight upstream's mask design. Use the standalone
  harness (`stage_a_harness.py`) as the evaluation driver; feed it a compacted
  cache produced by Compaction's **library API**.

### Stage B plan (next steps)
1. Wire Compaction's library compaction into the harness:
   - `from compaction.compaction_methods import get_compaction_method`
   - `from compaction.query_generation import QueryConfig`
   - build method via `get_compaction_method(name, kwargs)`, call
     `compact_kv_cache(past_key_values, target_size, indices, query_config,
     model, tokenizer, formatted_context, ...)`.
   - returns `((C1, beta, C2), ...)` per layer; install via the model's
     `CompactedPrefixCache` and generate with the harness.
   - AM method names (from `evaluation/configs/algorithms/best.py`):
     `highest_attn_keys_rms_nnls2_-3_3_lsq_on-policy` (= AM-HighestAttnKeys),
     `omp_nnls0_-inf_7_drop-7_lsq_on-policy` (AM-OMP),
     `omp_nnls0_-inf_7_drop-7_lsq_k4int2_on-policy` (AM-OMP-fast).
   - query config: `ss-plus-repeat`; budget: ratio `.02` (and K=2048).
2. Build our compiler's Qwen3 capture + install adapter (uniform synthetic K/V).
3. Run Stage B on articles 0–2 at 2%.

### Key paths on XTX
```
/home/arpin/kvbench/env/bin/python          # bench interpreter
/home/arpin/kvbench/compaction/             # pinned Compaction checkout
/home/arpin/kvbench/cartridges/             # pinned Cartridges checkout
/home/arpin/kvbench/smoke_qwen_c.py         # proven load+generate smoke
/home/arpin/kvbench/compaction/stage_a_harness.py   # working MCQ harness
/home/arpin/kvbench/compaction/rocm_vllm_shim.py    # vLLM->HF shim (partial)
/mnt/sandisk/kvbench/models/Qwen3-4B        # model weights
/home/arpin/kvbench/results/                # run outputs
```
