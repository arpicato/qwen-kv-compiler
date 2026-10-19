# External benchmark — status + honest assessment (2026-10-12)

## Implementation/results audit (2026-10-12; supersedes claims below)

**Verdict: AM remains promising; neither method has a confirmed ~6x lead.**
The per-question JSON counts are internally consistent. Our diagnostic cache
scores 10/14 versus AM's 9/14, with two ours-only wins (questions 0, 13) and one
AM-only win (question 6). This is one question net, not evidence of superiority.
No new GPU benchmark was run for this audit, and no algorithm was changed.

### Does our AM run align with the publication?

| Setting | Published AM paper v2, 50 articles / 894 questions | Local diagnostic |
|---|---:|---:|
| Full context | 71.1% | reported 39/51 = 76.5% |
| AM-HighestAttnKeys, 2% retained | 65.0% | verified 33/51 = 64.7% |
| Drop from full context | 6.1 percentage points | reported 11.8 points |
| AM-HighestAttnKeys, 10% / 20% retained | 71.3% / 71.0% | not reproduced |
| AM-HighestAttnKeys, 15.6% retained | no exact published point | 9/14 = 64.3% |

The 2% absolute score agrees closely, but the retention gap is larger locally.
Three articles cannot validate a population-level curve. The 15.6% result is
only one article and does not establish disagreement with the paper either.
Published source: https://arxiv.org/html/2602.16284v2#A6.SS4 (Table 10).

Our harness is NOT the paper protocol: local greedy decoding, thinking disabled,
boxed-answer prompt and different parser; upstream uses sampling, thinking
enabled and its own prompt/parser. `stage_b_harness.py:199-203` also passes
`indices=None`, compacting chat-template tokens rather than preserving them as
the paper does. Matching local token caps makes the local comparison useful,
but does not make it a published-result reproduction.

### Implementation findings

1. **Diagnostic recipe differs from the frozen protocol.** Saved
   `compiled_k1024_art0_fullq/manifest.json` and the K128 manifest show 400 steps,
   LR **0.003**, `oproj_dir=null`, no minibatching. Capture metadata shows **8**
   conversations / 458 query rows. Protocol specifies LR **0.001**, projected
   loss, 24 examples/update and **71** conversations. These runs must be labelled
   diagnostic, not a benchmark of the frozen recipe.
2. **Projected cosine loss is incorrectly normalized.**
   `scripts/compile_torch_v2.py:347-354` sums valid row cosines instead of averaging
   within each trajectory. CPU reproduction with identical teacher/student
   produces loss 0 for one query row and **-3 for four identical rows**.
   This changes weighting with sequence length. It did **not** affect the saved
   diagnostic runs, which have no output projection. No fix applied in review.
3. **AM effective K was misreported.** `stage_b_harness.py:206` reports only
   layer 0's padded length and discards returned effective-budget statistics.
   Reconstruction using the released 288-head budget, ratio cap 0.75, and
   prefix length 6543 gives ~129.4 effective slots/head at 2%, and **1019.5** at
   15.6% (layer 0 padded length **1142**). Thus AM@15.6% and ours K1024 are
   approximately budget matched, both ~6.4x in effective KV entries.
   Reconstructed padded K/V storage is ~447.1 MiB for AM versus 144 MiB for
   uniform K1024; AM bias adds ~1.75 MiB. These are budget-derived tensor sizes,
   not measured GPU allocations or a saved-cache inspection.
4. **Evaluation evidence is incomplete.** Stage B silently skips generation
   exceptions (`:222-225`); Stage B/C JSON omit answers, token cap and seeds.
   Counts for reviewed runs match 14/19/18 questions, so no missing questions
   were found in these files. Broad letter fallback makes parse=1.00 weaker than
   proof of an explicit final answer. Raw answers cannot be re-scored from them.
5. **Passage locators are not fully grounded.** `gen_qwen3_ctx.py:90-94` inserts
   `[Passage k of N]` in questions, but the shared article contains no passage
   labels or boundaries. This makes questions distinct; it does not prove the
   model can identify the chunk that generated the answer.
6. **The capacity conclusion was too strong.** Failure of real tail-128 plus
   low training error proves neither a fundamental K128 limit nor generalization.
   AM's 8/14 with ~129 effective slots is direct counterevidence to a blanket
   capacity claim. Query coverage, drift, allocation, mass preservation and
   optimization remain plausible explanations.
7. **Control evidence is narrower than the prose.** Saved
   `teacher_install_control.json` has byte-identical reference/full-install text,
   but both parsed answers are null and its `plumbing_matches` verdict is false.
   Text equality supports that tested uniform full-cache path, not every
   nonuniform cache/mask path. Current upstream Qwen code takes the mask's LAST
   `kv_length` columns, so the earlier first-column mask concern is not proven.
8. **Speed is not an end-to-end comparison.** Ours' ~8 minutes includes capture
   and compile but omits self-study answer generation; AM's ~17 minutes includes
   query generation. Batched HF-shim equivalence is not equivalence to vLLM's
   sampled outputs, and its full-prep speedup remains unmeasured.

CPU check artifact: `/tmp/opencode/kv_review_check.py` (local), copied unchanged
to XTX `/tmp/kv_review_check.py`; run with the bench Python, CPU only. Other
audit copies: `/tmp/opencode/kv-review-{results,compaction,cartridges,logs}/`.

### What about CARTRIDGES?

No local CARTRIDGES training/evaluation has been completed. Its code freezes
model weights but backpropagates through the model to train the entire prefix
cache against teacher token probabilities (`cartridges/train.py:209-214,383-401`).
That directly trains the deployed computation, unlike independent-layer
teacher-input attention matching, and is a credible accuracy-oriented route.

The pinned AM repository's plotting data report CARTRIDGES QuALITY accuracy
59.94% at 1%/2%, 61.90% at 5%, 61.62% at 10% (first 20 articles, full 75.0%).
At 2%, its training-time points rise from 50.1% at 0.436 hours to 59.94% at
4.84 hours. Sources: `scripts/plot_metric_vs_target_size.py:338-343` and
`scripts/plot_metric_vs_compaction_time.py:313-322`. Paper Appendix B.3 specifies
32,768 synthetic samples (~25-30M tokens), one epoch, LR 0.02 per article.
These H100-era published costs are not estimates for the XTX.

The original CARTRIDGES LongHealth/MTOB gains use different tasks/checkpoint
settings and cannot be substituted for QuALITY scores. The AM paper also reports
CARTRIDGES outperforming AM at more extreme compression on some LongHealth
settings; this is not evidence it will outperform AM here.

**Recommended next experiment:** correct benchmark accounting/metadata first;
then compare the unchanged frozen compiler with AM-HighestAttnKeys and the
stronger, not-yet-tested AM-OMP-fast at 2% and ~16% on the same first three
articles. Keep a separate paper-compatible evaluation track. If short-prefix
quality remains poor, run a bounded CARTRIDGES-style end-to-end distillation
pilot; label it budget-limited, not a reproduction. Do not declare our compiler
better, dismiss AM, or launch the full CARTRIDGES recipe from these diagnostics.

## TL;DR (REVISED — supersedes the earlier "our method fails" conclusion)

- **AM baseline comparison: DONE and clean.**
- **Our compiler on QuALITY: WORKS once three defects are fixed.** At K=1024
  (6.4x compression) on article 0, matched protocol (greedy, max_new_tokens=512),
  it scores **10/14 = 0.714** vs AM-HighestAttnKeys at ~6x = **0.643**.
- The earlier "does NOT work as a drop-in prefix" note (and the whole
  EXTERNAL_BENCH_STATUS conclusion that followed) was **an artifact of three
  fixable bugs**, not a property of the method. See "Corrections" below.
- Remaining honest gaps: (a) at 51x our method (0.143) is far behind AM (0.571);
  (b) the ~6x lead is n=14, ONE article — not yet a result; (c) an earlier AM@6x
  figure of 0.429 was a max_new_tokens mismatch, not a real drop.

## Corrections to the earlier negative result

The previous version of this file reported our cache as unusable as a long-context
prefix. Three independent defects were found and fixed; each is verified.

### (1) Compiler used the wrong attention scale  [FIXED]

`scripts/compile_torch_v2.py` hardcoded `scale = 1/16` in the training loss. That
is only correct for `head_dim = 256`; **Qwen3-4B has `head_dim = 128`, so the
deployed scale is `1/sqrt(128) = 0.08839`.**

CPU replay of saved layer-35 training trajectories, MSE of compiled-vs-teacher:

| Layer | at training scale (1/16) | at model scale (1/sqrt(128)) |
|---|---:|---:|
| 18 | 0.000589 | 0.002976 |
| 35 | 0.002412 | **0.043715** |

Training under the wrong scale optimises a different attention distribution than
deployment. Fixed: `default_scale(head_dim)` derives `head_dim**-0.5`; the compiler
accepts `--scale` to reproduce legacy runs, and the manifest records
`attention_scale` + `head_dim`. (`default_scale(256) == 1/16` exactly, so old
256-dim paths are unchanged.)

### (2) Self-study questions lost their passage reference  [FIXED]

`scripts/gen_qwen3_ctx.py` generated each answer from *one chunk* but stored the
*full article + only the bare template question*. With 8 items there were only
**5 distinct questions**, and duplicate questions had **byte-identical first
prediction queries with different answers** — contradictory supervision.

Fixed: each question now carries a stable locator (`[Passage k of N] ...`), giving
**8 distinct, grounded questions**. The capture also records `n_sys` (was `null`)
and a `context_sha256`, and asserts a single shared context.

### (3) Training queries never covered the question-prefill region  [FIXED]

`scripts/capture_qwen3_traj.py` trained on only the **last user token + 10 answer
tokens per item — 88 query rows total**, spanning logical positions `6564..6584`.
The deployed MCQ prompt's *earlier question tokens* (which drive the live K/V of
later layers) were **never in the loss**.

Fixed: `scripts/capture_qwen3_fullquery.py` records **every question-turn row plus
sampled answer rows — 458 query rows**, spanning `6543..6676`, i.e. the region the
installed cache actually meets.

## Plumbing control (verified OK)

`scripts/teacher_install_control.py` installs the **real full teacher K/V** through
the exact `CompactedPrefixCache` + `generate_with_compacted_cache_batch` path used
by Stage C, and compares to a plain full-context forward.

- Full teacher install output was **byte-identical (390 chars)** to the
  full-context reference. **The install path is correct.**
- Truncating that real cache to the tail 128 slots reproduced the same degenerate
  loop, confirming K=128 on a 6543-token article is genuinely capacity-bound.

## Our method on QuALITY article 0 — MATCHED protocol

All runs below use greedy decoding, the same harness, and **max_new_tokens=512**.
(Matching the token budget matters: an earlier AM run at max_new_tokens=128
produced 4/14 EMPTY completions, scoring 0.429 instead of 0.643. Any comparison
must hold max_new_tokens fixed.)

| Cache | K | Compression | Score | Parse |
|---|---:|---:|---:|---:|
| Full context | — | 1x | 11/14 = 0.786 | 1.00 |
| AM HighestAttnKeys @2% | ~129 | ~51x | 8/14 = 0.571 | 1.00 |
| AM HighestAttnKeys @15.6% | ~1142 | 5.7x | 9/14 = 0.643 | 1.00 |
| **Ours, full-query cache** | **1024** | **6.4x** | **10/14 = 0.714** | 1.00 |
| Ours, legacy (3 bugs) | 128 | 51x | 0/14 = 0.000 | 0.00 |
| Ours, full-query cache | 128 | 51x | 2/14 = 0.143 | 0.93 |

Honest reading:
- **At ~50x:** AM wins decisively (0.571 vs 0.143). Our method is capacity-bound
  at K=128 for a 6543-token article.
- **At ~6x:** ours 0.714 vs AM 0.643 on this article. We are ahead, but n=14 and
  one article — this is a hypothesis, not a result. It needs replication on
  articles 1–2 and a ratio sweep before any claim.
- Both methods are far below full context (0.786) at these budgets.

## Build speed (article 0, this box)

| Stage | Ours | AM |
|---|---:|---:|
| Query/data prep | capture 182 s | self-study query gen ~1005 s |
| Build/optimize | compile 313 s (K=1024) | included above |
| **Total** | **~8 min** | **~17 min** |

AM's prep dominates because our vLLM shim (`rocm_vllm_shim.py`) generated one
prompt per Python iteration. A batched-shim rewrite is committed and verified
equiv-batched-vs-single on greedy prompts (`/tmp/shim_equiv_test.py`), which
should cut AM's prep substantially — that speedup is **not yet reflected above**.

## Completed, real result: AM vs full context (QuALITY, Qwen3-4B)

Same harness, same articles/questions, greedy, max_new_tokens 512.

| Article | Questions | Full context | AM-HighestAttnKeys @ 2% | K (tokens) |
|---|---:|---:|---:|---:|
| 0 | 14 | 0.786 | 0.571 | 129 |
| 1 | 19 | 0.842 | 0.684 | 117 |
| 2 | 18 | 0.667 | 0.667 | 134 |
| **Total** | **51** | **0.765** | **0.647** | ~127 |

- Full-context 0.765 vs published 71.1% (50 articles) — protocol validated.
- AM @ 2% drops 11.8 points here vs the paper's ~6-point drop; n=51, 3 articles.
- AM method: `highest_attn_keys_rms_nnls2_-3_3_lsq_on-policy`, `ss-plus-repeat`,
  released head budget, `--max-ratio-per-head 0.75`.
- Prep time ~950 s/article (self-study query generation on the HF path).

## Why the pipeline looks correct end-to-end

1. **Capture** (`capture_qwen3_traj.py` / `capture_qwen3_fullquery.py`): 36 layer
   shards, schema validated, shapes Hq=32, Hkv=8, D=128. Full-query capture is
   182 s for 8 items / 6543-token context.
2. **Compile** (`compile_torch_v2.py`): all 36 layers, loss falls strongly
   (e.g. L35 0.0472 → 0.0015 at the corrected scale).
3. **Install**: verified correct — see "Plumbing control" above. The earlier
   "install FAILS" observation was the compiled cache carrying no usable
   content, not the install path.

## Capacity diagnostic (why K=128 alone was never going to work)

`/tmp/capacity_diag.py` measures, on the saved training queries, the compiled
cache's attention output vs the full teacher prefix:

| Layer | Compiled relRMSE | Teacher-tail-128 relRMSE |
|---|---:|---:|
| 12 | 0.084 | 1.042 |
| 24 | 0.107 | 1.500 |
| 35 | **0.017** | 1.415 |

The compiled cache **beats** a real 128-slot teacher tail at every layer *on the
training queries* — so the optimiser is working. The failure at K=128 was
capacity + query coverage; at K=1024 the same objective becomes competitive.

## Honest time accounting

Most of the session went to: LAN archival + verification, reclaiming disk,
building a Python 3.12 ROCm env from scratch, ROCm compatibility shims, then
forensic debugging of the compiled cache. The earlier "negative" was reported
after one capture+compile cycle that contained all three defects above.

## What is ready to reuse

- Working env: `/home/arpin/kvbench/env` (torch 2.8.0+rocm6.4, transformers 4.57.1).
- `stage_a_harness.py`, `stage_b_harness.py` (full/AM paths), `rocm_vllm_shim.py`.
- `capture_qwen3_traj.py`, `capture_qwen3_fullquery.py` (full-query policy),
  `stage_c_our_harness.py`, `teacher_install_control.py`.
- AM results: `results/{original_art1,original_art2,am2pct_art1,am2pct_art2}.json`,
  `am_highest_2pct_art0.json`.
- Our results: `results/ours_k128_art0_fullq.json`, `ours_k1024_art0_fullq.json`.

## Recommended next steps

1. **Replicate K=1024 (and a K sweep) on articles 1–2** to turn the n=1 result
   into a real comparison vs AM.
2. **Push K=128 down** if the small-budget regime matters — likely needs the
   paired/"dirty-input" objective so training sees the deployed query
   distribution, now that query *coverage* is fixed.
3. **Re-run the K=1024 comparison against AM at a matched budget** (AM at ~6.4x,
   not 50x) for an apples-to-apples claim.
